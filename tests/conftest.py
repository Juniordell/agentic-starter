"""Shared pytest fixtures for all tests."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_agent():
    """Generic mock agent returning a high-confidence response."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "messages": [MagicMock(content="Revenue is $127K")]
    }
    return agent


@pytest.fixture
def sample_trace():
    """An AgentTrace with a successful tool call."""
    from src.project_name.observability.tracer import AgentTrace
    trace = AgentTrace(question="What is revenue?")
    trace.tools_called = ["execute_sql"]
    trace.total_steps = 2
    trace.confidence = 0.95
    return trace
