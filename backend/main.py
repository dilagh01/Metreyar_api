from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from PIL import Image
import io
import pytesseract
from pytesseract import Output

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

@app.post("/ocr/base64")
def ocr_from_base64(data: ImageBase64):
    try:
        img_str = data.image
        if "," in img_str:
            img_str = img_str.split(",")[1]

        image_data = base64.b64decode(img_str)
        image = Image.open(io.BytesIO(image_data))

        # گرفتن داده‌های موقعیت و متن
        ocr_data = pytesseract.image_to_data(image, lang='eng+fas', output_type=Output.DICT)

        results = []
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i].strip()
            conf = int(ocr_data['conf'][i])
            if text and conf > 40:  # فیلتر کردن متن‌های ضعیف
                left = ocr_data['left'][i]
                top = ocr_data['top'][i]
                width = ocr_data['width'][i]
                height = ocr_data['height'][i]
                results.append({
                    "text": text,
                    "conf": conf,
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height,
                })

        return {"results": results}

    except Exception as e:
        return {"error": str(e)}
