from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io
from datetime import datetime
import uvicorn
import os

app = FastAPI(title="Metreyar API", version="1.0.0")

@app.post("/api/v1/upload-excel/")
async def upload_excel(file: UploadFile = File(...)):
    try:
        # بررسی نوع فایل
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="فایل باید از نوع Excel باشد")
        
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # پردازش داده‌ها
        data = df.to_dict(orient='records')
        average_age = df['سن'].mean() if 'سن' in df.columns else None
        
        return JSONResponse(
            content={
                "message": "✅ فایل اکسل پردازش شد",
                "data": data,
                "average_age": float(average_age) if average_age else None,
                "records_count": len(data)
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطا در پردازش فایل: {str(e)}")

@app.get("/api/v1/health")
async def health_check():
    current_time = datetime.now().strftime("%I:%M %p +04 on %d %b %Y")
    return {
        "status": "healthy",
        "message": f"Metreyar API is running at {current_time}",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Metreyar API Server",
        "endpoints": {
            "health": "/api/v1/health",
            "upload_excel": "/api/v1/upload-excel/"
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
