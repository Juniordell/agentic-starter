"""Unit tests for FastAPI API module."""

import json
import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport

from src.project_name.api.main import app
from src.project_name.observability.tracer import AgentTrace
from src.project_name.models import QueryOutput
from src.project_name.guardrails.retry import GuardrailError


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_output_and_trace(answer: str = "Revenue is $127K") -> tuple[QueryOutput, AgentTrace]:
    output = QueryOutput(answer=answer, confidence=0.95, sources=["execute_sql"])
    trace = AgentTrace(question="test?")
    trace.tools_called = ["execute_sql"]
    trace.total_steps = 1
    trace.latency_ms = 120.0
    return output, trace


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.invoke.return_value = {"messages": [MagicMock(content="Revenue is $127K")]}
    return agent


@pytest.fixture
async def client(mock_agent):
    app.state.agent = mock_agent
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.state.agent = None


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.fast
class TestChatEndpoint:
    async def test_chat_returns_sse_stream(self, client):
        """POST /chat returns SSE stream with token events."""
        output, trace = _make_output_and_trace()
        with patch("src.project_name.api.routes.chat.validated_invoke", return_value=(output, trace)):
            async with client.stream("POST", "/chat", json={"question": "What is revenue?"}) as resp:
                assert resp.status_code == 200
                assert "text/event-stream" in resp.headers["content-type"]
                body = await resp.aread()

        assert b"event: token" in body
        assert b"event: done" in body

    async def test_chat_sends_trace_event(self, client):
        """SSE stream ends with a trace event containing AgentTrace data."""
        output, trace = _make_output_and_trace()
        with patch("src.project_name.api.routes.chat.validated_invoke", return_value=(output, trace)):
            async with client.stream("POST", "/chat", json={"question": "What is revenue?"}) as resp:
                body = await resp.aread()

        assert b"event: trace" in body
        lines = body.decode().split("\n")
        trace_data = None
        for i, line in enumerate(lines):
            if line.strip() == "event: trace" and i + 1 < len(lines):
                data_line = lines[i + 1]
                if data_line.startswith("data: "):
                    trace_data = json.loads(data_line[6:])
        assert trace_data is not None
        assert "tools_called" in trace_data
        assert "hallucinated" in trace_data

    async def test_chat_sends_error_on_guardrail_failure(self, client):
        """GuardrailError produces an error SSE event, not a 500."""
        with patch(
            "src.project_name.api.routes.chat.validated_invoke",
            side_effect=GuardrailError(reason="Low confidence", attempts=3),
        ):
            async with client.stream("POST", "/chat", json={"question": "test?"}) as resp:
                body = await resp.aread()

        assert b"event: error" in body
        lines = body.decode().split("\n")
        for i, line in enumerate(lines):
            if line.strip() == "event: error" and i + 1 < len(lines):
                data_line = lines[i + 1]
                if data_line.startswith("data: "):
                    error_data = json.loads(data_line[6:])
                    assert error_data["attempts"] == 3
                    break

    async def test_health_returns_ok(self, client):
        """GET /health returns 200 with status ok."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data

    async def test_cors_allows_localhost(self, client):
        """CORS headers allow requests from localhost:3000."""
        resp = await client.options(
            "/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
