---
name: define
description: >
  Phase 2 of SDD: requirements, Clarity Score, acceptance criteria.
  Auto-activates when invoked via /define or transitioning from brainstorm
  to formal requirements.
---

# Define — Phase 2

## Core principle
Requirements are contracts. Ambiguous requirements produce wrong software.
Phase 2 ends when every requirement is testable and unambiguous.

## Clarity Score (gate: ≥ 12/15)
Rate each dimension 0–3:
1. **Problem clarity** — is the problem completely understood?
2. **User clarity** — do we know exactly who uses this and how?
3. **Scope clarity** — is the boundary between in/out explicit?
4. **Data clarity** — do we know all inputs, outputs, and data shapes?
5. **Success clarity** — can we measure when we're done?

## Outputs
- Functional requirements (numbered, testable)
- Non-functional requirements (latency, reliability, security)
- Data models (field names, types, constraints)
- API contracts (request/response shapes)
- Acceptance criteria for each requirement

## Template
```markdown
## Requirements

### Functional
- FR-01: [System shall X when Y]
- FR-02: [System shall X when Y]

### Non-functional
- NFR-01: Response time < 2s for 95th percentile
- NFR-02: Zero PII logged

### Data models
[Pydantic model sketches]

### Acceptance criteria
- FR-01: Given [context], when [action], then [outcome]
```

## Gate
Clarity Score ≥ 12/15. Do NOT proceed to Phase 3 without this.
