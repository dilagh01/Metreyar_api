from fastapi import FastAPI, File, UploadFile
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

app = FastAPI()

# فعال‌سازی CORS برای GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dilagh01.github.io/Metreyar_flutter_web/"],  # یا ["*"] برای تست باز
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploaded_images"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to Metreyar OCR API"}

@app.post("/ocr/")
async def perform_ocr(files: List[UploadFile] = File(...)):
    extracted_texts = []
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    wb = Workbook()
    ws = wb.active
    ws.title = "OCR Results"
    ws.append(["Filename", "Extracted Text"])  # Excel header
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

        # انجام OCR با زبان فارسی و انگلیسی
        text = pytesseract.image_to_string(img, lang="fas+eng")
        extracted_texts.append(text)

        # افزودن به PDF
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in text.splitlines():
            pdf.multi_cell(0, 10, line)

        # افزودن به Excel
        ws.append([filename, text])

    # ذخیره PDF
    pdf_path = Path(RESULT_FOLDER) / "ocr_result.pdf"
    pdf.output(str(pdf_path))

    # ذخیره TXT
    txt_path = Path(RESULT_FOLDER) / "ocr_result.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for text in extracted_texts:
            f.write(text + "\n\n")

    # ذخیره Excel
    excel_path = Path(RESULT_FOLDER) / "ocr_result.xlsx"
    wb.save(str(excel_path))

    return {
        "message": "OCR completed",
        "uploaded_files": saved_filenames,
        "pdf_result": str(pdf_path),
        "txt_result": str(txt_path),
        "excel_result": str(excel_path),
        "text": extracted_texts
    }

@app.get("/download/pdf")
def download_pdf():
    path = Path(RESULT_FOLDER) / "ocr_result.pdf"
    if path.exists():
        return FileResponse(path, media_type="application/pdf", filename="ocr_result.pdf")
    return {"error": "PDF not found"}

@app.get("/download/txt")
def download_txt():
    path = Path(RESULT_FOLDER) / "ocr_result.txt"
    if path.exists():
        return FileResponse(path, media_type="text/plain", filename="ocr_result.txt")
    return {"error": "Text file not found"}

@app.get("/download/excel")
def download_excel():
    path = Path(RESULT_FOLDER) / "ocr_result.xlsx"
    if path.exists():
        return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="ocr_result.xlsx")
    return {"error": "Excel file not found"}
