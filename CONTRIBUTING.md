# Contributing to agentic-starter

## Ways to contribute
- Add a Skill — improve agent domain knowledge
- Propose a new flag — new optional module
- Improve guardrails — new semantic validators
- Add evals — expand the behavioral test dataset
- Fix bugs in bootstrap.py or existing files

## How to add a new Skill
1. Create `.claude/skills/<name>/SKILL.md`
2. Add frontmatter with `name`, `description`, and optionally `model`
3. Include: core principle, code examples, negative knowledge section
4. Keep it under 150 lines
5. PR title: `skill: add <name> skill`

## How to add a new eval case
1. Add an entry to `evals/datasets/agent_behavior.json`
2. Add a corresponding test in `evals/test_agent_behavior.py`
3. Mark with `@pytest.mark.fast` (mocked) or `@pytest.mark.llm` (real API)
4. PR title: `eval: add <description> case`

## How to add a semantic validator
1. Create a class in `src/project_name/guardrails/validators.py`
2. Extend `SemanticValidator`, implement `validate()`
3. Add tests in `tests/test_guardrails.py`
4. PR title: `guardrail: add <name> validator`

## How to propose a new flag
1. Create `.templates/<module-name>/` with all module files
2. Add manifest in `bootstrap.py`
3. Add flag to argparse
4. Update `pyproject.toml` optional deps
5. Mark as `🚧 Coming soon` until tests complete
6. PR title: `feat: add --with-<name> flag`

## Testing locally
```bash
git clone https://github.com/Juniordell/agentic-starter test-run
cd test-run
python bootstrap.py --name "Test" --author "Test Author"
uv run pytest tests/ evals/ -m "not llm" --tb=short
# All tests should pass
```

## Pull Request checklist
- [ ] `uv run pytest tests/ evals/ -m "not llm"` passes
- [ ] `uv run ruff check src/` passes
- [ ] New skills have a "Negative knowledge" section
- [ ] New validators have tests in `test_guardrails.py`
- [ ] New eval cases have both a dataset entry and a test function
- [ ] `uv.lock` is committed if deps changed

## Commit style
`feat:`, `fix:`, `docs:`, `skill:`, `eval:`, `guardrail:`
