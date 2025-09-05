from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Settings
class Settings:
    PROJECT_NAME = "Metreyar API"
    VERSION = "1.0.0"
    SECRET_KEY = "your-secret-key-here-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

settings = Settings()

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserResponse(BaseModel):
    email: str
    full_name: str

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    total_area: Optional[float] = None
    total_cost: Optional[float] = None

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('metreyar.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        location TEXT,
        total_area REAL,
        total_cost REAL,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

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

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dilagh01.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://metreyar.onrender.com",
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
        "frontend": "https://dilagh01.github.io/metreyar_flutter_web/"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "metreyar-api"}

# Authentication endpoints
@app.post("/api/auth/register")
def register(user: UserCreate):
    conn = sqlite3.connect('metreyar.db')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user.password)
    cursor.execute(
        "INSERT INTO users (email, hashed_password, full_name) VALUES (?, ?, ?)",
        (user.email, hashed_password, user.full_name)
    )
    conn.commit()
    conn.close()
    
    return {"message": "User created successfully", "email": user.email}

@app.post("/api/auth/login")
def login(user: UserCreate):
    conn = sqlite3.connect('metreyar.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    db_user = cursor.fetchone()
    conn.close()
    
    if not db_user or not verify_password(user.password, db_user[2]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Project endpoints
@app.get("/api/projects")
def get_projects():
    conn = sqlite3.connect('metreyar.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": project[0],
            "name": project[1],
            "description": project[2],
            "location": project[3],
            "total_area": project[4],
            "total_cost": project[5],
            "status": project[6],
            "created_at": project[7]
        }
        for project in projects
    ]

@app.post("/api/projects")
def create_project(project: ProjectCreate):
    conn = sqlite3.connect('metreyar.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO projects (name, description, location, total_area, total_cost) VALUES (?, ?, ?, ?, ?)",
        (project.name, project.description, project.location, project.total_area, project.total_cost)
    )
    conn.commit()
    conn.close()
    
    return {"message": "Project created successfully", "name": project.name}

# Calculation endpoint
@app.post("/api/calculate/estimation")
def calculate_estimation(calculation_data: dict):
    try:
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
            {"id": 4, "name": "ماسه", "unit": "متر مکعب", "price": 350000}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
