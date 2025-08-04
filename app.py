from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from database import db, bcrypt, User, Event, Photo, FaceEncoding
from face_utils import get_face_encodings, compare_faces
import qrcode
from io import BytesIO
import base64
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eventphotoai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

db.init_app(app)
bcrypt.init_app(app)

with app.app_context():
    db.create_all()

# --- Auth Routes ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('auth/login.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    if User.query.filter_by(email=email).first():
        flash('An account with this email already exists.', 'warning')
        return redirect(url_for('login'))
    new_user = User(email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    flash('Account created successfully! Please log in.', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))

# --- Admin Routes ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    stats = {
        'active_events': Event.query.filter_by(user_id=user.id).count(),
        'total_photos': db.session.query(func.count(Photo.id)).join(Event).filter(Event.user_id == user.id).scalar() or 0,
        'guests_served': 0
    }
    recent_events = Event.query.filter_by(user_id=user.id).order_by(Event.id.desc()).limit(3).all()
    return render_template('admin/dashboard.html', user=user, stats=stats, recent_events=recent_events)

@app.route('/events')
def my_events():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    all_events = Event.query.filter_by(user_id=user.id).order_by(Event.id.desc()).all()
    return render_template('admin/my_events.html', events=all_events)

@app.route('/events/new', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        new_event = Event(name=request.form['event_name'], date=request.form['event_date'], location=request.form['location'], description=request.form['description'], user_id=session['user_id'])
        db.session.add(new_event)
        db.session.commit()
        
        files = request.files.getlist('photos')
        photos_processed = 0
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                event_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], str(new_event.id))
                os.makedirs(event_upload_path, exist_ok=True)
                filepath = os.path.join(event_upload_path, filename)
                file.save(filepath)
                encodings = get_face_encodings(filepath)
                if encodings:
                    photos_processed += 1
                    new_photo = Photo(filename=filename, event_id=new_event.id)
                    db.session.add(new_photo)
                    db.session.flush()
                    for enc in encodings:
                        db.session.add(FaceEncoding(encoding=enc, photo_id=new_photo.id))
        db.session.commit()
        flash(f'Event "{new_event.name}" created and {photos_processed} photos processed!', 'success')
        return redirect(url_for('manage_event', event_id=new_event.id))
    return render_template('admin/create_event.html')

@app.route('/events/<int:event_id>', methods=['GET', 'POST'])
def manage_event(event_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    event = Event.query.get_or_404(event_id)
    if event.user_id != session['user_id']:
        flash("You do not have permission to view this event.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        files = request.files.getlist('photos')
        photos_processed = 0
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                event_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], str(event.id))
                os.makedirs(event_upload_path, exist_ok=True)
                filepath = os.path.join(event_upload_path, filename)
                file.save(filepath)
                encodings = get_face_encodings(filepath)
                if encodings:
                    photos_processed += 1
                    new_photo = Photo(filename=filename, event_id=event.id)
                    db.session.add(new_photo)
                    db.session.flush()
                    for enc in encodings:
                        db.session.add(FaceEncoding(encoding=enc, photo_id=new_photo.id))
        db.session.commit()
        flash(f'Added {photos_processed} new photos to "{event.name}"!', 'success')
        return redirect(url_for('manage_event', event_id=event.id))

    event_url = url_for('client_scan', event_id=event.id, _external=True)
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(event_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    qr_code_data_uri = f"data:image/png;base64,{qr_code_base64}"
    return render_template('admin/event_manage.html', event=event, qr_code_data_uri=qr_code_data_uri, event_url=event_url)

# --- Client Routes & API ---
@app.route('/scan/<int:event_id>')
def client_scan(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('client/scan.html', event=event)

@app.route('/uploads/<int:event_id>/<filename>')
def uploaded_file(event_id, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], str(event_id)), filename)

@app.route('/api/find_my_photos/<int:event_id>', methods=['POST'])
def find_my_photos(event_id):
    data = request.get_json()
    if not data or 'image' not in data: return jsonify({'error': 'No image data provided'}), 400
    
    image_data_url = data['image']
    image_data = base64.b64decode(image_data_url.split(',')[1])
    temp_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_client_face.jpg')
    with open(temp_image_path, 'wb') as f: f.write(image_data)
    
    client_encodings = get_face_encodings(temp_image_path)
    if os.path.exists(temp_image_path): os.remove(temp_image_path)
    
    if not client_encodings:
        return jsonify({'error': 'Could not detect a face in your selfie. Please try again.'}), 400
    
    client_encoding = client_encodings[0]
    matching_photo_urls = set()
    for photo in Photo.query.filter_by(event_id=event_id).all():
        known_encodings = [fe.encoding for fe in photo.face_encodings]
        if compare_faces(known_encodings, client_encoding):
            matching_photo_urls.add(url_for('uploaded_file', event_id=photo.event_id, filename=photo.filename))
            
    if not matching_photo_urls: return jsonify({'message': 'No matching photos found for you in this event.'})
    
    gallery_html = render_template('client/gallery_partial.html', photo_urls=list(matching_photo_urls))
    return jsonify({'gallery_html': gallery_html})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
