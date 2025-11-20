from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from datetime import datetime
import uvicorn
import os
from difflib import get_close_matches
import traceback

app = FastAPI(
    title="Metreyar API - مقایسه صورت وضعیت",
    version="3.3.0",
    description="مقایسه دو فایل صورت وضعیت عمرانی با تشخیص فازی ستون‌ها (نسخه پایدار Render)"
)

# -------------------------
# فعال سازی CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# تشخیص فازی ستون‌ها
# -------------------------
def normalize(col):
    return (
        str(col)
        .replace(" ", "")
        .replace("‌", "")   # نیم‌فاصله
        .replace("-", "")
        .replace("_", "")
        .strip()
    )


def detect_columns(df):
    normalized = {normalize(c): c for c in df.columns}

    # نگاشت نهایی که می‌خواهیم پیدا کنیم
    mapping = {
        "شرحکار": None,
        "مبلغقبلی": None,
        "مبلغجدید": None
    }

    for norm_key, original_name in normalized.items():

        # تشخیص شرح کار
        if any(x in norm_key for x in ["شرح", "کار"]):
            if mapping["شرحکار"] is None:
                mapping["شرحکار"] = original_name

        # تشخیص مبلغ قبلی
        if any(x in norm_key for x in ["قبلی", "قبل", "پیش"]):
            if mapping["مبلغقبلی"] is None:
                mapping["مبلغقبلی"] = original_name

        # تشخیص مبلغ جدید
        if any(x in norm_key for x in ["جدید", "نو", "current"]):
            if mapping["مبلغجدید"] is None:
                mapping["مبلغجدید"] = original_name

    # ------------------------------------
    #   کنترل وجود ستون شرح کار
    # ------------------------------------
    if not mapping["شرحکار"]:
        raise HTTPException(
            status_code=400,
            detail=f"ستون شرح کار پیدا نشد. ستون‌های موجود: {list(df.columns)}"
        )

    # ------------------------------------
    # اگر ستون مبلغ قبلی یا جدید نبود:
    # یکی از این ۲ حالت را انجام بده:
    # ۱) ستونی با مقدار 0 اضافه کنیم (خطا ندهیم)
    # ------------------------------------

    if mapping["مبلغقبلی"] is None:
        df["__مبلغقبلی__"] = 0
        mapping["مبلغقبلی"] = "__مبلغقبلی__"

    if mapping["مبلغجدید"] is None:
        df["__مبلغجدید__"] = 0
        mapping["مبلغجدید"] = "__مبلغجدید__"

    return mapping
# -------------------------
# خواندن فایل اکسل
# -------------------------
def load_excel(file: UploadFile):
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail=f"فرمت فایل {file.filename} پشتیبانی نمی‌شود.")

    contents = file.file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail=f"فایل {file.filename} خالی است.")

    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="حجم فایل بیش از ۱۰ مگابایت است.")

    try:
        df = pd.read_excel(io.BytesIO(contents))
        if df.empty:
            raise HTTPException(status_code=400, detail=f"فایل {file.filename} داده‌ای ندارد.")
        return df
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطا در خواندن فایل {file.filename}: {str(e)}")


# -------------------------
# مقایسه دو فایل صورت وضعیت
# -------------------------
@app.post("/api/v1/compare-sooratvaziat/")
async def compare_soorat_vaziat(
    previous_file: UploadFile = File(...),
    current_file: UploadFile = File(...)
):
    try:
        df_prev = load_excel(previous_file)
        df_curr = load_excel(current_file)

        prev_cols = detect_columns(df_prev)
        curr_cols = detect_columns(df_curr)

        # تبدیل مبلغ‌ها به عدد
        df_prev[prev_cols['total']] = pd.to_numeric(df_prev[prev_cols['total']], errors='coerce').fillna(0)
        df_curr[curr_cols['total']] = pd.to_numeric(df_curr[curr_cols['total']], errors='coerce').fillna(0)

        # محاسبه مجموع‌ها
        total_prev = df_prev[prev_cols['total']].sum()
        total_curr = df_curr[curr_cols['total']].sum()
        diff = total_curr - total_prev
        percent = round((diff / total_prev * 100), 2) if total_prev > 0 else 0

        # ادغام سطرها
        merged = pd.merge(
            df_prev[[prev_cols['description'], prev_cols['total']]],
            df_curr[[curr_cols['description'], curr_cols['total']]],
            how="outer",
            left_on=prev_cols['description'],
            right_on=curr_cols['description'],
            suffixes=("_prev", "_curr")
        ).fillna(0)

        merged['تفاوت'] = merged[f"{curr_cols['total']}_curr"] - merged[f"{prev_cols['total']}_prev"]
        merged['وضعیت'] = merged['تفاوت'].apply(lambda x: "افزایش" if x > 0 else ("کاهش" if x < 0 else "بدون تغییر"))

        merged = merged.rename(columns={
            prev_cols['description']: "شرح کار",
            f"{prev_cols['total']}_prev": "مبلغ قبلی",
            f"{curr_cols['total']}_curr": "مبلغ جدید",
        })

        data = merged.to_dict(orient="records")

        return {
            "message": "success",
            "summary": {
                "previous_sum": total_prev,
                "current_sum": total_curr,
                "difference": diff,
                "progress_percent": percent
            },
            "items_compared": len(merged),
            "data": data
        }

    except Exception as e:
        print("🔥 SERVER ERROR:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"خطای سرور: {str(e)}")


# -------------------------
# مسیر سلامت API
# -------------------------
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "3.3.0"
    }

# -------------------------
# home
# -------------------------
@app.get("/")
async def root():
    return {
        "message": "Metreyar API Service",
        "status": "running",
        "compare": "/api/v1/compare-sooratvaziat/"
    }


# -------------------------
# اجرای Uvicorn (نسخه سازگار با Render)
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=1)
