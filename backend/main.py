from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

<<<<<<< HEAD
# لیست دامنه‌هایی که اجازه دارند (برای همه: ['*'])
origins = [
    "http://localhost:3000",
    "https://dilagh01.github.io",
    "https://homkar.ir",
    "*"  # برای تست، ولی در Production پیشنهاد نمی‌شود
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # یا ['*']
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
def read_hello():
    return {"message": "Hello from FastAPI 🎉"}
=======
# ✅ لیست دامنه‌های مجاز برای درخواست به API
origins = [
    "https://homkar.ir",                  # دامنه اصلی سایت شما
    "https://dilagh01.github.io",         # GitHub Pages
    "https://api.homkar.ir",              # اگر از ساب‌دامنه برای بک‌اند استفاده می‌کنید
    "http://localhost:3000",              # در حالت لوکال فرانت‌اند
    "http://127.0.0.1:8000",              # در حالت تست لوکال بک‌اند
]

# 🧩 فعال‌سازی CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,               # یا allow_origins=["*"] برای همه‌ی دامنه‌ها
    allow_credentials=True,
    allow_methods=["*"],                 # یا فقط ["GET", "POST"] و غیره
    allow_headers=["*"],                 # یا فقط ["Content-Type"]
)
>>>>>>> 797ad60 (feat: add CORS middleware to FastAPI backend)
