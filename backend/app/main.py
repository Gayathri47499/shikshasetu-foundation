from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routes import (
    assistant,
    auth,
    dashboard,
    imports,
    interventions,
    notifications,
    planner,
    reports,
    risk,
    schools,
    students,
)
from app.seed import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shikshasetu")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ShikshaSetu Foundation database schema and assessment seed data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Student Success & Intervention Intelligence Platform (Veltris Vertical AI Academy Challenge A)",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(schools.router)
app.include_router(students.router)
app.include_router(risk.router)
app.include_router(interventions.router)
app.include_router(planner.router)
app.include_router(assistant.router)
app.include_router(reports.router)
app.include_router(imports.router)
app.include_router(notifications.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "subtitle": settings.APP_SUBTITLE,
        "environment": settings.ENVIRONMENT,
        "gemini_configured": bool(settings.GEMINI_API_KEY.strip()),
    }
