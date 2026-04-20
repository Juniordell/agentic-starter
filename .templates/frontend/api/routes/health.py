"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Return API health status. Frontend uses this to show connection state."""
    return {"status": "ok", "version": "0.1.0"}
