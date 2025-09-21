# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

app = FastAPI()

# فعال کردن CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://github.com/dilagh01/metreyar_flutter_web"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# دیتای اولیه (جنریک)
DATA = [
    {"نام": "علی", "سن": 30, "شهر": "تهران"},
    {"نام": "زهرا", "سن": 25, "شهر": "شیراز"},
]

@app.get("/data/")
async def get_data():
    """برگرداندن داده‌ها به فرانت"""
    return DATA

@app.post("/data/")
async def update_data(new_data: list[dict]):
    """دریافت داده‌های ویرایش‌شده و ذخیره"""
    global DATA
    DATA = new_data
    return {"message": "✅ داده‌ها ذخیره شدند", "data": DATA}

@app.get("/generate-report/")
async def generate_report():
    """ساخت گزارش PDF از داده‌ها"""
    df = pd.DataFrame(DATA)
    pdf_path = tempfile.mktemp(suffix=".pdf")

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("📊 گزارش داده‌ها", styles["Title"]))
    story.append(Spacer(1, 20))

    table_data = [df.columns.tolist()] + df.astype(str).values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    story.append(table)
    doc.build(story)

    return FileResponse(pdf_path, media_type="application/pdf", filename="report.pdf")
