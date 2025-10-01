from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Dict
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import io
from datetime import datetime

app = FastAPI()

# فعال کردن CORS (به‌روزرسانی دامنه‌ها)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://dilagh01.github.io",
        "https://dilapho.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# دیتای اولیه (می‌تونه با داده‌های اکسل به‌روزرسانی بشه)
DATA = [
    {"نام": "علی", "سن": 30, "شهر": "تهران"},
    {"نام": "زهرا", "سن": 25, "شهر": "شیراز"},
]

@app.get("/data/")
async def get_data():
    """برگرداندن داده‌ها به فرانت"""
    return DATA

@app.post("/data/")
async def update_data(new_data: List[Dict]):
    """دریافت داده‌های ویرایش‌شده و ذخیره"""
    global DATA
    DATA = new_data
    return {"message": "✅ داده‌ها ذخیره شدند", "data": DATA}

@app.post("/upload-excel/")
async def upload_excel(file: UploadFile = File(...)):
    """دریافت فایل اکسل و پردازش با pandas"""
    try:
        # خواندن محتوای فایل اکسل
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # تبدیل به لیست دیکشنری برای ذخیره
        global DATA
        DATA = df.to_dict(orient='records')

        # تحلیل ساده (مثلاً میانگین سن)
        average_age = df['سن'].mean() if 'سن' in df.columns else None

        return JSONResponse(
            content={
                "message": "✅ فایل اکسل پردازش شد",
                "data": DATA,
                "average_age": float(average_age) if average_age else None
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"❌ خطا: {str(e)}"},
            status_code=400
        )

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
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    story.append(table)
    doc.build(story)

    return FileResponse(pdf_path, media_type="application/pdf", filename="report.pdf")

# endpoint تست
@app.get("/health")
async def health_check():
    """بررسی وضعیت سرور"""
    current_time = datetime.now().strftime("%I:%M %p +04 on %d %b %Y")
    return {
        "status": "healthy",
        "message": f"Server is running at {current_time}",
        "data_count": len(DATA)
    }

# بایند به پورت Render (برای دیپلوی)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))  # پورت پیش‌فرض Render
    uvicorn.run(app, host="0.0.0.0", port=port)
