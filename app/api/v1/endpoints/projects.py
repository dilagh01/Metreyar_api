from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter()

@router.get("/projects", response_model=List[ProjectResponse])
def get_projects():
    """Get all projects for Flutter frontend"""
    try:
        projects = ProjectService.get_all_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate):
    """Create new project from Flutter"""
    try:
        return ProjectService.create_project(project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    """Get specific project"""
    try:
        project = ProjectService.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
