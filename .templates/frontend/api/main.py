"""
FastAPI app — bridge between the Python agent and any frontend.

Set app.state.agent during lifespan to enable the /chat endpoint.

Usage:
    uv run uvicorn src.project_name.api.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.project_name.api.routes.chat import router as chat_router
from src.project_name.api.routes.health import router as health_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure your agent here before the server accepts requests.
    # Example:
    #   from src.project_name.agent import build_agent
    #   app.state.agent = build_agent()
    app.state.agent = None
    logger.info("API started — set app.state.agent in lifespan to enable /chat")
    yield
    logger.info("API shutting down")


app = FastAPI(
    title="{{PROJECT_NAME}} API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # never use ["*"]
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(health_router)
