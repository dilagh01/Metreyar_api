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

# 🛡️ فعال‌سازی CORS برای دسترسی از GitHub Pages یا سایر فرانت‌ها
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dilagh01.github.io",
        "https://dilagh01.github.io/metreyar_flutter_web"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 پوشه‌های ذخیره‌سازی
UPLOAD_FOLDER = "uploaded_images"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)


@app.get("/")
def read_root():
    return {"message": "✅ Welcome to Metreyar OCR API"}


# 🔹 مسیر OCR از آپلود فایل‌های تصویری (multipart)
@app.post("/ocr/base64")
async def ocr_from_base64(request: Request):
    ...
    extracted_texts = []
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    wb = Workbook()
    ws = wb.active
    ws.title = "OCR Results"
    ws.append(["Filename", "Extracted Text"])
    saved_filenames = []

    for file in files:
        unique_id = str(uuid.uuid4())
        extension = Path(file.filename).suffix
        filename = f"{unique_id}{extension}"
        filepath = Path(UPLOAD_FOLDER) / filename

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved_filenames.append(str(filepath))
        img = Image.open(filepath)

        # 🔍 انجام OCR
        text = pytesseract.image_to_string(img, lang="fas+eng")
        extracted_texts.append(text)

        # 📝 افزودن به PDF
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in text.splitlines():
            pdf.multi_cell(0, 10, line)

        # 📊 افزودن به Excel
        ws.append([filename, text])

    # 💾 ذخیره نتایج
    pdf_path = Path(RESULT_FOLDER) / "ocr_result.pdf"
    pdf.output(str(pdf_path))

    txt_path = Path(RESULT_FOLDER) / "ocr_result.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for text in extracted_texts:
            f.write(text + "\n\n")

    excel_path = Path(RESULT_FOLDER) / "ocr_result.xlsx"
    wb.save(str(excel_path))

    return {
        "message": "✅ OCR completed",
        "uploaded_files": saved_filenames,
        "text": extracted_texts
    }


# 🔸 مسیر OCR از تصویر Base64 (برای Flutter Web)
@app.post("/ocr/base64")
async def ocr_from_base64(request: Request):
    data = await request.json()
    image_data = data.get("image")

    if not image_data:
        return {"error": "❌ No image data provided"}

    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="fas+eng")
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}


# 📥 مسیر دانلود PDF
@app.get("/download/pdf")
def download_pdf():
    path = Path(RESULT_FOLDER) / "ocr_result.pdf"
    if path.exists():
        return FileResponse(path, media_type="application/pdf", filename="ocr_result.pdf")
    return {"error": "PDF not found"}


# 📥 مسیر دانلود فایل متنی
@app.get("/download/txt")
def download_txt():
    path = Path(RESULT_FOLDER) / "ocr_result.txt"
    if path.exists():
        return FileResponse(path, media_type="text/plain", filename="ocr_result.txt")
    return {"error": "Text file not found"}


# 📥 مسیر دانلود فایل Excel
@app.get("/download/excel")
def download_excel():
    path = Path(RESULT_FOLDER) / "ocr_result.xlsx"
    if path.exists():
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="ocr_result.xlsx"
        )
    return {"error": "Excel file not found"}
