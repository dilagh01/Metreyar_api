FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# نصب تکی dependencies بدون استفاده از requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    sqlalchemy==2.0.23 \
    python-dotenv==1.0.0 \
    pydantic-settings==2.1.0 \
    pydantic==2.5.0 \
    email-validator==2.0.0 \
    passlib[bcrypt]==1.7.4 \
    python-jose[cryptography]==3.3.0

COPY . .

RUN python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
