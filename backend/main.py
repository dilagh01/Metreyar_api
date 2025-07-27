from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
from pathlib import Path
import shutil
import pytesseract
from PIL import Image
from fpdf import FPDF
from openpyxl import Workbook
import os
import uuid
from io import BytesIO
import base64

app = FastAPI()

# فعال‌سازی CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dilagh01.github.io", "https://dilagh01.github.io/metreyar_flutter_web"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# مسیر OCR فایل (multipart)
@app.post("/ocr/")
async def perform_ocr(files: List[UploadFile] = File(...)):
    # ... (کد مربوط به OCR فایل‌ها)
    pass

# 🔹 مسیر OCR از base64 (مخصوص Flutter Web)
@app.post("/ocr/base64")
async def ocr_from_base64(request: Request):
    data = await request.json()
    image_data = data.get("image")

    if not image_data:
        return {"error": "No image data provided"}

    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="fas+eng")
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}

# مسیرهای دانلود (PDF, TXT, Excel)
@app.get("/download/pdf")
def download_pdf():
    # ...
    pass
