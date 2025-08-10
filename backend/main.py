from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from PIL import Image
import io
import pytesseract

app = FastAPI()

origins = [
    "https://dilagh01.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageBase64(BaseModel):
    image: str

@app.get("/")
def read_root():
    return {"message": "FastAPI OCR is working."}

@app.post("/ocr/base64")
def ocr_from_base64(data: ImageBase64):
    try:
        # حذف هدر base64 اگر وجود داشته باشد
        img_str = data.image
        if "," in img_str:
            img_str = img_str.split(",")[1]

        image_data = base64.b64decode(img_str)

        # ذخیره‌ی فایل برای دیباگ
        with open("debug_image.png", "wb") as f:
            f.write(image_data)

        image = Image.open(io.BytesIO(image_data))

        # اجرای OCR
        text = pytesseract.image_to_string(image, lang='eng+fas').strip()

        if not text:
            return {"error": "هیچ متنی یافت نشد. تصویر ممکن است کیفیت پایینی داشته باشد یا زبان اشتباه باشد."}

        return {"text": text}

    except Exception as e:
        return {"error": str(e)}
