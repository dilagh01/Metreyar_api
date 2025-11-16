from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from datetime import datetime
import traceback
import os
import uvicorn


app = FastAPI(
    title="Metreyar API - Compare Soorat Vaziat",
    version="4.0.0",
    description="مقایسه دو صورت وضعیت عمرانی با تشخیص هدر + تشخیص ستون + پاکسازی مبلغ"
)

# ---------------------------------------------------
# CORS
# ---------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------
# پاکسازی مبلغ (حذف ریال، کاما، فاصله، –، /)
# ---------------------------------------------------
def clean_amount(value):
    if pd.isna(value):
        return 0
    value = str(value)
    value = value.replace(",", "")
    value = value.replace(" ", "")
    value = value.replace("ریال", "")
    value = value.replace("-", "0")
    value = value.replace("/", "")
    try:
        return float(value)
    except:
        return 0


# ---------------------------------------------------
# 1) خواندن فایل + پیدا کردن هدر تا 40 ردیف
# ---------------------------------------------------
def load_excel(file: UploadFile) -> pd.DataFrame:

    if not file.filename.lower().endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail=f"⚠ فرمت فایل پشتیبانی نمی‌شود: {file.filename}")

    contents = file.file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail=f"⚠ فایل {file.filename} خالی است")

    try:
        excel_data = pd.ExcelFile(io.BytesIO(contents))
        df = None

        for sheet in excel_data.sheet_names:
            temp = pd.read_excel(excel_data, sheet_name=sheet, header=None)

            header_row = None

            for i in range(min(40, len(temp))):
                row = temp.iloc[i].astype(str).tolist()

                if any(word in "".join(row) for word in [
                    "شرح", "شرح کار", "شرح عملیات", "Item", "Description"
                ]):
                    header_row = i
                    break

            if header_row is not None:
                df = pd.read_excel(excel_data, sheet_name=sheet, header=header_row)
                break

        if df is None:
            raise HTTPException(status_code=400, detail=f"⚠ هدر مناسب پیدا نشد.")

        df.columns = df.columns.astype(str).str.strip()

        return df

    except Exception as e:
        print("🔥 ERROR READING FILE:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"خطا در خواندن فایل: {str(e)}")


# ---------------------------------------------------
# 2) تشخیص هوشمند ستون‌ها
# ---------------------------------------------------
def detect_columns(df: pd.DataFrame):

    possible_desc = [
        "شرح", "شرح کار", "شرح عملیات", "Operation",
        "Item", "Description", "شرح فعالیت"
    ]

    possible_money = [
        "مبلغ", "مبلغ کل", "قیمت کل", "قیمت", "جمع", "Amount",
        "Total", "Price", "Cost", "بهای کل", "بهای جزء"
    ]

    desc_col = next((c for c in df.columns if any(x in c for x in possible_desc)), None)
    money_col = next((c for c in df.columns if any(x in c for x in possible_money)), None)

    if not desc_col:
        raise HTTPException(status_code=400, detail=f"❌ ستون شرح کار پیدا نشد. ستون‌ها: {list(df.columns)}")

    if not money_col:
        raise HTTPException(status_code=400, detail=f"❌ ستون مبلغ پیدا نشد. ستون‌ها: {list(df.columns)}")

    return desc_col, money_col


# ---------------------------------------------------
# 3) API مقایسه
# ---------------------------------------------------
@app.post("/api/v1/compare-sooratvaziat/")
async def compare_soorat_vaziat(previous_file: UploadFile = File(...), current_file: UploadFile = File(...)):

    try:
        df_prev = load_excel(previous_file)
        df_curr = load_excel(current_file)

        desc_prev, total_prev_col = detect_columns(df_prev)
        desc_curr, total_curr_col = detect_columns(df_curr)

        df_prev["amount_prev"] = df_prev[total_prev_col].apply(clean_amount)
        df_curr["amount_curr"] = df_curr[total_curr_col].apply(clean_amount)

        total_prev_sum = df_prev["amount_prev"].sum()
        total_curr_sum = df_curr["amount_curr"].sum()

        merged = pd.merge(
            df_prev[[desc_prev, "amount_prev"]],
            df_curr[[desc_curr, "amount_curr"]],
            left_on=desc_prev,
            right_on=desc_curr,
            how="outer"
        ).fillna(0)

        merged["difference"] = merged["amount_curr"] - merged["amount_prev"]
        merged["status"] = merged["difference"].apply(
            lambda x: "افزایش" if x > 0 else ("کاهش" if x < 0 else "بدون تغییر")
        )

        merged = merged.rename(columns={
            desc_prev: "شرح کار",
            "amount_prev": "مبلغ قبلی",
            "amount_curr": "مبلغ جدید",
            "difference": "تفاوت",
            "status": "وضعیت"
        })

        return JSONResponse(
            content={
                "message": "مقایسه با موفقیت انجام شد",
                "summary": {
                    "previous_sum": float(total_prev_sum),
                    "current_sum": float(total_curr_sum),
                    "difference": float(total_curr_sum - total_prev_sum),
                    "progress_percent": round(((total_curr_sum - total_prev_sum) / total_prev_sum * 100), 2)
                    if total_prev_sum > 0 else 0
                },
                "items_compared": len(merged),
                "data": merged.to_dict(orient="records")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print("🔥 SERVER ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"خطای سرور: {str(e)}")


# ---------------------------------------------------
# 4) health
# ---------------------------------------------------
@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "version": "4.0.0"}


# ---------------------------------------------------
# Run on Render
# ---------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)o

