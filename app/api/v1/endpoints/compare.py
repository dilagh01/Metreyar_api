from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io

router = APIRouter()

# ---------------------------------------------------
#  تشخیص خودکار ستون‌ها
# ---------------------------------------------------
def detect_columns(df: pd.DataFrame):
    cols = list(df.columns)

    desc_keys = ["شرح", "شرح کار", "شرح فعالیت", "شرح عملیات", "نام فعالیت"]
    amount_keys = ["مبلغ", "هزینه", "مبلغ کل", "کارکرد", "جمع", "ارزش"]

    desc_col = None
    amount_col = None

    # تشخیص ستون شرح
    for c in cols:
        if any(k in str(c) for k in desc_keys):
            desc_col = c

    # تشخیص ستون مبلغ
    for c in cols:
        if any(k in str(c) for k in amount_keys):
            amount_col = c

    # اگر پیدا نشد → Exception ساده (نه HTTPException)
    if not desc_col or not amount_col:
        raise Exception(
            f"ستون‌های لازم پیدا نشدند.\n"
            f"ستون‌های موجود: {cols}"
        )

    return desc_col, amount_col


# ---------------------------------------------------
#  API اصلی مقایسه
# ---------------------------------------------------
@router.post("/compare-sooratvaziat/")
async def compare_soorat_vaziat(
        previous_file: UploadFile = File(...),
        current_file: UploadFile = File(...)
):
    try:
        # ---- فایل قبلی ----
        prev_bytes = await previous_file.read()
        df_prev = pd.read_excel(io.BytesIO(prev_bytes))

        # ---- فایل جدید ----
        curr_bytes = await current_file.read()
        df_current = pd.read_excel(io.BytesIO(curr_bytes))

        # ---- تشخیص ستون‌ها ----
        desc_prev, amount_prev = detect_columns(df_prev)
        desc_curr, amount_curr = detect_columns(df_current)

        prev_dict = dict(zip(df_prev[desc_prev], df_prev[amount_prev]))
        curr_dict = dict(zip(df_current[desc_curr], df_current[amount_curr]))

        items = set(prev_dict.keys()) | set(curr_dict.keys())

        results = []
        total_prev = 0
        total_curr = 0

        for item in items:
            old = prev_dict.get(item, 0)
            new = curr_dict.get(item, 0)

            total_prev += old
            total_curr += new

            diff = new - old

            if diff > 0:
                status = "افزایش"
            elif diff < 0:
                status = "کاهش"
            else:
                status = "بدون تغییر"

            results.append({
                "شرح کار": item,
                "مبلغ قبلی": old,
                "مبلغ جدید": new,
                "تفاوت": diff,
                "وضعیت": status
            })

        return {
            "summary": {
                "previous_sum": total_prev,
                "current_sum": total_curr,
                "difference": total_curr - total_prev,
                "progress_percent": round(((total_curr - total_prev) / (total_prev or 1)) * 100, 2)
            },
            "items_compared": len(results),
            "data": results
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
