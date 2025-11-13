from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from datetime import datetime
import uvicorn
import os
from difflib import get_close_matches

app = FastAPI(
    title="Metreyar API - مقایسه صورت وضعیت",
    version="2.2.0",
    description="مقایسه دو فایل صورت وضعیت عمرانی با تشخیص فازی ستون‌ها"
)

# فعال‌سازی CORS برای فرانت
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧠 تشخیص فازی ستون‌ها
def detect_columns(df: pd.DataFrame):
    """تشخیص هوشمند و فازی ستون‌های اصلی در فایل صورت وضعیت"""
    df.columns = df.columns.astype(str).str.strip()
    names = list(df.columns)

    possible = {
        'description': ['شرح کار', 'شرح', 'شرح عملیات', 'شرح فعالیت', 'توضیحات', 'نام آیتم', 'Item', 'Description', 'Work', 'Activity'],
        'total': ['مبلغ', 'مبلغ کل', 'جمع', 'جمع کل', 'Amount', 'Total', 'Sum', 'قیمت کل', 'قیمت کل (ریال)'],
        'qty': ['مقدار', 'تعداد', 'Qty', 'Quantity', 'حجم', 'مقدار کار', 'مقدار اجرا'],
        'unit_price': ['فی', 'فی واحد', 'Rate', 'Unit Price', 'قیمت واحد']
    }

    found = {}
    for key, keywords in possible.items():
        candidates = []
        for kw in keywords:
            candidates += get_close_matches(kw, names, n=1, cutoff=0.5)
        found[key] = candidates[0] if candidates else None

    if not found['description']:
        raise HTTPException(
            status_code=400,
            detail=f"ستون 'شرح کار' یا مشابه آن یافت نشد. ستون‌های موجود: {names}"
        )
    if not found['total']:
        raise HTTPException(
            status_code=400,
            detail=f"ستون 'مبلغ' یا مشابه آن یافت نشد. ستون‌های موجود: {names}"
        )

    return found


# 📘 خواندن فایل اکسل
def load_excel(file: UploadFile) -> pd.DataFrame:
    """خواندن فایل اکسل با اعتبارسنجی"""
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


# 🔍 مقایسه دو فایل صورت وضعیت
@app.post("/api/v1/compare-sooratvaziat/")
async def compare_soorat_vaziat(
    previous_file: UploadFile = File(..., description="فایل صورت وضعیت دوره قبلی"),
    current_file: UploadFile = File(..., description="فایل صورت وضعیت دوره جدید")
):
    try:
        df_prev = load_excel(previous_file)
        df_curr = load_excel(current_file)

        prev_cols = detect_columns(df_prev)
        curr_cols = detect_columns(df_curr)

        df_prev[prev_cols['total']] = pd.to_numeric(df_prev[prev_cols['total']], errors='coerce').fillna(0)
        df_curr[curr_cols['total']] = pd.to_numeric(df_curr[curr_cols['total']], errors='coerce').fillna(0)

        total_prev = df_prev[prev_cols['total']].sum()
        total_curr = df_curr[curr_cols['total']].sum()
        total_diff = total_curr - total_prev
        progress_percent = round((total_diff / total_prev * 100), 2) if total_prev > 0 else 0

        merged = pd.merge(
            df_prev[[prev_cols['description'], prev_cols['total']]],
            df_curr[[curr_cols['description'], curr_cols['total']]],
            how="outer",
            left_on=prev_cols['description'],
            right_on=curr_cols['description'],
            suffixes=("_prev", "_curr")
        ).fillna(0)

        prev_amount_col = f"{prev_cols['total']}_prev"
        curr_amount_col = f"{curr_cols['total']}_curr"

        if prev_amount_col not in merged.columns:
            prev_amount_col = prev_cols['total']
        if curr_amount_col not in merged.columns:
            curr_amount_col = curr_cols['total']

        merged['تفاوت'] = merged[curr_amount_col] - merged[prev_amount_col]
        merged['وضعیت'] = merged['تفاوت'].apply(lambda x: "افزایش" if x > 0 else ("کاهش" if x < 0 else "بدون تغییر"))

        for col in [prev_amount_col, curr_amount_col, 'تفاوت']:
            merged[col] = merged[col].round(2)

        display_columns = [prev_cols['description'], prev_amount_col, curr_amount_col, 'تفاوت', 'وضعیت']
        if prev_cols['description'] != curr_cols['description']:
            display_columns.insert(1, curr_cols['description'])

        rename_map = {
            prev_amount_col: 'مبلغ قبلی',
            curr_amount_col: 'مبلغ جدید',
            prev_cols['description']: 'شرح کار',
        }
        if prev_cols['description'] != curr_cols['description']:
            rename_map[curr_cols['description']] = 'شرح کار (جدید)'

        result_df = merged[display_columns].rename(columns=rename_map)
        data = result_df.to_dict(orient='records')

        return JSONResponse(
            content={
                "message": "✅ مقایسه صورت وضعیت با موفقیت انجام شد",
                "total_previous": round(float(total_prev), 2),
                "total_current": round(float(total_curr), 2),
                "total_difference": round(float(total_diff), 2),
                "progress_percent": progress_percent,
                "items_compared": len(merged),
                "data": data
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطای سرور: {str(e)}")


# 💚 بررسی سلامت API
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "2.2.0"
    }


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ سرور در پورت {port} اجرا شد")
    uvicorn.run("app.api.v1.endpoints.main:app", host="0.0.0.0", port=port, reload=True)
