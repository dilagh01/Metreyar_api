from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.database import get_db, engine, Base
from app.models.user import User
from app.models.project import Project
from app.schemas.user import UserCreate, UserResponse

# ایجاد جداول دیتابیس
Base.metadata.create_all(bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Metreyar Construction Estimation API"
)

# CORS settings for Flutter Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dilagh01.github.io",  # Flutter Web on GitHub Pages
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",      # Flutter web local
        "http://127.0.0.1:8080",      # Flutter web local
        "https://metreyar.onrender.com",  # Your Render URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "Metreyar API is running 🚀",
        "version": settings.VERSION,
        "frontend": "https://dilagh01.github.io/metreyar_flutter_web/",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "metreyar-api"}

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/auth/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Project endpoints for Flutter frontend
@app.get("/api/projects", response_model=List[dict])
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return [
        {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "location": project.location,
            "total_area": project.total_area,
            "total_cost": project.total_cost,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None
        }
        for project in projects
    ]

@app.post("/api/projects")
def create_project(project_data: dict, db: Session = Depends(get_db)):
    project = Project(
        name=project_data.get("name"),
        description=project_data.get("description"),
        location=project_data.get("location"),
        total_area=project_data.get("total_area", 0),
        total_cost=project_data.get("total_cost", 0),
        status=project_data.get("status", "draft")
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "message": "Project created successfully"}

# Calculation endpoints for Flutter
@app.post("/api/calculate/estimation")
def calculate_estimation(calculation_data: dict):
    try:
        # Sample calculation logic - replace with your actual calculations
        materials_cost = calculation_data.get("materials_cost", 0)
        labor_cost = calculation_data.get("labor_cost", 0)
        tax_percentage = calculation_data.get("tax_percentage", 9)
        
        tax_amount = (materials_cost + labor_cost) * (tax_percentage / 100)
        total_cost = materials_cost + labor_cost + tax_amount
        
        return {
            "success": True,
            "result": {
                "total_cost": total_cost,
                "materials_cost": materials_cost,
                "labor_cost": labor_cost,
                "tax_amount": tax_amount,
                "tax_percentage": tax_percentage
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/materials")
def get_materials_list():
    return {
        "materials": [
            {"id": 1, "name": "سیمان", "unit": "کیسه", "price": 120000},
            {"id": 2, "name": "آجر", "unit": "عدد", "price": 2500},
            {"id": 3, "name": "شن", "unit": "متر مکعب", "price": 400000},
            {"id": 4, "name": "ماسه", "unit": "متر مکعب", "price": 350000},
            {"id": 5, "name": "تیرآهن", "unit": "کیلوگرم", "price": 45000},
            {"id": 6, "name": "سیمان سفید", "unit": "کیسه", "price": 180000}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
