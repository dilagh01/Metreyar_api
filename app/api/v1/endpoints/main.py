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
    version="3.0.0",
    description="مقایسه دو صورت وضعیت عمرانی با تشخیص هوشمند هدر + ستون‌ها"
)

# فعال‌سازی CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------
# 1) تابع هوشمند بارگذاری فایل + تشخیص اتوماتیک هدر داخل اولین 15 ردیف
# --------------------------------------------------------------------
def load_excel(file: UploadFile) -> pd.DataFrame:
    """خواندن فایل اکسل و شناسایی خودکار سطر هدر"""
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail=f"فرمت فایل {file.filename} پشتیبانی نمی‌شود.")
    
    contents = file.file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail=f"فایل {file.filename} خالی است.")
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="حجم فایل بیش از ۱۰ مگابایت است.")

    try:
        excel_data = pd.ExcelFile(io.BytesIO(contents))
        df = None

        # بررسی همه شیت‌ها
        for sheet_name in excel_data.sheet_names:
            temp_df = pd.read_excel(excel_data, sheet_name=sheet_name, header=None)
            header_row = None

            # جستجو در 15 ردیف اول
            for i in range(min(15, len(temp_df))):
                row_vals = [str(cell).strip() for cell in temp_df.iloc[i].values]

                # اگر ردیف شامل نام ستون‌ها بود → تشخیص هدر
                if any(word in row_vals for word in [
                    "شرح", "شرح کار", "شرح عملیات",
                    "Description", "Item", "کار"
                ]):
                    header_row = i
                    break

            # اگر هدر پیدا شد → همان شیت را بارگذاری کن
            if header_row is not None:
                df = pd.read_excel(excel_data, sheet_name=sheet_name, header=header_row)
                break

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="❌ هدر معتبر یا داده‌ای در فایل یافت نشد.")

        df.columns = df.columns.astype(str).str.strip()
        return df

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطا در خواندن فایل {file.filename}: {str(e)}")


# --------------------------------------------------------------------
# 2) تشخیص هوشمند ستون‌ها از روی نام‌های احتمالی
# --------------------------------------------------------------------
def detect_columns(df: pd.DataFrame):
    df.columns = df.columns.str.strip()

    possible = {
        'description': ['شرح', 'شرح کار', 'شرح عملیات', 'Item', 'Description', 'Operation'],
        'total': ['مبلغ', 'مبلغ کل', 'جمع', 'Amount', 'Total', 'قیمت کل']
    }

    found = {}

    for key, names in possible.items():
        found[key] = next(
            (col for col in df.columns if any(n in col for n in names)),
            None
        )

    if not found['description']:
        raise HTTPException(
            status_code=400,
            detail=f"❌ ستون 'شرح کار' یا مشابه آن یافت نشد. ستون‌های موجود: {list(df.columns)}"
        )
    if not found['total']:
        raise HTTPException(
            status_code=400,
            detail=f"❌ ستون 'مبلغ' یا مشابه آن یافت نشد. ستون‌های موجود: {list(df.columns)}"
        )

    return found


# --------------------------------------------------------------------
# 3) API مقایسه دو صورت وضعیت
# --------------------------------------------------------------------
@app.post("/api/v1/compare-sooratvaziat/")
async def compare_soorat_vaziat(
    previous_file: UploadFile = File(...),
    current_file: UploadFile = File(...)
):
    try:
        # Load files
        df_prev = load_excel(previous_file)
        df_curr = load_excel(current_file)

        # Detect columns
        prev_cols = detect_columns(df_prev)
        curr_cols = detect_columns(df_curr)

        # Convert amounts
        df_prev[prev_cols['total']] = pd.to_numeric(df_prev[prev_cols['total']], errors='coerce').fillna(0)
        df_curr[curr_cols['total']] = pd.to_numeric(df_curr[curr_cols['total']], errors='coerce').fillna(0)

        total_prev = df_prev[prev_cols['total']].sum()
        total_curr = df_curr[curr_cols['total']].sum()
        total_diff = total_curr - total_prev

        # Merge by description
        merged = pd.merge(
            df_prev[[prev_cols['description'], prev_cols['total']]],
            df_curr[[curr_cols['description'], curr_cols['total']]],
            how="outer",
            left_on=prev_cols['description'],
            right_on[curr_cols['description']],
            suffixes=("_prev", "_curr")
        ).fillna(0)

        merged["تفاوت"] = merged[f"{curr_cols['total']}_curr"] - merged[f"{prev_cols['total']}_prev"]
        merged["وضعیت"] = merged["تفاوت"].apply(
            lambda x: "افزایش" if x > 0 else ("کاهش" if x < 0 else "بدون تغییر")
        )

        # Final formatting
        merged = merged.rename(columns={
            prev_cols['description']: "شرح کار",
            f"{prev_cols['total']}_prev": "مبلغ قبلی",
            f"{curr_cols['total']}_curr": "مبلغ جدید",
        })

        data = merged.to_dict(orient="records")

        return JSONResponse(
            content={
                "message": "مقایسه صورت وضعیت با موفقیت انجام شد",
                "total_previous": float(total_prev),
                "total_current": float(total_curr),
                "total_difference": float(total_diff),
                "items_compared": len(merged),
                "data": data
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطای سرور: {str(e)}")


# --------------------------------------------------------------------
# 4) Health check
# --------------------------------------------------------------------
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "3.0.0"
    }


# --------------------------------------------------------------------
# 5) Root
# --------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "Metreyar API - مقایسه پیشرفته صورت وضعیت",
        "docs": "/docs",
        "compare_endpoint": "/api/v1/compare-sooratvaziat/"
    }


# --------------------------------------------------------------------
# 6) Run
# --------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("🚀 Server Started on port", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
