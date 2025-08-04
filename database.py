from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    events = db.relationship('Event', backref='organizer', lazy=True, cascade="all, delete-orphan")

    def __init__(self, email, password):
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50))
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    photos = db.relationship('Photo', backref='event', lazy=True, cascade="all, delete-orphan")

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    face_encodings = db.relationship('FaceEncoding', backref='photo', lazy=True, cascade="all, delete-orphan")

class FaceEncoding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    encoding = db.Column(db.PickleType, nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)