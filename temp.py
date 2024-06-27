from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os
from werkzeug.utils import secure_filename
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'webdev',
    'database': 'pneumonia_detection'
}

# Load the model
model = tf.keras.models.load_model('vgg_unfrozen.h5')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user'] = email
            return redirect(url_for('main'))
        else:
            error = 'Invalid email or password'
            return render_template('login.html', error=error)
    
    return render_template('login.html')

@app.route('/main', methods=['GET', 'POST'])
def main():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    return render_template('main.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'user' not in session:
        return redirect(url_for('login'))

    if 'file' not in request.files:
        return render_template('main.html', result='No file part')
    
    file = request.files['file']
    if file.filename == '':
        return render_template('main.html', result='No selected file')
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        # Predict pneumonia
        img = image.load_img(filepath, target_size=(128,128))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0
        
        prediction = model.predict(img_array)
        result = 'Pneumonia Detected' if prediction[0][0] > 0.5 else 'No Pneumonia'
        
        return render_template('main.html', result=result)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
