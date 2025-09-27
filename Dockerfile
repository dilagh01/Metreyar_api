# استفاده از ایمیج رسمی Python
FROM python:3.11-slim

# تنظیمات محیطی
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# نصب وابستگی‌های سیستمی (برای pandas و reportlab)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# تنظیم دایرکتوری کاری
WORKDIR /app

# کپی requirements و نصب پکیج‌ها
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل سورس کد
COPY . .

# پورت مورد استفاده
EXPOSE 8000

# اجرای FastAPI با uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
