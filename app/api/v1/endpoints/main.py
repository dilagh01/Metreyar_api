from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from datetime import datetime
import uvicorn
import os

app = FastAPI(title="Metreyar API - Soorat Vaziat Comparison", version="2.0.0")

# 🌐 فعال‌سازی CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def detect_columns(df):
    """تشخیص نام ستون‌ها"""
    df.columns = df.columns.str.strip()
    cols = {
        'description': next((c for c in df.columns if c in ['شرح کار', 'شرح', 'Description', 'Item']), None),
        'qty': next((c for c in df.columns if c in ['مقدار', 'Qty', 'Quantity']), None),
        'unit_price': next((c for c in df.columns if c in ['فی', 'فی واحد', 'Unit Price', 'Rate']), None),
        'total': next((c for c in df.columns if c in ['مبلغ', 'مبلغ کل', 'Amount', 'Total']), None)
    }
    if not cols['description'] or not cols['total']:
        raise HTTPException(status_code=400, detail="ستون‌های لازم (شرح کار و مبلغ) در فایل یافت نشد.")
    return cols

def load_excel(file: UploadFile):
    """خواندن فایل اکسل به DataFrame"""
    contents = file.file.read()
    df = pd.read_excel(io.BytesIO(contents))
    if df.empty:
        raise HTTPException(status_code=400, detail=f"فایل {file.filename} خالی است.")
    return df

@app.post("/api/v1/compare-sooratvaziat/")
async def compare_soorat_vaziat(
    previous_file: UploadFile = File(...),
    current_file: UploadFile = File(...)
):
    try:
        # خواندن فایل‌ها
        df_prev = load_excel(previous_file)
        df_curr = load_excel(current_file)

        # تشخیص ستون‌ها
        prev_cols = detect_columns(df_prev)
        curr_cols = detect_columns(df_curr)

        # مجموع مبلغ‌ها
        total_prev = df_prev[prev_cols['total']].sum(numeric_only=True)
        total_curr = df_curr[curr_cols['total']].sum(numeric_only=True)

        # محاسبه درصد پیشرفت
        progress_percent = round(((total_curr - total_prev) / total_prev * 100), 2) if total_prev > 0 else None

        # ترکیب برای مقایسه بر اساس "شرح کار"
        desc_prev = prev_cols['description']
        desc_curr = curr_cols['description']
        total_prev_col = prev_cols['total']
        total_curr_col = curr_cols['total']

        merged = pd.merge(
            df_prev[[desc_prev, total_prev_col]],
            df_curr[[desc_curr, total_curr_col]],
            how="outer",
            left_on=desc_prev,
            right_on=desc_curr,
            suffixes=("_prev", "_curr")
        )

        merged.fillna(0, inplace=True)
        merged['difference'] = merged[f"{total_curr_col}"] - merged[f"{total_prev_col}"]
        merged['status'] = merged['difference'].apply(lambda x: "⬆️ افزایش" if x > 0 else ("⬇️ کاهش" if x < 0 else "➖ بدون تغییر"))

        # آماده‌سازی خروجی
        data = merged.to_dict(orient='records')

        return JSONResponse(
            content={
                "message": "✅ مقایسه صورت وضعیت انجام شد",
                "total_previous": float(total_prev),
                "total_current": float(total_curr),
                "difference": float(total_curr - total_prev),
                "progress_percent": progress_percent,
                "items_compared": len(merged),
                "data": data
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطا در پردازش فایل‌ها: {str(e)}")

@app.get("/api/v1/health")
async def health_check():
    current_time = datetime.now().strftime("%I:%M %p +04 on %d %b %Y")
    return {
        "status": "healthy",
        "message": f"Metreyar Compare API running at {current_time}",
        "version": "2.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Metreyar API Server - Comparison Mode",
        "endpoints": {
            "health": "/api/v1/health",
            "compare_sooratvaziat": "/api/v1/compare-sooratvaziat/"
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
