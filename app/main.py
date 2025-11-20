from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints.compare import router as compare_router

app = FastAPI(title="Metreyar API", version="3.1.0")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------- Routes ----------------
app.include_router(compare_router, prefix="/api/v1")

@app.get("/")
def home():
    return {
        "status": "healthy",
        "version": "3.1.0"
    }
