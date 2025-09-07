from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

# ---------- مدل‌ها برای Pydantic ----------
class PriceItem(BaseModel):
    id: Optional[int]
    code: str
    name: str
    unit: str
    unit_price: float

class BOQRow(BaseModel):
    id: Optional[int]
    price_item_id: int
    description: str
    unit: str
    quantity: float
    unit_price: float
    total_price: Optional[float] = 0

class BOQRequest(BaseModel):
    project_id: int
    boq: List[BOQRow]

class BOQResponse(BaseModel):
    project_id: int
    total_cost: float
    boq: List[BOQRow]

class AnalysisComponent(BaseModel):
    id: Optional[int]
    boq_item_id: int
    description: str
    unit: str
    quantity: float
    unit_price: float
    total_price: Optional[float] = 0

class AnalysisRequest(BaseModel):
    boq_item_id: int
    components: List[AnalysisComponent]

class AnalysisResponse(BaseModel):
    boq_item_id: int
    total_cost: float
    components: List[AnalysisComponent]

# ---------- اپلیکیشن ----------
app = FastAPI(title="Metreyar API", version="2.0.0")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # یا لیست فرانت‌های مجاز
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- دیتابیس ----------
DB_FILE = "metreyar.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        name TEXT NOT NULL,
        unit TEXT NOT NULL,
        unit_price REAL NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS boq_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        price_item_id INTEGER,
        description TEXT,
        unit TEXT,
        quantity REAL,
        unit_price REAL,
        total_price REAL,
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        boq_item_id INTEGER,
        description TEXT,
        unit TEXT,
        quantity REAL,
        unit_price REAL,
        total_price REAL,
        FOREIGN KEY(boq_item_id) REFERENCES boq_items(id)
    )""")

    conn.commit()
    conn.close()

init_db()

# ---------- توابع کمکی ----------
def calculate_total(rows):
    total = 0
    for row in rows:
        row.total_price = row.quantity * row.unit_price
        total += row.total_price
    return total

# ---------- روت‌ها ----------

@app.get("/")
def root():
    return {"message": "Metreyar API is running 🚀"}

# BOQ محاسبه
@app.post("/api/boq/calculate", response_model=BOQResponse)
def calculate_boq(data: BOQRequest):
    total = calculate_total(data.boq)
    return BOQResponse(project_id=data.project_id, total_cost=total, boq=data.boq)

# Analysis محاسبه
@app.post("/api/analysis/calculate", response_model=AnalysisResponse)
def calculate_analysis(data: AnalysisRequest):
    total = calculate_total(data.components)
    return AnalysisResponse(boq_item_id=data.boq_item_id, total_cost=total, components=data.components)

# لیست مصالح
@app.get("/api/materials")
def get_materials():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, code, name, unit, unit_price FROM price_items")
    items = cursor.fetchall()
    conn.close()
    return [
        {"id": i[0], "code": i[1], "name": i[2], "unit": i[3], "unit_price": i[4]}
        for i in items
    ]
