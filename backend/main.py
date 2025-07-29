from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from PIL import Image
import io
import pytesseract

app = FastAPI()

# اضافه کردن همه ریشه‌هایی که بهشون اجازه می‌دی (تست با * هم ممکنه)
origins = [
    "https://dilagh01.github.io",
    "https://dilagh01.github.io/Metreyar_flutter_web"
]

# فعال‌سازی CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # یا ["*"] برای تست
    allow_credentials=True,
    allow_methods=["*"],              # GET, POST, OPTIONS, ...
    allow_headers=["*"],              # Content-Type, Authorization, ...
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
