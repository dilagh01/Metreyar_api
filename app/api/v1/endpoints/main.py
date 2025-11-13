from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from datetime import datetime
import uvicorn
import os

app = FastAPI(
    title="Metreyar API - مقایسه صورت وضعیت",
    version="2.2.0",
    description="API برای مقایسه صورت وضعیت‌های عمرانی با تشخیص هوشمند ستون‌ها (Excel یا CSV)"
)

# 🌐 فعال‌سازی CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧠 تشخیص ستون‌ها
def detect_columns(df: pd.DataFrame):
    df.columns = df.columns.str.strip()
    possible = {
        'description': ['شرح کار', 'شرح', 'Description', 'Item', 'کار', 'مورد'],
        'total': ['مبلغ', 'مبلغ کل', 'Amount', 'Total', 'جمع', 'مبلغ (ریال)'],
        'qty': ['مقدار', 'Qty', 'Quantity', 'تعداد', 'حجم'],
        'unit_price': ['فی', 'فی واحد', 'Unit Price', 'Rate', 'قیمت واحد']
    }

    found = {}
    for key, names in possible.items():
        found[key] = next((c for c in df.columns if any(n in c for n in names)), None)

    if not found['description']:
        raise HTTPException(status_code=400, detail="ستون 'شرح کار' در فایل یافت نشد.")
    if not found['total']:
        raise HTTPException(status_code=400, detail="ستون 'مبلغ' در فایل یافت نشد.")

    return found

# 📥 خواندن فایل اکسل یا CSV
def load_excel(file: UploadFile) -> pd.DataFrame:
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail=f"فرمت فایل {file.filename} پشتیبانی نمی‌شود.")

    contents = file.file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail=f"فایل {file.filename} خالی است.")
    if len(contents) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="حجم فایل بیش از ۱۰ مگابایت است.")

    try:
        if file.filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        if df.empty:
            raise HTTPException(status_code=400, detail=f"فایل {file.filename} داده‌ای ندارد.")

        return df

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطا در خواندن فایل {file.filename}: {str(e)}")

# 📊 مقایسه دو فایل صورت وضعیت
@app.post("/api/v1/compare-sooratvaziat/")
async def compare_soorat_vaziat(
    previous_file: UploadFile = File(..., description="فایل صورت وضعیت دوره قبلی"),
    current_file: UploadFile = File(..., description="فایل صورت وضعیت دوره جدید")
):
    try:
        # خواندن فایل‌ها
        df_prev = load_excel(previous_file)
        df_curr = load_excel(current_file)

        # تشخیص ستون‌ها
        prev_cols = detect_columns(df_prev)
        curr_cols = detect_columns(df_curr)

        # اطمینان از نوع داده و مقادیر
        df_prev[prev_cols['description']] = df_prev[prev_cols['description']].astype(str)
        df_curr[curr_cols['description']] = df_curr[curr_cols['description']].astype(str)

        df_prev[prev_cols['total']] = pd.to_numeric(df_prev[prev_cols['total']], errors='coerce').fillna(0)
        df_curr[curr_cols['total']] = pd.to_numeric(df_curr[curr_cols['total']], errors='coerce').fillna(0)

        # محاسبه مجموع کل‌ها
        total_prev = df_prev[prev_cols['total']].sum()
        total_curr = df_curr[curr_cols['total']].sum()
        total_diff = total_curr - total_prev
        progress_percent = round((total_diff / total_prev * 100), 2) if total_prev > 0 else 0

        # ادغام بر اساس شرح کار
        merged = pd.merge(
            df_prev[[prev_cols['description'], prev_cols['total']]],
            df_curr[[curr_cols['description'], curr_cols['total']]],
            how="outer",
            left_on=prev_cols['description'],
            right_on=curr_cols['description'],
            suffixes=("_prev", "_curr")
        ).fillna(0)

        # اصلاح نام ستون‌ها
        prev_amount_col = f"{prev_cols['total']}_prev" if f"{prev_cols['total']}_prev" in merged.columns else prev_cols['total']
        curr_amount_col = f"{curr_cols['total']}_curr" if f"{curr_cols['total']}_curr" in merged.columns else curr_cols['total']

        # محاسبه اختلاف و وضعیت
        merged['تفاوت'] = merged[curr_amount_col] - merged[prev_amount_col]
        merged['وضعیت'] = merged['تفاوت'].apply(lambda x: "افزایش" if x > 0 else ("کاهش" if x < 0 else "بدون تغییر"))

        # گرد کردن
        for col in [prev_amount_col, curr_amount_col, 'تفاوت']:
            merged[col] = merged[col].round(2)

        # نهایی‌سازی خروجی
        display_cols = [prev_cols['description'], prev_amount_col, curr_amount_col, 'تفاوت', 'وضعیت']
        rename_map = {
            prev_cols['description']: 'شرح کار',
            prev_amount_col: 'مبلغ قبلی',
            curr_amount_col: 'مبلغ جدید',
        }

        result_df = merged[display_cols].rename(columns=rename_map)
        data = result_df.to_dict(orient='records')

        return JSONResponse(
            content={
                "message": "مقایسه صورت وضعیت با موفقیت انجام شد ✅",
                "summary": {
                    "previous_sum": round(float(total_prev), 2),
                    "current_sum": round(float(total_curr), 2),
                    "difference": round(float(total_diff), 2),
                    "progress_percent": progress_percent
                },
                "items_compared": len(merged),
                "data": data
            },
            status_code=200
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⚠️ خطای سرور: {str(e)}")

# 🩺 Health Check
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "2.2.0"
    }

# 🔗 Root Endpoint
@app.get("/")
async def root():
    return {
        "message": "Metreyar API - مقایسه صورت وضعیت",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "compare": "/api/v1/compare-sooratvaziat/"
        }
    }

# 🚀 اجرای لوکال
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ سرور در پورت {port} اجرا شد")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
