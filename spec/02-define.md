# Phase 2 — Define

> Use `/define` to start this phase.

## Clarity Score: __/15

| Dimension | Score (0-3) | Notes |
|-----------|-------------|-------|
| Problem clarity | | |
| User clarity | | |
| Scope clarity | | |
| Data clarity | | |
| Success clarity | | |

## Functional Requirements

- FR-01: [System shall X when Y]
- FR-02: [System shall X when Y]
- FR-03: [System shall X when Y]

## Non-Functional Requirements

- NFR-01: Response time < 2s for 95th percentile
- NFR-02: Zero PII logged
- NFR-03: Test coverage ≥ 80%

## Data Models

```python
# Input model
class Input(BaseModel):
    ...

# Output model
class Output(BaseModel):
    ...
```

## API Contracts

```
POST /api/endpoint
Request:  { "field": "value" }
Response: { "result": "value", "confidence": 0.95 }
```

## Acceptance Criteria

- FR-01: Given [context], when [action], then [outcome]
- FR-02: Given [context], when [action], then [outcome]

---

**Gate:** Clarity Score ≥ 12/15 → proceed to `/design`
