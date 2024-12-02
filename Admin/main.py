from flask import Flask, render_template, request, jsonify
from datetime import datetime
import sqlite3
import cv2
from pyzbar.pyzbar import decode
import base64
import numpy as np

app = Flask(__name__)

# Database initialization
def init_db():
    conn = sqlite3.connect('qr_logs.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  person_id TEXT,
                  phone TEXT,
                  scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_qr():
    try:
        # Get image data from request
        image_data = request.json['image']
        # Convert base64 to image
        encoded_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Decode QR code
        decoded_objects = decode(img)
        
        if not decoded_objects:
            return jsonify({'success': False, 'error': 'No QR code found'})
        
        # Parse QR data (assuming comma-separated format: name,id,phone)
        qr_data = decoded_objects[0].data.decode('utf-8')
        name, person_id, phone = qr_data.split(',')
        
        # Save to database
        conn = sqlite3.connect('qr_logs.db')
        c = conn.cursor()
        c.execute('''INSERT INTO scans (name, person_id, phone)
                     VALUES (?, ?, ?)''', (name, person_id, phone))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'name': name,
                'id': person_id,
                'phone': phone
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logs')
def view_logs():
    conn = sqlite3.connect('qr_logs.db')
    c = conn.cursor()
    c.execute('SELECT * FROM scans ORDER BY scan_time DESC')
    logs = c.fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

if __name__ == '__main__':
    app.run(port=8000,debug=True)