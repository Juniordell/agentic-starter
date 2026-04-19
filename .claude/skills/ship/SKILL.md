---
name: ship
description: >
  Phase 5 of SDD: verification, deployment check, and lessons archival.
  Auto-activates when invoked via /ship or completing implementation.
---

# Ship — Phase 5

## Core principle
Done means deployed and verified. Not "tests pass locally."
Phase 5 ends with lessons archived and the next iteration seeded.

## Checklist
- [ ] All tests pass (`uv run pytest`)
- [ ] Ruff clean (`uv run ruff check src/`)
- [ ] Mypy clean (`uv run mypy src/`)
- [ ] Coverage ≥ 80% (`uv run pytest --cov=src --cov-fail-under=80`)
- [ ] CI passing on GitHub Actions
- [ ] No secrets committed (check `.env` is gitignored)
- [ ] `tasks/lessons.md` updated with anything learned

## Archiving lessons
After every completed feature, add to `tasks/lessons.md`:
```markdown
## [Date] — [Feature name]
- What went wrong: [description]
- Rule to prevent it: [the rule]
```

## Seeding next iteration
End Phase 5 by proposing the next `/brainstorm` topic if known.

## Negative knowledge
- Do NOT skip the lessons archive — it feeds future sessions
- Do NOT ship with known test failures
- Do NOT consider CI optional — it's the final gate
