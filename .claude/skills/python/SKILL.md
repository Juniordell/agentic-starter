---
name: python
description: >
  Clean Python patterns: typing, async, logging, dataclasses, pathlib.
  Auto-activates when writing Python utility code, async functions,
  or setting up structured logging.
---

# Python

## Core principle
Explicit over implicit. Types everywhere. No magic.

## Typing patterns
```python
from typing import Any
from collections.abc import Sequence

def process(items: Sequence[str], config: dict[str, Any]) -> list[str]:
    return [item.strip() for item in items if item]
```

## Structured logging
```python
import logging

logger = logging.getLogger(__name__)

# Always pass extra= dict for structured log fields
logger.info("Agent invoked", extra={"question": question, "attempt": attempt})
logger.warning("Validation failed", extra={"reason": reason, "tool": tool_name})
```

## Async patterns
```python
import asyncio
from typing import Any

async def fetch_all(queries: list[str]) -> list[Any]:
    tasks = [fetch_one(q) for q in queries]
    return await asyncio.gather(*tasks)
```

## Dataclasses vs Pydantic
- Use `@dataclass` for internal data that doesn't cross API boundaries
- Use `BaseModel` for anything validated from external input or LLM output

## Negative knowledge
- Do NOT use `print()` for logging — use `logging`
- Do NOT use mutable default args `def f(items=[])` — use `None` + guard
- Do NOT catch bare `except:` — always specify the exception type
- Do NOT use `os.path` — use `pathlib.Path`
