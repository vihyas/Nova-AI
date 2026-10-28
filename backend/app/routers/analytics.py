from fastapi import APIRouter
from backend.app.models.schemas import ProductivityMetrics
from backend.app.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/productivity", response_model=ProductivityMetrics)
def get_productivity():
    return analytics_service.get_productivity_metrics()

@router.get("/benchmarks")
def get_system_benchmarks():
    return analytics_service.get_system_benchmarks()

