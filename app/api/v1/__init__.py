from fastapi import APIRouter
from .endpoints import auth, projects, items, calculations

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(items.router, prefix="/items", tags=["items"])
router.include_router(calculations.router, prefix="/calculations", tags=["calculations"])
