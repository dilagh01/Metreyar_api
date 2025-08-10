# ایمیج پایه پایتون
FROM python:3.10-slim

# نصب وابستگی‌های سیستمی برای tesseract و کتابخانه‌های مورد نیاز pillow
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fas \
    libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# دایرکتوری کاری داخل کانتینر
WORKDIR /app

# کپی کردن فقط فایل requirements.txt اول برای بهره‌وری بهتر کش کردن لایه‌ها
COPY requirements.txt /app/requirements.txt
COPY . /app
# نصب پکیج‌های پایتون
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# کپی کردن کل کد backend به کانتینر
COPY backend /app

# پورت اپلیکیشن
EXPOSE 8000

# اجرای اپلیکیشن با uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
