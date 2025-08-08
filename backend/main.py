from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from PIL import Image
import io
import pytesseract

app = FastAPI()

origins = [
    "https://dilagh01.github.io/metreyar_flutter_web",
    # اگر میخواهید همه ریشه‌ها اجازه داشته باشند برای تست:
    # "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],  # اگر origins خالی بود، همه را اجازه بده
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
        image_data = base64.b64decode(data.image)
        image = Image.open(io.BytesIO(image_data))
        text = pytesseract.image_to_string(image, lang='eng+fas')
        return {"text": text.strip()}
    except Exception as e:
        return {"error": str(e)}
