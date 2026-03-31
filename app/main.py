import os
from dotenv import load_dotenv

load_dotenv()  # 🔥 REQUIRED

import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes.health       import router as health_router
from app.routes.analysis     import router as analysis_router
from app.routes.auth         import router as auth_router
from app.routes.notifications import router as notifications_router
from app.routes.domain_matrix import router as domain_matrix_router
from app.routes.gemini_insights import router as gemini_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MarketIQ API v4",
    description="Real-time market intelligence with AI insights.",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(analysis_router)
app.include_router(auth_router)
app.include_router(notifications_router)
app.include_router(domain_matrix_router)
app.include_router(gemini_router)


@app.on_event("startup")
async def startup():
    gemini = "✓" if os.environ.get("GEMINI_API_KEY") else "✗ (add GEMINI_API_KEY for AI insights)"
    logger.info(
        f"MarketIQ API v4.0.0 — "
        f"Tavily: {'✓' if settings.has_tavily else '✗'} | "
        f"Email: {'✓' if settings.has_email else '✗'} | "
        f"Gemini: {gemini}"
    )