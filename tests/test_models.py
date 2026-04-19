"""Unit tests for core Pydantic models."""

import pytest
from pydantic import ValidationError
from src.project_name.models import QueryOutput


class TestQueryOutput:
    def test_valid_output(self):
        output = QueryOutput(answer="Revenue is $127K", confidence=0.95)
        assert output.answer == "Revenue is $127K"
        assert output.confidence == 0.95
        assert output.sources == []

    def test_with_sources(self):
        output = QueryOutput(
            answer="Result", confidence=0.8, sources=["execute_sql"]
        )
        assert "execute_sql" in output.sources

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            QueryOutput(answer="A", confidence=-0.1)

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            QueryOutput(answer="A", confidence=1.1)

    def test_confidence_boundary_values(self):
        low = QueryOutput(answer="A", confidence=0.0)
        high = QueryOutput(answer="A", confidence=1.0)
        assert low.confidence == 0.0
        assert high.confidence == 1.0

    def test_empty_answer_allowed(self):
        output = QueryOutput(answer="", confidence=0.0)
        assert output.answer == ""
