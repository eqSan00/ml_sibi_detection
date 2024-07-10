from flask import Flask, render_template, request, jsonify
import cv2 as cv
import mediapipe as mp
import numpy as np
import tensorflow as tf
import keras
from tensorflow import keras   # type: ignore
import base64   
import os


app = Flask(__name__)

# Buat direktori untuk menyimpan gambar sementara
temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)

# Muat model 
model_path = "model.h5"
model = keras.models.load_model(model_path)

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

# Rute untuk menyajikan file HTML Anda
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detection')
def detection():
    return render_template('detection.html')

@app.route('/about')
def about():
    return render_template('about.html') 

@app.route('/alphabet')
def alphabet():
    return render_template('alphabet.html')

if __name__ == '__main__':
    app.run(debug=True)

