from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env."""

    APP_NAME: str = "ShikshaSetu Foundation"
    APP_SUBTITLE: str = "Student Success & Intervention Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./shikshasetu.db"

    # Auth / JWT
    JWT_SECRET: str = "shikshasetu-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Gemini LLM (Backend-only)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # Optional Supabase integration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = "https://shikshasetu-foundation.vercel.app"

    # Case study operational constraints (Dataset A3)
    OUTREACH_WORKERS_COUNT: int = 5
    MAX_VISITS_PER_WORKER_PER_DAY: int = 4
    WORKING_DAYS_PER_WEEK: int = 5
    MAX_WEEKLY_VISITS: int = 100
    WEEKLY_BUDGET_INR: float = 25000.0
    AVERAGE_VISIT_COST_INR: float = 250.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def normalized_database_url(self) -> str:
        url = self.DATABASE_URL.strip()
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql://") and "+psycopg" not in url and "+psycopg2" not in url:
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
