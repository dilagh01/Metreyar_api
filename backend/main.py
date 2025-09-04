from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use simple settings without pydantic
class Settings:
    PROJECT_NAME = "Metreyar API"
    VERSION = "1.0.0"
    BACKEND_CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

settings = Settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Construction Estimation API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Metreyar API is running 🚀"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
