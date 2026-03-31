from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # ─────────────────────────────────────────────────────────────
    # Tavily
    # ─────────────────────────────────────────────────────────────
    TAVILY_API_KEY: Optional[str] = None

    # ─────────────────────────────────────────────────────────────
    # Gemini AI
    # ─────────────────────────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None  # ✅ FIX ADDED

    # ─────────────────────────────────────────────────────────────
    # CORS / Environment
    # ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "*"
    APP_ENV: str = "development"

    # ─────────────────────────────────────────────────────────────
    # Cache
    # ─────────────────────────────────────────────────────────────
    CACHE_TTL: int = 300
    CACHE_MAX: int = 256
    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_SIZE: int = 256
    MAX_ARTICLES_PER_QUERY: int = 40
    SCRAPING_TIMEOUT: int = 12
    SCRAPING_MAX_HTML_BYTES: int = 600_000
    SCRAPING_RATE_LIMIT_RPS: float = 1.5

    # ─────────────────────────────────────────────────────────────
    # JWT Auth
    # ─────────────────────────────────────────────────────────────
    JWT_SECRET: str = "marketiq-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # ─────────────────────────────────────────────────────────────
    # Google OAuth
    # ─────────────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # ─────────────────────────────────────────────────────────────
    # Email / SMTP
    # ─────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "MarketIQ <noreply@marketiq.app>"

    # ─────────────────────────────────────────────────────────────
    # Feature Flags (VERY USEFUL)
    # ─────────────────────────────────────────────────────────────
    ENABLE_AI: bool = True

    # ─────────────────────────────────────────────────────────────
    # Computed Properties
    # ─────────────────────────────────────────────────────────────
    @property
    def has_tavily(self) -> bool:
        return bool(self.TAVILY_API_KEY and self.TAVILY_API_KEY.strip().startswith("tvly-"))

    @property
    def has_email(self) -> bool:
        return bool(self.SMTP_USER and self.SMTP_PASSWORD)

    @property
    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())

    # ─────────────────────────────────────────────────────────────
    # Pydantic Config
    # ─────────────────────────────────────────────────────────────
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # ✅ Prevents crash if extra vars exist


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()