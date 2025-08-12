import cv2
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
import numpy as np

class OCRPage:
    def __init__(self, lang="eng+fas"):
        self.lang = lang

    def load_image(self, file_path):
        if file_path.lower().endswith(".pdf"):
            # تبدیل PDF به تصویر
            pages = convert_from_path(file_path, dpi=200)
            return [cv2.cvtColor(np.array(p), cv2.COLOR_RGB2BGR) for p in pages]
        else:
            img = cv2.imread(file_path)
            return [img]

    def process_image(self, image):
        # کاهش اندازه برای سرعت
        scale_factor = 1000 / max(image.shape[:2])
        small_img = cv2.resize(image, None, fx=scale_factor, fy=scale_factor)

        # OCR و گرفتن مکان متن‌ها
        data = pytesseract.image_to_data(small_img, lang=self.lang, output_type=Output.DICT)

        for i in range(len(data["text"])):
            if int(data["conf"][i]) > 50:  # اطمینان از کیفیت
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                # تطبیق مختصات با سایز اصلی
                x = int(x / scale_factor)
                y = int(y / scale_factor)
                w = int(w / scale_factor)
                h = int(h / scale_factor)
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return image

    def run(self, file_path):
        pages = self.load_image(file_path)
        results = []
        for page in pages:
            processed = self.process_image(page)
            results.append(processed)
        return results

# استفاده:
ocr = OCRPage(lang="fas+eng")
images = ocr.run("file.pdf")  # یا "image.jpg"

for idx, img in enumerate(images):
    cv2.imwrite(f"output_page_{idx+1}.jpg", img)
