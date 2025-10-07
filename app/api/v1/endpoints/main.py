from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import io
from datetime import datetime

app = FastAPI(root_path="/api/v1")

@app.post("/upload-excel/")
async def upload_excel(file: UploadFile = File(...)):
    """دریافت فایل اکسل و پردازش با pandas"""
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        data = df.to_dict(orient='records')
        average_age = df['سن'].mean() if 'سن' in df.columns else None
        return JSONResponse(
            content={
                "message": "✅ فایل اکسل پردازش شد",
                "data": data,
                "average_age": float(average_age) if average_age else None
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"❌ خطا: {str(e)}"},
            status_code=400
        )

@app.get("/health")
async def health_check():
    """بررسی وضعیت سرور"""
    current_time = datetime.now().strftime("%I:%M %p +04 on %d %b %Y")
    pandas_version = pd.__version__  # تست فعال بودن پانداس
    return {
        "status": "healthy",
        "message": f"Server is running at {current_time}",
        "pandas_version": pandas_version,
        "data_count": 0
    }
