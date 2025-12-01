from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db import init_db
from app.core.logging import setup_logging, get_logger
from app.routes.routes import router

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting application")
    await init_db()
    yield
    logger.info("Shutting down application")

app = FastAPI(title="RFP Agentic System", lifespan=lifespan)
app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to RFP Agentic System"}
