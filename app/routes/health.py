from fastapi import APIRouter
from app.config import settings
import sys

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "python": sys.version.split()[0],
        "tavily_configured": settings.has_tavily,
        "data_policy": "100% real data — no dummy content",
    }


@router.get("/")
async def root():
    return {
        "name": "MarketIQ Backend",
        "version": "2.0.0",
        "tavily_configured": settings.has_tavily,
        "endpoints": ["/health", "/analyze?company=Apple&days=7", "/docs"],
        "data_policy": "This API returns only real news data. No fabricated content.",
    }
