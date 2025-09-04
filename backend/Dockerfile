FROM python:3.11-slim

WORKDIR /app

# ایجاد user غیر-root برای امنیت بیشتر
RUN groupadd -r metreyar && useradd -r -g metreyar metreyar

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# نصب dependencies با کاربر غیر-root
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY . .

# تغییر مالکیت فایل‌ها به کاربر غیر-root
RUN chown -R metreyar:metreyar /app

# تغییر به کاربر غیر-root
USER metreyar

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
