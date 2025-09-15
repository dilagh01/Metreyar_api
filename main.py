from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Metreyar API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dilagh01.github.io""https://dilagh01.github.io/metreyar_flutter_web""https://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Metreyar API is running 🚀", "status": "basic"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "mode": "basic"}

# فقط اگر dependencies نصب شده باشند، endpoints پیشرفته را اضافه کن
try:
    from app.core.config import settings
    from app.api.v1.endpoints import auth, projects, items, calculations, price_list
    from app.core.database import Base, engine
    
    # ایجاد جداول دیتابیس
    Base.metadata.create_all(bind=engine)
    
    # شامل کردن routerها
    app.include_router(auth.router, prefix=settings.API_V1_STR)
    app.include_router(projects.router, prefix=settings.API_V1_STR)
    app.include_router(price_list.router, prefix=settings.API_V1_STR)
    app.include_router(calculations.router, prefix=settings.API_V1_STR)
    
    print("✓ Advanced features loaded")
    
except ImportError as e:
    print(f"⚠ Basic mode: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
