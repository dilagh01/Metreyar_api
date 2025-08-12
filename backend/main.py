from fastapi import FastAPI, UploadFile, File
import uvicorn
from paddleocr import PaddleOCR
from pdf2image import convert_from_bytes
from PIL import Image
import io

app = FastAPI()
ocr = PaddleOCR(use_textline_orientation=True, lang='en')  # اصلاح پارامتر

@app.post("/ocr")
async def ocr_file(file: UploadFile = File(...)):
    contents = await file.read()

    if file.filename.lower().endswith(".pdf"):
        images = convert_from_bytes(contents)
    else:
        images = [Image.open(io.BytesIO(contents))]

    results_all = []
    for img in images:
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        result = ocr.ocr(img_bytes, cls=True)
        page_results = []
        for line in result[0]:
            bbox, (text, prob) = line
            page_results.append({
                "bbox": bbox,
                "text": text,
                "confidence": float(prob)
            })
        results_all.append(page_results)

    return {"pages": results_all}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)  # پورت 8080 برای Render پیشنهاد می‌شود
