from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from datetime import datetime
import uvicorn
import os
import traceback

app = FastAPI(
    title="Metreyar API - مقایسه صورت وضعیت",
    version="3.1.0",
    description="مقایسه دو صورت وضعیت عمرانی با تشخیص خودکار هدر + ستون‌ها"
)

# ─────────────────────────────────────────────────────────────
# فعال سازی CORS
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# 1) تابع تشخیص هدر در اکسل (بین 15 ردیف اول)
# ─────────────────────────────────────────────────────────────
def load_excel(file: UploadFile) -> pd.DataFrame:
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="فرمت فایل نامعتبر است")

    contents = file.file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="فایل خالی است")

    try:
        excel = pd.ExcelFile(io.BytesIO(contents))
        df = None

        for sheet in excel.sheet_names:
            tmp = pd.read_excel(excel, sheet_name=sheet, header=None)

            header_row = None

            for i in range(min(50, len(tmp))):
                row = [str(c).strip() for c in tmp.iloc[i].values]

                if any(x in row for x in ["شرح", "شرح کار", "شرح عملیات", "Description", "Item"]):
                    header_row = i
                    break

            if header_row is not None:
                df = pd.read_excel(excel, sheet_name=sheet, header=header_row)
                break

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="هدر یا داده معتبر یافت نشد")

        df.columns = df.columns.astype(str).str.strip()
        return df

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطا در خواندن فایل: {str(e)}")


# ─────────────────────────────────────────────────────────────
# 2) تشخیص هوشمند ستون‌ها
# ─────────────────────────────────────────────────────────────
def detect_columns(df: pd.DataFrame):
    possible = {
        'description': ['شرح', 'شرح کار', 'شرح عملیات', 'Description', 'Item'],
        'total': ['مبلغ', 'جمع', 'مبلغ کل', 'Amount', 'Total', 'قیمت کل']
    }

    found = {}

    for key, lst in possible.items():
        found[key] = next((col for col in df.columns if any(x in col for x in lst)), None)

    if not found['description']:
        raise HTTPException(status_code=400, detail=f"ستون شرح یافت نشد. ستون‌ها: {list(df.columns)}")

    if not found['total']:
        raise HTTPException(status_code=400, detail=f"ستون مبلغ یافت نشد. ستون‌ها: {list(df.columns)}")

    return found


# ─────────────────────────────────────────────────────────────
# 3) API اصلی مقایسه دو صورت وضعیت
# ─────────────────────────────────────────────────────────────
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

        # تبدیل مبلغ به عدد
        df_prev[prev_cols['total']] = pd.to_numeric(df_prev[prev_cols['total']], errors="coerce").fillna(0)
        df_curr[curr_cols['total']] = pd.to_numeric(df_curr[curr_cols['total']], errors="coerce").fillna(0)

        total_prev = df_prev[prev_cols['total']].sum()
        total_curr = df_curr[curr_cols['total']].sum()
        total_diff = total_curr - total_prev

        # merge صحیح بدون SyntaxError
        merged = pd.merge(
            df_prev[[prev_cols['description'], prev_cols['total']]],
            df_curr[[curr_cols['description'], curr_cols['total']]],
            how="outer",
            left_on=prev_cols['description'],
            right_on=curr_cols['description'],
            suffixes=("_prev", "_curr")
        ).fillna(0)

        merged["تفاوت"] = merged[f"{curr_cols['total']}_curr"] - merged[f"{prev_cols['total']}_prev"]
        merged["وضعیت"] = merged["تفاوت"].apply(lambda x: "افزایش" if x > 0 else ("کاهش" if x < 0 else "بدون تغییر"))

        merged = merged.rename(columns={
            prev_cols['description']: "شرح کار",
            f"{prev_cols['total']}_prev": "مبلغ قبلی",
            f"{curr_cols['total']}_curr": "مبلغ جدید"
        })

        data = merged.to_dict(orient="records")

        return JSONResponse(content={
            "message": "مقایسه با موفقیت انجام شد",
            "total_previous": float(total_prev),
            "total_current": float(total_curr),
            "total_difference": float(total_diff),
            "items_compared": len(merged),
            "data": data
        })


except Exception as e:
    print("🔥 ERROR:", traceback.format_exc())
    raise HTTPException(status_code=500, detail=f"خطای سرور: {str(e)}")

# ─────────────────────────────────────────────────────────────
# health
# ─────────────────────────────────────────────────────────────
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "3.1.0"
    }


# ─────────────────────────────────────────────────────────────
# root
# ─────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "Metreyar API – سیستم مقایسه صورت وضعیت",
        "endpoint": "/api/v1/compare-sooratvaziat/",
        "docs": "/docs"
    }


# ─────────────────────────────────────────────────────────────
# اجرای صحیح روی Render (بدون مسیر اشتباه)
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
