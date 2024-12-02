import os
from flask import Flask, render_template, request, redirect, url_for
from pyzbar.pyzbar import decode
import sqlite3
from datetime import datetime
import cv2
from uuid import uuid4

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Create the database and table (run only once)
def create_db():
    conn = sqlite3.connect('qr_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS qr_scans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        phone TEXT,
                        unique_id TEXT,
                        scan_date TEXT)''')
    conn.commit()
    conn.close()

# Save QR data to the database
def save_qr_data(name, phone, unique_id):
    conn = sqlite3.connect('qr_data.db')
    cursor = conn.cursor()
    scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''INSERT INTO qr_scans (name, phone, unique_id, scan_date)
                      VALUES (?, ?, ?, ?)''', (name, phone, unique_id, scan_date))
    conn.commit()
    conn.close()

# Read and decode QR code from image
def read_qr_code(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return "Failed to load image. Please upload a valid image."

    decoded_objects = decode(image)
    data = []
    
    for obj in decoded_objects:
        qr_data = obj.data.decode('utf-8')
        print(f"QR Data: {qr_data}")  # Debugging: print the QR data
        data_parts = qr_data.split('\n')
        
        if len(data_parts) < 3:
            return "QR data format is incorrect. Expected at least 3 parts."
        
        try:
            name = data_parts[0].split(": ")[1]
            phone = data_parts[1].split(": ")[1]
            unique_id = data_parts[2].split(": ")[1]
        except IndexError:
            return "Error: QR data format is not correct, missing expected parts."
        
        save_qr_data(name, phone, unique_id)
        data.append((name, phone, unique_id))

    return data

# Route for home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for handling QR upload and processing
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith(('png', 'jpg', 'jpeg')):
        return "Invalid file format. Please upload a valid image."
    
    unique_filename = f"{uuid4().hex}_{file.filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)

    qr_data = read_qr_code(file_path)
    
    if qr_data:
        return render_template('qr_result.html', data=qr_data, current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    else:
        return render_template('error.html', message="No QR code found.")

# Route for displaying all saved QR data
@app.route('/scans')
def scans():
    conn = sqlite3.connect('qr_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM qr_scans')
    all_scans = cursor.fetchall()
    conn.close()
    return render_template('scans.html', scans=all_scans)

if __name__ == '__main__':
    create_db()  # Create the database (only needs to run once)
    app.run(port=8000,debug=True)
