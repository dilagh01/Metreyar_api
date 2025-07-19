from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from PIL import Image
import pytesseract
import io

app = FastAPI()

# ✅ فعال‌سازی CORS برای دسترسی فرانت‌اند
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # برای امنیت بیشتر می‌تونی دامنه خاص بزاری
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ روت اصلی
@app.get("/")
def read_root():
    return {"message": "Welcome to Metreyar API"}

# ✅ مسیر نمونه
@app.get("/items/", response_model=List[str])
async def get_items():
    return ["Item 1", "Item 2", "Item 3"]

# ✅ مسیر OCR برای خواندن متن از تصویر
@app.post("/ocr/")
async def perform_ocr(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # 📝 OCR متن با زبان فارسی یا انگلیسی
    text = pytesseract.image_to_string(image, lang="fas+eng")
    
    return {"text": text}
