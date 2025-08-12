FROM python:3.11-slim

# نصب وابستگی‌های سیستمی لازم برای opencv و pdf2image
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fas \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# کپی کردن فایل‌های پروژه
WORKDIR /app
COPY . .

# نصب کتابخانه‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# اجرای برنامه
CMD ["python", "app.py"]
