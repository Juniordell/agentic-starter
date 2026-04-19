---
name: observability
description: >
  AgentTrace model, step logging, latency tracking. Auto-activates when
  implementing agent calls, debugging agent behavior, or adding tracing
  to existing agent code.
---

# Observability

## Core principle
You cannot improve what you cannot measure.
Every agent invocation should produce a trace — what happened,
how long it took, which tools were called, and where it failed.

## AgentTrace — the data model
```python
from src.project_name.observability.tracer import AgentTracer

with AgentTracer(question="What is total revenue?") as tracer:
    result = agent.invoke({"messages": [("user", question)]})
    tracer.set_output(result)

# Access the trace
print(tracer.trace.tools_called)   # ["execute_sql"]
print(tracer.trace.total_steps)    # 2
print(tracer.trace.latency_ms)     # 1240.5
print(tracer.trace.hallucinated)   # False
```

## What to trace
- `tools_called` — which tools were invoked, in order
- `total_steps` — how many ReAct cycles the agent used
- `latency_ms` — total wall time for the invocation
- `hallucinated` — True if the agent answered without querying a source
- `confidence` — from the structured output

## What the trace enables
- Detect when the model routes to the wrong tool
- Spot runaway loops (total_steps > threshold)
- Measure latency regression between versions
- Identify which questions cause hallucination

## Negative knowledge
- Do NOT log raw prompts in production — they may contain PII
- Do NOT block the agent loop with synchronous trace writes
- Do NOT use print() for tracing — use structured logging
