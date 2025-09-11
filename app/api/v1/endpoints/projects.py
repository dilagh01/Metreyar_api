from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session  # اضافه کردن
from typing import List
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService
from app.core.database import get_db  # اضافه کردن

router = APIRouter()

@router.get("/projects", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):  # اضافه کردن db
    """Get all projects for Flutter frontend"""
    try:
        projects = ProjectService.get_all_projects(db)  # اضافه کردن db
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create new project from Flutter"""
    try:
        return ProjectService.create_project(db, project)  # اضافه کردن db
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get specific project"""
    try:
        project = ProjectService.get_project_by_id(db, project_id)  # اضافه کردن db
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
