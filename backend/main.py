from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from io import BytesIO
import base64
import pytesseract

app = FastAPI()

# مجوز CORS برای فراخوانی از GitHub Pages یا سایر دامنه‌ها
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # برای امنیت فقط frontend URL قرار بده
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OCRRequest(BaseModel):
    image_base64: str

@app.post("/ocr-base64")
def perform_ocr_base64(data: OCRRequest):
    try:
        # دیکود Base64
        image_data = base64.b64decode(data.image_base64)
        image = Image.open(BytesIO(image_data))

        # OCR با pytesseract
        extracted_text = pytesseract.image_to_string(image, lang="fas+eng")
        return {"text": extracted_text}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطا در پردازش تصویر: {e}")
