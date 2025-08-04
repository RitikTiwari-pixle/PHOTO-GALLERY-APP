import cv2
import numpy as np
import os

# This is the core AI engine of your application. It uses the OpenCV library
# to perform face detection and recognition.

# --- Model Loading ---
# We load two pre-trained models when the application starts.
# It's crucial that the two model files are in the same root folder as your app.py.
try:
    # 1. Face Detector: A Haar Cascade model to find the location (the box) of faces in an image.
    face_detector_path = os.environ.get('FACE_DETECTOR_PATH', 'haarcascade_frontalface_default.xml')
    face_embedder_path = os.environ.get('FACE_EMBEDDER_PATH', 'openface.nn4.small2.v1.t7')
    face_detector = cv2.CascadeClassifier(face_detector_path)
    
    # 2. Face Embedder: A deep learning model (from OpenFace) to generate a unique
    #    128-point mathematical representation (an "encoding" or "embedding") of a face.
    face_embedder = cv2.dnn.readNetFromTorch(face_embedder_path)
except cv2.error as e:
    # This error block will run if the model files are missing, preventing the app from crashing.
    print("="*60)
    print("FATAL ERROR: Could not load AI model files.")
    print("Please ensure 'haarcascade_frontalface_default.xml' and 'openface.nn4.small2.v1.t7' are in the project's root directory.")
    print("="*60)
    face_detector = None
    face_embedder = None

def get_face_encodings(image_path):
    """
    Extracts 128-point face encodings from an image file using OpenCV and OpenFace.
    Returns a list of encodings (np.ndarray), one for each detected face.
    """
    if not face_detector or not face_embedder:
        print("Face models not loaded. Cannot process image.")
        return []

    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Warning: Could not read image file at {image_path}. It might be corrupted or an unsupported format.")
            return []
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    except Exception as e:
        print(f"Error during image processing for {image_path}: {e}")
        return []

    encodings = []
    if faces is None or len(faces) == 0:
        return encodings

    for (x, y, w, h) in faces:
        face_roi = img[y:y+h, x:x+w]
        try:
            face_blob = cv2.dnn.blobFromImage(face_roi, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False)
            face_embedder.setInput(face_blob)
            vec = face_embedder.forward()
            encodings.append(vec.flatten())
        except Exception as e:
            print(f"Error encoding face at ({x},{y},{w},{h}): {e}")
            continue
    return encodings

def compare_faces(known_encodings, face_to_check_encoding, tolerance=0.8):
    """
    Compares a single new face encoding against a list of known encodings.
    Returns True if any match is found within the tolerance, else False.
    """
    for known_encoding in known_encodings:
        try:
            dist = np.linalg.norm(known_encoding - face_to_check_encoding)
            if dist < tolerance:
                return True
        except Exception as e:
            print(f"Error comparing encodings: {e}")
            continue
    return False
