from fastapi import APIRouter

from app.services.analytics_service import get_analytics_stats


router = APIRouter()


@router.get("/api/analytics")
def analytics_stats():
    return get_analytics_stats()
