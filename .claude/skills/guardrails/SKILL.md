---
name: guardrails
description: >
  Semantic validation, automatic retry with backoff, and hallucination
  detection. Auto-activates when implementing agent calls, adding
  validation to outputs, or handling agent errors.
---

# Guardrails

## Core principle
Schema validation (Pydantic) ensures correct structure.
Semantic validation ensures correct content.
Both are required. Neither alone is sufficient.

## Three validation levels
1. **Schema** (Pydantic) — field types, constraints, required fields
2. **Semantic** — did the model actually query a source before answering?
3. **Behavioral** — did the model take the right path to get here?

## Using validated_invoke
```python
from src.project_name.guardrails.retry import validated_invoke

# Instead of calling agent directly:
result = agent.invoke({"messages": [("user", question)]})

# Always use:
result = validated_invoke(
    agent=agent,
    question=question,
    max_retries=3
)
```

## Writing a semantic validator
```python
from src.project_name.guardrails.validators import SemanticValidator

class RevenueValidator(SemanticValidator):
    def validate(self, output: QueryOutput, trace: AgentTrace) -> bool:
        # Revenue questions must use SQL
        if "revenue" in self.question.lower():
            return "execute_sql" in trace.tools_called
        return True
```

## When guardrails trigger a retry
- `confidence < 0.7` — model is uncertain
- `sources == []` — model answered without citing a source
- Semantic rule violated — model used wrong tool for the question
- Exception during tool execution — transient failure

## Negative knowledge
- Do NOT retry infinitely — always set max_retries
- Do NOT swallow GuardrailError silently — log and surface it
- Do NOT write validators that are too strict — they cause false retries
- Do NOT validate inside the agent loop — validate the final output only
