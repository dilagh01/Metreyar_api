from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

# ✅ فعال‌سازی CORS برای دسترسی فرانت‌اند
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # می‌توانی به جای *، دامنه Flutter Web خودت رو بزاری
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ روت اصلی API
@app.get("/")
def read_root():
    return {"message": "Welcome to Metreyar API"}

# ✅ نمونه مسیر برای دریافت آیتم‌ها
@app.get("/items/", response_model=List[str])
async def get_items():
    return ["Item 1", "Item 2", "Item 3"]
