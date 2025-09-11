from sqlalchemy.orm import Session
from app.models.project import Project
from app.schemas.project import ProjectCreate

class ProjectService:
    @staticmethod
    def get_all_projects(db: Session):
        return db.query(Project).all()

    @staticmethod
    def create_project(db: Session, project: ProjectCreate):
        db_project = Project(
            name=project.name,
            description=project.description,
            location=project.location,
            total_area=project.total_area,
            total_cost=0.0  # مقدار پیش‌فرض
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def get_project_by_id(db: Session, project_id: int):
        return db.query(Project).filter(Project.id == project_id).first()
