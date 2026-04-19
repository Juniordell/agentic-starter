"""Core Pydantic models for structured agent outputs."""

from pydantic import BaseModel, Field
from typing import Annotated


class QueryOutput(BaseModel):
    """Structured output from an agent invocation."""
    answer: str = Field(..., description="The agent's answer")
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ..., description="Model confidence (0.0–1.0)"
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Tools or data sources used to produce the answer",
    )
