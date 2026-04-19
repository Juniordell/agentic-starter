# agentic-starter

> Open source Claude Code template focused on reducing hallucination
> and optimizing token usage through guardrails, observability, and SDD.

## Quick Start

```bash
git clone https://github.com/Juniordell/agentic-starter my-project
cd my-project

python bootstrap.py --name "My Project" --author "Your Name"
# or with vector DB:
python bootstrap.py --name "My Project" --author "Your Name" --with-vector-db
```

## What makes this different

Most Claude Code templates are about structure. This one is about **precision**.

| Problem | Solution |
|---------|----------|
| Model hallucinates data | Guardrails reject answers without sources |
| Model routes to wrong tool | Explicit docstring routing + ToolRoutingValidator |
| Can't measure agent quality | AgentTracer records every step and tool call |
| Tests don't cover agent intelligence | Evals test routing, hallucination, confidence |
| Context gets bloated | Skills load on-demand, CLAUDE.md ≤ 100 lines |
| Broken AI commits slip through | GitHub Actions CI blocks them |

## Optional Modules

| Flag | Status | Adds |
|------|--------|------|
| `--with-vector-db` | ✅ Stable | Qdrant + Postgres + dual-store skills |
| `--with-frontend` | 🚧 v0.2 | Next.js + API route |
| `--with-multi-agent` | 🚧 v0.2 | CrewAI + LangFuse |

## SDD — 5 Phases

```
/brainstorm → Phase 1: Discovery            (Opus)
/define     → Phase 2: Requirements         (Opus)   Clarity Score ≥ 12/15
/design     → Phase 3: Architecture         (Opus)
/build      → Phase 4: TDD via subagents    (Sonnet)
/ship       → Phase 5: Verify + archive     (Sonnet)
```

## Running tests

```bash
uv run pytest tests/ --tb=short          # unit tests
uv run pytest evals/ -m fast             # fast behavioral evals (mocked)
uv run pytest evals/ -m llm              # real LLM evals (costs tokens)
```

## Requirements
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [Claude Code](https://claude.ai/code)
- Docker (with `--with-vector-db`)

## License
MIT
