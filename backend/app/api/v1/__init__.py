from fastapi import APIRouter

from .analysis import router as analysis_router

api_router = APIRouter()
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
