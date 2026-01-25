from fastapi import APIRouter
from api.services.performance_service import PerformanceService

router = APIRouter(prefix="/performance", tags=["Performance"])
service = PerformanceService()

@router.get("/summary")
def get_performance_summary():
    return service.get_performance_summary()
