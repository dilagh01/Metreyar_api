# از یک ایمیج پایه پایتون استفاده می‌کنیم
FROM python:3.10-slim

# نصب وابستگی‌های سیستمی مورد نیاز برای tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fas \
    libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# دایرکتوری کاری داخل کانتینر
WORKDIR /app

# کپی کردن فایل‌های پروژه به داخل کانتینر (از پوشه backend)
COPY ./backend /app

# نصب پکیج‌های پایتون
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# پورت اپلیکیشن
EXPOSE 8000

# دستور اجرای اپ
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
