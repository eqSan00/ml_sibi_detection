from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import cv2 as cv
import mediapipe as mp
import numpy as np
import tensorflow as tf
from tensorflow import keras
import base64
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey' # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Buat direktori untuk menyimpan gambar sementara
temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)

# Muat model 
model_path = "model.h5"
# Handling model loading error silently or safely if model doesn't exist yet
if os.path.exists(model_path):
    model = keras.models.load_model(model_path)
else:
    print(f"Warning: Model file {model_path} not found.")
    model = None

# Fungsi untuk mengekstrak fitur dari suatu gambar
def extract_feature(input_image_path):
    mp_hands = mp.solutions.hands   # type: ignore
    mp_drawing = mp.solutions.drawing_utils  # type: ignore
    image = cv.imread(input_image_path)
    with mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.1) as hands:
        results = hands.process(cv.flip(cv.cvtColor(image, cv.COLOR_BGR2RGB), 1))
        image_height, image_width, _ = image.shape

        if not results.multi_hand_landmarks:
            landmarks = [0] * 63
            return np.array([landmarks]).reshape((1, 63, 1)), image, "Tidak ada pose tangan yang terdeteksi dalam gambar."

        annotated_image = cv.flip(image.copy(), 1)
        landmarks = []
        for hand_landmarks in results.multi_hand_landmarks:
            for point in mp_hands.HandLandmark:
                x = hand_landmarks.landmark[point].x * image_width
                y = hand_landmarks.landmark[point].y * image_height
                z = hand_landmarks.landmark[point].z
                landmarks.extend([x, y, z])
            mp_drawing.draw_landmarks(annotated_image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        input_IMG = np.array([landmarks]).reshape((1, 63, 1))

        return input_IMG, annotated_image, "Fitur dari gambar berhasil diekstrak."

# Fungsi untuk memprediksi kelas dari fitur yang diekstraksi
def predict_class(features, model):
    if model is None:
        return "Model Error"
    prediction = model.predict(features)
    class_index = np.argmax(prediction)
    classes = {
        0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E',
        5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J',
        10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O',
        15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T',
        20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z'
    }
    return classes.get(class_index, "Tidak diketahui") # type: ignore

# Jalur memproses gambar yang diunggah dan mengembalikan hasil prediksi
@app.route('/process_image', methods=['POST'])
def process_image():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    image_data = data['image_data']

    # Simpan gambar ke file sementara
    image_path = os.path.join(temp_dir, "captured_image.jpg")
    with open(image_path, "wb") as fh:
        fh.write(base64.b64decode(image_data.split(',')[1]))

    # Ekstrak fitur dari gambar yang diunggah
    features, annotated_image, message = extract_feature(image_path)

    # Prediksi kelas gambar
    if message != "Fitur dari gambar berhasil diekstrak.":
        predicted_class = "Tidak diketahui"
    else:
        predicted_class = predict_class(features, model)

    # Ubah gambar beranotasi menjadi string yang disandikan base64
    _, buffer = cv.imencode('.jpg', annotated_image)
    annotated_image_data = base64.b64encode(buffer.tobytes()).decode('utf-8')
    
    return jsonify({
        'predicted_class': predicted_class,
        'annotated_image': annotated_image_data,
        'message': message
    })

# Auth Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        login_user(user, remember=remember)
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email address already exists')
            return redirect(url_for('register'))

        new_user = User(email=email, name=name, password=generate_password_hash(password, method='scrypt'))

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Pages
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detection')
@login_required
def detection():
    return render_template('detection.html')

@app.route('/about')
def about():
    return render_template('about.html') 

@app.route('/alphabet')
def alphabet():
    return render_template('alphabet.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
