from fastapi import FastAPI, HTTPException, Response, Form
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import qrcode
import string
import random
from io import BytesIO
import base64
from typing import Optional
import uvicorn
import os
from datetime import datetime

app = FastAPI()

class ContactInfo(BaseModel):
    phone: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    name: str = Field(..., min_length=1, max_length=50)

def generate_id(length=8):
    chars = string.ascii_uppercase + string.digits
    while True:
        id = ''.join(random.choices(chars, k=length))
        if any(c.isdigit() for c in id) and any(c.isalpha() for c in id):
            return id

def save_qr(phone: str, name: str, id: str) -> str:
    content = f"ID: {id}\nName: {name}\nPhone: {phone}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(content)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    os.makedirs('qr_codes', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"qr_codes/qr_{id}_{timestamp}.png"
    img.save(filename)
    return filename

@app.get("/", response_class=HTMLResponse)
async def home():
    with open('templates/index.html', 'r') as f:
        return f.read()

@app.post("/generate-qr-download")
async def generate_qr_download(name: str = Form(...), phone: str = Form(...)):
    try:
        # Validate input
        contact = ContactInfo(name=name, phone=phone)
        id = generate_id()
        filename = save_qr(contact.phone, contact.name, id)
        return FileResponse(
            path=filename,
            filename=f"QR_{contact.name}_{id}.png",
            media_type="image/png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)