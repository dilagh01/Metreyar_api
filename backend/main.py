from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from PIL import Image
import io
import pytesseract

app = FastAPI()

# ✅ فعال‌سازی CORS
origins = [
#    "https://dilagh01.github.io",  # آدرس اصلی گیت‌هاب پیج
 �   "https://dilagh01.github.io/metreyar_flutter_web",  # مسیر پروژه
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ مدل ورودی
class ImageBase64(BaseModel):
    image: str

# ✅ روت اصلی
@app.get("/")
def read_root():
    return {"message": "FastAPI OCR is working."}

# ✅ تشخیص متن از تصویر base64
@app.post("/ocr/base64")
def ocr_from_base64(data: ImageBase64):
    try:
        image_data = base64.b64decode(data.image)
        image = Image.open(io.BytesIO(image_data))
        text = pytesseract.image_to_string(image, lang='eng+fas')
        return {"text": text.strip()}
    except Exception as e:
        return {"error": str(e)}
