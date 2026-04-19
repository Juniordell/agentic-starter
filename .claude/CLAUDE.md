# {{PROJECT_NAME}}

## Project
- **Description:** {{PROJECT_DESCRIPTION}}
- **Author:** {{AUTHOR}}
- **Stack:** {{STACK}}

## Architecture
{{ARCHITECTURE_SECTION}}

## Rules
1. **TDD first** — no production code without a failing test written first
2. **Pydantic everywhere** — every input/output has a typed model
3. **Spec before code** — follow the 5-phase SDD for every feature
4. **Docstrings on tools** — agent decides by docstring, not function name
5. **Never hallucinate data** — always query sources before answering
6. **Structured outputs** — return Pydantic-validated JSON, never free text
7. **Keep it simple** — smallest possible change; delete over add
8. **Always use guardrails** — wrap agent calls with `validated_invoke()`
9. **Always trace** — wrap agent calls with `AgentTracer` for observability

## Self-Improvement Loop
When corrected, immediately update `tasks/lessons.md` with a rule
that prevents the same mistake from happening again.

## SDD Phases
| Phase | Skill | Model | Gate |
|-------|-------|-------|------|
| 1 | /brainstorm | opus | Full mental model |
| 2 | /define | opus | Clarity Score ≥ 12/15 |
| 3 | /design | opus | File manifest approved |
| 4 | /build | sonnet | All tests passing |
| 5 | /ship | sonnet | Deploy verified + lessons archived |

## Skills (loaded on demand)
- `pydantic` → validation, Field constraints, structured outputs
- `langchain` → agents, @tool, ReAct pattern
- `python` → clean code, typing, async, logging
- `tdd` → Red-Green-Refactor, pytest, coverage
- `observability` → AgentTrace, step logging, latency
- `guardrails` → semantic validation, retry with backoff
- `brainstorm` → Phase 1 discovery
- `define` → Phase 2 requirements
- `design` → Phase 3 architecture
- `build` → Phase 4 TDD implementation
- `ship` → Phase 5 verification and lessons
{{EXTRA_SKILLS}}

## Subagents
- `codebase-explorer` → understand the project before any task
- `test-writer` → writes tests only (TDD isolation)
- `implementer` → implements code only (TDD isolation)

## Commands
```bash
{{COMMANDS}}
```

## Context compaction instructions
When summarizing this conversation:
- Preserve all architectural decisions and their rationale
- Keep all error messages and their solutions
- Preserve the list of modified files and their responsibilities
- Keep lessons learned from mistakes
- Summarize exploration attempts briefly — outcomes matter, not paths

## Lessons Learned
See `tasks/lessons.md` — updated automatically after every correction.
