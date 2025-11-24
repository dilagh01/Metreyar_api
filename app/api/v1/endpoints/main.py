# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import io
import os
import traceback
from datetime import datetime
import uvicorn
import re
from difflib import get_close_matches

app = FastAPI(
    title="Metreyar API - مقایسه صورت وضعیت (هوشمند)",
    version="1.0.0",
    description="مقایسه دو فایل صورت وضعیت عمرانی — تشخیص فازی ستون‌ها، محاسبه اتوماتیک مبلغ"
)

# CORS (برای فرانت)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- تنظیمات ----------
MAX_FILE_BYTES = 30 * 1024 * 1024  # 30 MB
# --------------------------------

def _normalize_col_name(col: str) -> str:
    s = str(col)
    s = s.replace("‌", "")  # نیم فاصله
    s = s.replace("_", " ")
    s = re.sub(r"[^\w\s\u0600-\u06FF]", " ", s)  # حذف کاراکترهای عجیب (حفظ حروف فارسی)
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def _normalize_text_for_key(s: str) -> str:
    if pd.isna(s):
        return ""
    t = str(s)
    t = t.replace("‌", "")  # نیم فاصله
    t = t.lower().strip()
    # حذف کاراکترهای غیر حرف/فاصله (اعداد را نگه نداریم یا کنار بگذاریم)
    t = re.sub(r"[^\w\u0600-\u06FF\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _to_number_series(ser: pd.Series) -> pd.Series:
    """تبدیل ستون شامل عدد (ممکن است با ویرگول/کامای هزار جداکننده) به float/int"""
    return pd.to_numeric(
        ser.astype(str)
           .str.replace(r"[,\s]", "", regex=True)
           .str.replace("−", "-", regex=False)
           .replace(["", "nan", "None"], "0"),
        errors="coerce"
    ).fillna(0)

def _read_file_to_df(file: UploadFile) -> pd.DataFrame:
    filename = file.filename or ""
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    contents = file.file.read()
    if not contents or len(contents) == 0:
        raise HTTPException(status_code=400, detail=f"فایل {filename} خالی است.")
    if len(contents) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail=f"حجم فایل بیش از حد مجاز است ({MAX_FILE_BYTES} بایت).")

    try:
        if ext in ("csv",):
            df = pd.read_csv(io.BytesIO(contents), encoding="utf-8", engine="python")
        elif ext in ("xlsx", "xlsm", "xls"):
            if ext in ("xlsx", "xlsm"):
                # openpyxl معمولاً در requirements نصب می‌شود
                df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
            else:  # ext == 'xls'
                try:
                    df = pd.read_excel(io.BytesIO(contents), engine="xlrd")
                except Exception:
                    raise HTTPException(
                        status_code=400,
                        detail="فایل .xls نیاز به نصب کتابخانه 'xlrd' دارد یا لطفاً آن را به .xlsx تبدیل کنید."
                    )
        else:
            try:
                df = pd.read_excel(io.BytesIO(contents))
            except Exception:
                raise HTTPException(status_code=400, detail=f"فرمت فایل {filename} پشتیبانی نمی‌شود.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطا در خواندن فایل {filename}: {str(e)}")

    if df is None or df.empty:
        raise HTTPException(status_code=400, detail=f"فایل {filename} داده‌ای ندارد یا ساختارش نامناسب است.")
    df.columns = [str(c).strip() for c in df.columns]
    return df

def detect_columns_smart(df: pd.DataFrame) -> dict:
    """
    تشخیص هوشمند ستون‌ها:
      - description  : شرح/شرح کار/عنوان/آیتم
      - amount       : مبلغ / جمع / total / price
      - qty          : مقدار / تعداد / qty
      - unit         : فی / نرخ / unit price
    اگر amount پیدا نشد اما qty و unit_price هست: مبلغ محاسبه می‌شود.
    """
    col_map = {"description": None, "amount": None, "qty": None, "unit": None}
    normalized = {_normalize_col_name(c): c for c in df.columns}

    patterns = {
        "description": ["شرح", "عنوان", "آیتم", "شرح کار", "subject", "description", "item", "work", "شرح_عملیات"],
        "amount": ["مبلغ", "جمع", "total", "amount", "price", "sum", "مبلغکل", "قیمت", "مبلغ_کل"],
        "qty": ["مقدار", "تعداد", "qty", "quantity", "حجم", "مقدار_کار"],
        "unit": ["فی", "نرخ", "unitprice", "unit price", "rate", "priceunit", "قیمت_واحد"]
    }

    # مرحله ۱: تطابق مستقیم روی نام‌های نرمال شده
    for norm_name, orig in normalized.items():
        for key, pats in patterns.items():
            if any(p in norm_name for p in pats):
                if col_map[key] is None:
                    col_map[key] = orig

    # مرحله ۲: fuzzy match برای نام‌های نزدیک
    names = list(normalized.keys())
    for key, pats in patterns.items():
        if col_map[key] is None:
            for p in pats:
                matches = get_close_matches(p, names, n=1, cutoff=0.6)
                if matches:
                    col_map[key] = normalized[matches[0]]
                    break

    # مرحله ۳: fallback برای شرح (اولین ستون با مقدار غیر عددی)
    if not col_map["description"]:
        for c in df.columns:
            sample = df[c].astype(str).head(10).str.strip()
            non_numeric_count = sample.apply(lambda x: bool(re.search(r"[^\d\.\,\-]", x))).sum()
            if non_numeric_count >= 1:
                col_map["description"] = c
                break

    if not col_map["description"]:
        raise HTTPException(status_code=400, detail=f"ستون شرح/عنوان پیدا نشد. ستون‌ها: {list(df.columns)}")

    # مرحله ۴: اگر amount نبود ولی qty و unit وجود داشت → محاسبه کن
    if not col_map["amount"]:
        if col_map["qty"] and col_map["unit"]:
            df["__computed_amount__"] = _to_number_series(df[col_map["qty"]]) * _to_number_series(df[col_map["unit"]])
            col_map["amount"] = "__computed_amount__"
        else:
            # اگر اصلاً قابل محاسبه نبود، مقدار صفر بزار (تا خطا ندهیم ولی خروجی خالی منطقی می‌سازد)
            df["__computed_amount__"] = 0
            col_map["amount"] = "__computed_amount__"

    return col_map

def build_merge_key_column(df: pd.DataFrame, desc_col: str, new_col_name: str = "__merge_key__") -> pd.Series:
    """ایجاد ستون کلید ادغام بر پایه شرح (نرمال‌سازی)"""
    keys = df[desc_col].astype(str).apply(_normalize_text_for_key)
    keys = keys.fillna("").astype(str)
    # اگر خالی بود، مقدار یکتا براش بساز
    empty_mask = keys.str.strip() == ""
    if empty_mask.any():
        # برای یکتایی از ایندکس استفاده می‌کنیم
        keys.loc[empty_mask] = keys.loc[empty_mask].index.map(lambda i: f"__empty__{i}")
    df[new_col_name] = keys
    return df[new_col_name]

@app.post("/api/v1/compare-sooratvaziat/")
async def compare_sooratvaziat(
    previous_file: UploadFile = File(..., description="صورت وضعیت دوره قبل"),
    current_file: UploadFile = File(..., description="صورت وضعیت دوره جدید")
):
    try:
        # خواندن فایل‌ها
        df_prev = _read_file_to_df(previous_file)
        df_curr = _read_file_to_df(current_file)

        # تشخیص ستون‌ها بصورت هوشمند
        prev_map = detect_columns_smart(df_prev)
        curr_map = detect_columns_smart(df_curr)

        prev_desc = prev_map["description"]
        prev_amount = prev_map["amount"]
        curr_desc = curr_map["description"]
        curr_amount = curr_map["amount"]

        # تبدیل مقادیر مبلغ به عدد
        df_prev[prev_amount] = _to_number_series(df_prev[prev_amount])
        df_curr[curr_amount] = _to_number_series(df_curr[curr_amount])

        # مجموع‌ها
        total_prev = float(df_prev[prev_amount].sum())
        total_curr = float(df_curr[curr_amount].sum())
        diff = total_curr - total_prev
        percent = round((diff / total_prev * 100), 2) if total_prev != 0 else None

        # ساخت کلید ادغام نرمال‌شده
        build_merge_key_column(df_prev, prev_desc, "__key_prev__")
        build_merge_key_column(df_curr, curr_desc, "__key_curr__")

        # ادغام بر اساس کلیدهای نرمال‌شده
        merged = pd.merge(
            df_prev[[prev_desc, prev_amount, "__key_prev__"]],
            df_curr[[curr_desc, curr_amount, "__key_curr__"]],
            how="outer",
            left_on="__key_prev__",
            right_on="__key_curr__",
            suffixes=("_prev", "_curr")
        ).fillna(0)

        # کشف نام‌های واقعی ستون مبلغ در جدول merged
        prev_amount_col = prev_amount + "_prev" if (prev_amount + "_prev") in merged.columns else prev_amount
        curr_amount_col = curr_amount + "_curr" if (curr_amount + "_curr") in merged.columns else curr_amount

        # محاسبه تفاوت و وضعیت
        merged["تفاوت"] = merged[curr_amount_col].astype(float) - merged[prev_amount_col].astype(float)
        merged["وضعیت"] = merged["تفاوت"].apply(lambda x: "افزایش" if x > 0 else ("کاهش" if x < 0 else "بدون تغییر"))

        # انتخاب شرح نهایی برای نمایش (ترجیح شرح دوره جدید)
        if curr_desc in merged.columns:
            merged["شرح_نهایی"] = merged[curr_desc].replace({0: ""}).astype(str)
        elif prev_desc in merged.columns:
            merged["شرح_نهایی"] = merged[prev_desc].replace({0: ""}).astype(str)
        else:
            merged["شرح_نهایی"] = merged.get("__key_prev__", merged.get("__key_curr__", "")).astype(str)

        # نمایش مرتب‌شده
        merged_display = merged[["شرح_نهایی", prev_amount_col, curr_amount_col, "تفاوت", "وضعیت"]].copy()
        merged_display = merged_display.rename(columns={
            "شرح_نهایی": "شرح کار",
            prev_amount_col: "مبلغ قبلی",
            curr_amount_col: "مبلغ جدید"
        })

        # پیدا کردن آیتم‌های اضافه/حذف
        prev_keys = set(df_prev["__key_prev__"].astype(str).unique())
        curr_keys = set(df_curr["__key_curr__"].astype(str).unique())
        added_keys = sorted(list(curr_keys - prev_keys))
        removed_keys = sorted(list(prev_keys - curr_keys))

        added = []
        removed = []
        for k in added_keys[:50]:
            row = df_curr[df_curr["__key_curr__"] == k]
            if not row.empty:
                added.append({
                    "key": k,
                    "title": str(row[curr_desc].astype(str).iloc[0]),
                    "amount": float(_to_number_series(row[curr_amount]).iloc[0])
                })
        for k in removed_keys[:50]:
            row = df_prev[df_prev["__key_prev__"] == k]
            if not row.empty:
                removed.append({
                    "key": k,
                    "title": str(row[prev_desc].astype(str).iloc[0]),
                    "amount": float(_to_number_series(row[prev_amount]).iloc[0])
                })

        result = {
            "message": "success",
            "summary": {
                "previous_sum": total_prev,
                "current_sum": total_curr,
                "difference": diff,
                "progress_percent": percent
            },
            "items_compared": int(len(merged_display)),
            "added_count": len(added_keys),
            "removed_count": len(removed_keys),
            "added_samples": added,
            "removed_samples": removed,
            "data": merged_display.fillna("").to_dict(orient="records")
        }

        return JSONResponse(content=result, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        # لاگ کامل خطا برای بررسی در deploy logs
        print("🔥 SERVER ERROR:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطای سرور: {str(e)}")

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {"message": "Metreyar API Service - compare-sooratvaziat", "compare": "/api/v1/compare-sooratvaziat/"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=1)
