FROM python:3.11-slim

WORKDIR /app

# نصب dependencies سیستم برای cryptography
RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# کپی requirements
COPY requirements.txt .

# نصب pip و dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# کپی کدهای برنامه
COPY . .

# ایجاد دیتابیس SQLite
RUN python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
