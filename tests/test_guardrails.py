"""Unit tests for guardrails module."""

import pytest
from unittest.mock import MagicMock
from src.test_project.models import QueryOutput
from src.test_project.observability.tracer import AgentTrace
from src.test_project.guardrails.validators import (
    ConfidenceValidator,
    SourceValidator,
    ToolRoutingValidator,
)
from src.test_project.guardrails.retry import GuardrailError, validated_invoke


class TestConfidenceValidator:
    def test_passes_above_threshold(self):
        v = ConfidenceValidator(min_confidence=0.7, question="q?")
        output = QueryOutput(answer="A", confidence=0.9)
        trace = AgentTrace(question="q?")
        trace.tools_called = ["execute_sql"]
        assert v.validate(output, trace) is True

    def test_fails_below_threshold(self):
        v = ConfidenceValidator(min_confidence=0.7, question="q?")
        output = QueryOutput(answer="A", confidence=0.5)
        trace = AgentTrace(question="q?")
        trace.tools_called = ["execute_sql"]
        assert v.validate(output, trace) is False
        assert "0.50" in v.failure_reason

    def test_fails_at_exact_threshold(self):
        v = ConfidenceValidator(min_confidence=0.7, question="q?")
        output = QueryOutput(answer="A", confidence=0.7)
        trace = AgentTrace(question="q?")
        trace.tools_called = ["execute_sql"]
        # 0.7 is not below 0.7 — should pass
        assert v.validate(output, trace) is True


class TestSourceValidator:
    def test_passes_with_tools_called(self):
        v = SourceValidator(question="q?")
        output = QueryOutput(answer="A", confidence=0.9)
        trace = AgentTrace(question="q?")
        trace.tools_called = ["execute_sql"]
        assert v.validate(output, trace) is True

    def test_fails_without_tools(self):
        v = SourceValidator(question="q?")
        output = QueryOutput(answer="A", confidence=0.9)
        trace = AgentTrace(question="q?")
        # tools_called is empty
        assert v.validate(output, trace) is False

    def test_passes_with_empty_answer(self):
        """Empty answer with no tools is not a hallucination — it's a non-answer."""
        v = SourceValidator(question="q?")
        output = QueryOutput(answer="", confidence=0.0)
        trace = AgentTrace(question="q?")
        assert v.validate(output, trace) is True


class TestToolRoutingValidator:
    def test_passes_correct_tool(self):
        v = ToolRoutingValidator(
            question="What is total revenue?",
            expected_tool="execute_sql",
            trigger_keywords=["revenue", "total"]
        )
        output = QueryOutput(answer="A", confidence=0.9)
        trace = AgentTrace(question="What is total revenue?")
        trace.tools_called = ["execute_sql"]
        assert v.validate(output, trace) is True

    def test_fails_wrong_tool(self):
        v = ToolRoutingValidator(
            question="What is total revenue?",
            expected_tool="execute_sql",
            trigger_keywords=["revenue", "total"]
        )
        output = QueryOutput(answer="A", confidence=0.9)
        trace = AgentTrace(question="What is total revenue?")
        trace.tools_called = ["semantic_search"]  # wrong tool
        assert v.validate(output, trace) is False

    def test_passes_when_keyword_absent(self):
        """If keyword not in question, validator should not trigger."""
        v = ToolRoutingValidator(
            question="What are customer complaints?",
            expected_tool="execute_sql",
            trigger_keywords=["revenue", "total"]
        )
        output = QueryOutput(answer="A", confidence=0.9)
        trace = AgentTrace(question="What are customer complaints?")
        trace.tools_called = ["semantic_search"]
        assert v.validate(output, trace) is True


class TestValidatedInvoke:
    def test_returns_output_and_trace_on_success(self, mock_valid_agent):
        output, trace = validated_invoke(
            agent=mock_valid_agent,
            question="What is revenue?",
            validators=[ConfidenceValidator(min_confidence=0.7, question="What is revenue?")],
            confidence_fn=lambda q, a: 0.9,
            max_retries=1,
        )
        assert output.answer == "Revenue is $127K"
        assert isinstance(trace, AgentTrace)

    def test_confidence_fn_result_is_used(self, mock_valid_agent):
        """confidence_fn return value must appear in the output — not hardcoded 0.9."""
        output, trace = validated_invoke(
            agent=mock_valid_agent,
            question="What is revenue?",
            validators=[ConfidenceValidator(min_confidence=0.7, question="What is revenue?")],
            confidence_fn=lambda q, a: 0.82,
            max_retries=1,
        )
        assert output.confidence == pytest.approx(0.82)

    def test_raises_guardrail_error_after_max_retries(self, mock_failing_agent):
        with pytest.raises(GuardrailError) as exc_info:
            validated_invoke(
                agent=mock_failing_agent,
                question="What is revenue?",
                confidence_fn=lambda q, a: 0.9,
                max_retries=2,
                backoff_base=0.01,  # tiny backoff for fast tests
            )
        assert exc_info.value.attempts == 2


@pytest.fixture
def mock_valid_agent():
    """Agent that returns a high-confidence response with tools called."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "messages": [MagicMock(content="Revenue is $127K")]
    }
    return agent


@pytest.fixture
def mock_failing_agent():
    """Agent that always returns low-confidence responses."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "messages": [MagicMock(content="I'm not sure")]
    }
    return agent
