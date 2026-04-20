"""Pydantic request/response models for the API layer."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class TraceEvent(BaseModel):
    tools_called: list[str]
    total_steps: int
    latency_ms: float
    hallucinated: bool
    confidence: float | None
