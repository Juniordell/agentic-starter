"""
Behavioral evals for agent intelligence.

These tests verify HOW the agent reasons, not just WHAT it returns.
They are intentionally kept separate from unit tests because:
- They may call the real LLM API (use sparingly in CI)
- They test behavior, not implementation
- They should be run before releasing a new prompt or skill version

Run with:
    uv run pytest evals/ -v --tb=short
    uv run pytest evals/ -v -m "not llm"  # skip real LLM calls
"""
