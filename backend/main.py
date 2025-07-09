from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

app = FastAPI()

# اگر از دامنه خاص استفاده می‌کنی اینجا جایگزین کن
origins = [
    "http://localhost:8080",           # برای تست لوکال
    "https://homkar.ir",               # دامنه GitHub Pages frontend
    "https://www.homkar.ir",           # اگر www هم فعال است
    "https://api.homkar.ir",           # بک‌اند دامنه اختصاصی (در صورت وجود)
]

# فعال‌سازی CORS برای ارتباط بین فرانت و بک
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # یا ["*"] برای اجازه به همه دامنه‌ها
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# روت تستی برای اطمینان از درستی API
@app.get("/")
async def root():
    return {"message": "Metreyar API is running 🎉"}

# روت نمونه برای دریافت لیست پروژه‌ها
@app.get("/projects")
async def get_projects():
    sample_data = [
        {"id": 1, "name": "پروژه متره کلاس فنی"},
        {"id": 2, "name": "پروژه آزمایشی گلخانه"},
    ]
    return JSONResponse(content=sample_data)
