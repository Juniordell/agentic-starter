---
name: pydantic
description: >
  Pydantic v2 validation, Field constraints, structured outputs, and
  model composition. Auto-activates when defining data models, validating
  inputs/outputs, or using instructor for structured LLM responses.
---

# Pydantic

## Core principle
Every input and output in the system must be typed.
Free-form dicts cause silent bugs. Pydantic turns them into loud errors.

## Defining models
```python
from pydantic import BaseModel, Field
from typing import Annotated

class QueryOutput(BaseModel):
    answer: str = Field(..., min_length=1)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    sources: list[str] = Field(default_factory=list)
```

## Settings with pydantic-settings
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    model_name: str = "claude-sonnet-4-6"

    model_config = {"env_file": ".env"}
```

## Structured outputs with instructor
```python
import instructor
from anthropic import Anthropic

client = instructor.from_anthropic(Anthropic())

result = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    response_model=QueryOutput,
    messages=[{"role": "user", "content": question}],
)
# result is a validated QueryOutput instance
```

## Negative knowledge
- Do NOT use `model.dict()` — use `model.model_dump()` in Pydantic v2
- Do NOT use `Optional[X]` — use `X | None` in Python 3.11+
- Do NOT skip `Field(...)` for required fields — be explicit
- Do NOT validate inside the agent loop — validate the final output only
