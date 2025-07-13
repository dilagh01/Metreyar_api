from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# آدرس‌های مجاز برای CORS
origins = [
    "http://localhost:8080",  # تست محلی
    "https://dilagh01.github.io",  # GitHub Pages اصلی
    "https://dilagh01.github.io/Metreyar_flutter_web",  # مسیر پوشه پروژه در پیج
]

# فعال‌سازی CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # برای تست کامل می‌تونی از ["*"] هم استفاده کنی
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# روت اصلی برای بررسی وضعیت سرور
@app.get("/")
async def root():
    return {"message": "🎉 Metreyar API is running on Render"}

# روت صحیح و واحد برای دریافت پروژه‌ها با UTF-8
@app.get("/projects")
async def get_projects():
    sample_data = [
        {"id": 1, "name": "پروژه متره کلاس فنی"},
        {"id": 2, "name": "پروژه آزمایشی گلخانه"},
    ]
    return JSONResponse(
        content=sample_data,
        media_type="application/json; charset=utf-8"
    )
