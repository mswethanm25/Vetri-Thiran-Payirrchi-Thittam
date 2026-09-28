from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import init_db
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    init_db()
    yield


app = FastAPI(
    title="FitBuddy - AI Fitness Plan Generator",
    description="AI-powered 7-day workout plan and nutrition tip generator using Gemini models.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routes
app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "FitBuddy"}