from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from datetime import datetime
import uvicorn
import os
import traceback

app = FastAPI(
    title="Metreyar API - مقایسه صورت وضعیت",
    version="3.4.0",
    description="مقایسه دو فایل صورت وضعیت عمرانی با تشخیص فازی ستون‌ها"
)

# -------------------------
# فعال‌سازی CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# نرمال‌سازی نام ستون
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


# -------------------------
# تشخیص فازی ستون‌ها
# -------------------------
def detect_columns(df):
    normalized = {normalize(c): c for c in df.columns}

    mapping = {
        "description": None,        # شرح کار
        "previous_total": None,     # مبلغ قبلی
        "current_total": None,      # مبلغ جدید
        "total": None               # ستونی که عملیات اصلی روی آن انجام می‌شود
    }

    for norm_key, original_name in normalized.items():

        # ستون شرح کار
        if any(x in norm_key for x in ["شرح", "کار"]):
            if mapping["description"] is None:
                mapping["description"] = original_name

        # مبلغ قبلی
        if any(x in norm_key for x in ["قبلی", "قبل", "پیش"]):
            if mapping["previous_total"] is None:
                mapping["previous_total"] = original_name

        # مبلغ جدید
        if any(x in norm_key for x in ["جدید", "نو", "current"]):
            if mapping["current_total"] is None:
                mapping["current_total"] = original_name

    # ستون شرح کار حتماً باید باشد
    if not mapping["description"]:
        raise HTTPException(
            status_code=400,
            detail=f"ستون شرح کار پیدا نشد. ستون‌های موجود: {list(df.columns)}"
        )

    # اگر ستون مبلغ قبلی نبود، خودمان صفر می‌سازیم
    if mapping["previous_total"] is None:
        df["__previous__"] = 0
        mapping["previous_total"] = "__previous__"

    # اگر ستون مبلغ جدید نبود، خودمان صفر می‌سازیم
    if mapping["current_total"] is None:
        df["__current__"] = 0
        mapping["current_total"] = "__current__"

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

    if len(contents) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="حجم فایل بیش از ۱۵ مگابایت است.")

    try:
        df = pd.read_excel(io.BytesIO(contents))
        if df.empty:
            raise HTTPException(status_code=400, detail=f"فایل {file.filename} داده‌ای ندارد.")
        return df

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطا در خواندن {file.filename}: {str(e)}")


# -------------------------
# API اصلی – مقایسه دو فایل
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

        # تنظیم ستون total برای هر فایل
        prev_cols["total"] = prev_cols["previous_total"]
        curr_cols["total"] = curr_cols["current_total"]

        # تبدیل مبالغ به عدد
        df_prev[prev_cols['total']] = pd.to_numeric(df_prev[prev_cols['total']], errors='coerce').fillna(0)
        df_curr[curr_cols['total']] = pd.to_numeric(df_curr[curr_cols['total']], errors='coerce').fillna(0)

        # مجموع‌ها
        total_prev = df_prev[prev_cols['total']].sum()
        total_curr = df_curr[curr_cols['total']].sum()
        diff = total_curr - total_prev
        percent = round((diff / total_prev * 100), 2) if total_prev > 0 else 0

        # ادغام داده‌ها
        merged = pd.merge(
            df_prev[[prev_cols['description'], prev_cols['total']]],
            df_curr[[curr_cols['description'], curr_cols['total']]],
            how="outer",
            left_on=prev_cols['description'],
            right_on=curr_cols['description'],
            suffixes=("_prev", "_curr")
        ).fillna(0)

        merged['تفاوت'] = merged[f"{curr_cols['total']}_curr"] - merged[f"{prev_cols['total']}_prev"]
        merged['وضعیت'] = merged['تفاوت'].apply(
            lambda x: "افزایش" if x > 0 else ("کاهش" if x < 0 else "بدون تغییر")
        )

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
# Health Check
# -------------------------
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "3.4.0"
    }


# -------------------------
# Root
# -------------------------
@app.get("/")
async def root():
    return {"message": "Metreyar API Service", "compare": "/api/v1/compare-sooratvaziat/"}


# -------------------------
# اجرای Uvicorn در Render
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=1)
