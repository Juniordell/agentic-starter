---
name: tdd
description: >
  Red-Green-Refactor cycle, pytest patterns, fixtures, coverage.
  Auto-activates when writing tests, setting up test infrastructure,
  or implementing new features that require TDD.
---

# TDD

## Core principle
Write the test first. The test defines the contract.
Code that exists without a failing test first was written backwards.

## Red-Green-Refactor
1. **Red** — write a test that fails for the right reason
2. **Green** — write the minimum code to make it pass
3. **Refactor** — clean up without breaking the test

## pytest patterns
```python
import pytest

class TestMyFeature:
    def test_happy_path(self):
        result = my_function("valid input")
        assert result.status == "ok"

    def test_raises_on_invalid(self):
        with pytest.raises(ValueError, match="must not be empty"):
            my_function("")

    @pytest.mark.parametrize("input,expected", [
        ("a", 1),
        ("ab", 2),
        ("abc", 3),
    ])
    def test_length(self, input, expected):
        assert len(input) == expected
```

## Fixtures
```python
@pytest.fixture
def mock_agent():
    from unittest.mock import MagicMock
    agent = MagicMock()
    agent.invoke.return_value = {"messages": [MagicMock(content="answer")]}
    return agent
```

## Markers
```python
@pytest.mark.fast    # mocked, safe for CI
@pytest.mark.llm     # real LLM call, slow, costs tokens
@pytest.mark.slow    # takes > 5 seconds
```

## Negative knowledge
- Do NOT mock the thing you're testing — mock its dependencies
- Do NOT write tests after the code — you'll write tests that pass, not tests that fail
- Do NOT assert on implementation details — assert on observable behavior
- Do NOT skip `conftest.py` — shared fixtures live there
