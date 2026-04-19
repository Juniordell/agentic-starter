"""Unit tests for observability module."""

import pytest
import time
from src.project_name.observability.tracer import AgentTracer, AgentTrace, AgentStep


class TestAgentTrace:
    def test_initial_state(self):
        trace = AgentTrace(question="test?")
        assert trace.tools_called == []
        assert trace.total_steps == 0
        assert trace.hallucinated is False
        assert trace.error is None

    def test_mark_hallucinated(self):
        trace = AgentTrace(question="test?")
        trace.mark_hallucinated()
        assert trace.hallucinated is True

    def test_to_dict(self):
        trace = AgentTrace(question="test?")
        trace.tools_called = ["execute_sql"]
        trace.total_steps = 2
        trace.confidence = 0.9

        d = trace.to_dict()
        assert d["question"] == "test?"
        assert d["tools_called"] == ["execute_sql"]
        assert d["total_steps"] == 2
        assert d["confidence"] == 0.9
        assert d["hallucinated"] is False


class TestAgentTracer:
    def test_context_manager_sets_latency(self):
        with AgentTracer(question="test?") as tracer:
            time.sleep(0.01)  # simulate work

        assert tracer.trace.latency_ms >= 10  # at least 10ms

    def test_records_tool_calls(self):
        with AgentTracer(question="test?") as tracer:
            tracer.record_tool_call(
                tool_name="execute_sql",
                tool_input={"keyword": "revenue"},
                tool_output="[{'revenue': 1000}]",
                latency_ms=150.0
            )

        assert "execute_sql" in tracer.trace.tools_called
        assert tracer.trace.total_steps == 1
        assert tracer.trace.steps[0].tool_called == "execute_sql"

    def test_detects_hallucination(self):
        """If agent answers without calling any tool, mark as hallucinated."""
        with AgentTracer(question="What is revenue?") as tracer:
            tracer.set_output("Revenue is $100K", confidence=0.9)
            # No tool calls recorded

        assert tracer.trace.hallucinated is True

    def test_no_hallucination_when_tool_called(self):
        with AgentTracer(question="What is revenue?") as tracer:
            tracer.record_tool_call("execute_sql", {}, "result", 100.0)
            tracer.set_output("Revenue is $127K", confidence=0.95)

        assert tracer.trace.hallucinated is False

    def test_captures_exception(self):
        with pytest.raises(ValueError):
            with AgentTracer(question="test?") as tracer:
                raise ValueError("something went wrong")

        assert tracer.trace.error == "something went wrong"
