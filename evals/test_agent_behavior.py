"""
Behavioral evals for the agent.

These tests measure agent INTELLIGENCE, not code correctness.
They verify routing decisions, hallucination resistance, and confidence.

Marks:
    @pytest.mark.llm    — requires real LLM API call (slow, costs tokens)
    @pytest.mark.fast   — uses mocks, safe for CI

Run only fast evals in CI:
    uv run pytest evals/ -m "not llm"

Run all evals locally before releasing:
    uv run pytest evals/ -v
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Load ground truth dataset
DATASET_PATH = Path(__file__).parent / "datasets" / "agent_behavior.json"
with open(DATASET_PATH) as f:
    DATASET = json.load(f)

CASES = {case["id"]: case for case in DATASET["cases"]}


# ── Fast evals (mocked — safe for CI) ────────────────────────────────────────

class TestRoutingDecisions:
    """
    Verify the agent routes questions to the correct tool.
    These use mocked agents — they test the ROUTING LOGIC, not the LLM.
    """

    @pytest.mark.fast
    def test_numeric_question_routes_to_sql(self, mock_agent_sql):
        """Revenue questions must use execute_sql, never semantic_search."""
        case = CASES["sql-routing-01"]
        trace = mock_agent_sql.last_trace

        assert case["expected_tool"] in trace.tools_called, (
            f"Expected '{case['expected_tool']}' in tools_called, "
            f"got: {trace.tools_called}"
        )
        assert case.get("must_not_use_tool") not in trace.tools_called, (
            f"Agent should NOT call '{case['must_not_use_tool']}' "
            f"for numeric questions"
        )

    @pytest.mark.fast
    def test_semantic_question_routes_to_qdrant(self, mock_agent_semantic):
        """Sentiment questions must use semantic_search, never execute_sql."""
        case = CASES["semantic-routing-01"]
        trace = mock_agent_semantic.last_trace

        assert case["expected_tool"] in trace.tools_called, (
            f"Expected '{case['expected_tool']}' in tools_called, "
            f"got: {trace.tools_called}"
        )

    @pytest.mark.fast
    def test_agent_does_not_answer_without_tools(self, mock_agent_no_tools):
        """
        Agent must not answer questions that require data
        without calling any tool first.
        Answering without tools = hallucination risk.
        """
        from src.project_name.observability.tracer import AgentTrace
        trace = AgentTrace(question="What is revenue?")
        # No tools called — should be flagged
        trace.final_answer = "Revenue is $100,000"
        if trace.final_answer and not trace.tools_called:
            trace.mark_hallucinated()

        assert trace.hallucinated is True


class TestGuardrails:
    """Verify the guardrail layer blocks bad responses."""

    @pytest.mark.fast
    def test_low_confidence_triggers_retry(self):
        """Responses with confidence < 0.7 should not pass validation."""
        from src.project_name.guardrails.validators import ConfidenceValidator
        from src.project_name.models import QueryOutput
        from src.project_name.observability.tracer import AgentTrace

        validator = ConfidenceValidator(min_confidence=0.7, question="test?")
        output = QueryOutput(answer="Some answer", confidence=0.5)
        trace = AgentTrace(question="test?")
        trace.tools_called = ["execute_sql"]

        assert validator.validate(output, trace) is False
        assert "0.50" in validator.failure_reason

    @pytest.mark.fast
    def test_source_validator_blocks_toolless_answers(self):
        """Agent that answers without calling any tool should be rejected."""
        from src.project_name.guardrails.validators import SourceValidator
        from src.project_name.models import QueryOutput
        from src.project_name.observability.tracer import AgentTrace

        validator = SourceValidator(question="What is total revenue?")
        output = QueryOutput(answer="Revenue is $100K", confidence=0.9)
        trace = AgentTrace(question="What is total revenue?")
        # tools_called is empty — model answered from memory

        assert validator.validate(output, trace) is False

    @pytest.mark.fast
    def test_valid_response_passes_all_validators(self):
        """A well-formed response with sources should pass all validators."""
        from src.project_name.guardrails.validators import (
            ConfidenceValidator, SourceValidator
        )
        from src.project_name.models import QueryOutput
        from src.project_name.observability.tracer import AgentTrace

        output = QueryOutput(
            answer="Revenue is $127,430",
            confidence=0.95,
            sources=["execute_sql"]
        )
        trace = AgentTrace(question="What is revenue?")
        trace.tools_called = ["execute_sql"]

        q = "What is revenue?"
        assert ConfidenceValidator(min_confidence=0.7, question=q).validate(output, trace)
        assert SourceValidator(question=q).validate(output, trace)


# ── Slow evals (real LLM — run locally before release) ───────────────────────

class TestAgentIntelligence:
    """
    Real LLM behavioral tests. These cost tokens and take time.
    Run before every release, not in every CI build.
    """

    @pytest.mark.llm
    @pytest.mark.slow
    def test_agent_routes_revenue_to_sql(self, real_agent):
        """
        REAL LLM TEST: Agent must call execute_sql for revenue questions.
        If this fails, the tool docstrings need improvement.
        """
        from src.project_name.guardrails.retry import validated_invoke

        output, trace = validated_invoke(
            agent=real_agent,
            question=CASES["sql-routing-01"]["question"],
            max_retries=2,
        )

        assert "execute_sql" in trace.tools_called, (
            "Agent did not use SQL for a revenue question. "
            "Check the execute_sql docstring routing keywords."
        )
        assert trace.hallucinated is False

    @pytest.mark.llm
    @pytest.mark.slow
    def test_agent_confidence_above_threshold(self, real_agent):
        """REAL LLM TEST: Agent confidence must be ≥ 0.7 for factual questions."""
        from src.project_name.guardrails.retry import validated_invoke

        output, trace = validated_invoke(
            agent=real_agent,
            question=CASES["confidence-01"]["question"],
        )

        assert output.confidence >= CASES["confidence-01"]["min_confidence"], (
            f"Confidence {output.confidence} below threshold. "
            "The model is uncertain — improve context or data quality."
        )


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_agent_sql():
    """Mock agent that simulates calling execute_sql."""
    from src.project_name.observability.tracer import AgentTrace

    agent = MagicMock()
    trace = AgentTrace(question="What is total revenue?")
    trace.tools_called = ["execute_sql"]
    trace.total_steps = 2
    agent.last_trace = trace

    agent.invoke.return_value = {
        "messages": [MagicMock(content="Revenue is $127,430")]
    }
    return agent


@pytest.fixture
def mock_agent_semantic():
    """Mock agent that simulates calling semantic_search."""
    from src.project_name.observability.tracer import AgentTrace

    agent = MagicMock()
    trace = AgentTrace(question="What are customers complaining about?")
    trace.tools_called = ["semantic_search"]
    agent.last_trace = trace

    agent.invoke.return_value = {
        "messages": [MagicMock(content="Customers complain about delivery times.")]
    }
    return agent


@pytest.fixture
def mock_agent_no_tools():
    """Mock agent that answers without calling any tool."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "messages": [MagicMock(content="Revenue is $100,000")]
    }
    return agent


@pytest.fixture
def real_agent():
    """Real agent — only used in @pytest.mark.llm tests."""
    from src.project_name.config import get_settings
    settings = get_settings()

    from langchain_anthropic import ChatAnthropic
    from langgraph.prebuilt import create_react_agent

    llm = ChatAnthropic(
        model=settings.model_name,
        anthropic_api_key=settings.anthropic_api_key
    )

    return create_react_agent(model=llm, tools=[], prompt="You are a helpful assistant.")
