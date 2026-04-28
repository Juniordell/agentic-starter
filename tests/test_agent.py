"""Unit tests for agent module — tools and build_agent()."""

import json
import pytest
from unittest.mock import MagicMock


class TestStubTools:
    def test_execute_sql_returns_json(self):
        from src.project_name.agent import execute_sql
        result = execute_sql.invoke({"query": "SELECT revenue FROM metrics"})
        data = json.loads(result)
        assert "rows" in data
        assert len(data["rows"]) > 0

    def test_semantic_search_returns_json(self):
        from src.project_name.agent import semantic_search
        result = semantic_search.invoke({"query": "customer complaints"})
        data = json.loads(result)
        assert "results" in data
        assert len(data["results"]) > 0

    def test_execute_sql_contains_numeric_data(self):
        from src.project_name.agent import execute_sql
        result = execute_sql.invoke({"query": "SELECT *"})
        data = json.loads(result)
        row = data["rows"][0]
        assert isinstance(row["value"], (int, float))

    def test_semantic_search_contains_text(self):
        from src.project_name.agent import semantic_search
        result = semantic_search.invoke({"query": "feedback"})
        data = json.loads(result)
        assert all("text" in r for r in data["results"])


class TestBuildAgent:
    def test_build_agent_returns_invocable(self):
        """build_agent() should return an object with .invoke()."""
        from src.project_name.agent import build_agent
        agent = build_agent()
        assert hasattr(agent, "invoke")

    def test_execute_sql_has_routing_docstring(self):
        """Tool description must mention routing keywords so the LLM routes correctly."""
        from src.project_name.agent import execute_sql
        # LangChain @tool stores the docstring in .description, not .__doc__
        desc = (execute_sql.description or "").lower()
        assert "revenue" in desc or "numeric" in desc or "sql" in desc

    def test_semantic_search_has_routing_docstring(self):
        from src.project_name.agent import semantic_search
        desc = (semantic_search.description or "").lower()
        assert "feedback" in desc or "qualitative" in desc or "search" in desc


class TestSourceValidatorRequiresData:
    def test_conversational_turn_bypasses_source_check(self):
        """Greetings and clarifications should not be flagged as hallucinations."""
        from src.project_name.guardrails.validators import SourceValidator
        from src.project_name.models import QueryOutput
        from src.project_name.observability.tracer import AgentTrace

        v = SourceValidator(question="Olá, tudo bem?", requires_data=False)
        output = QueryOutput(answer="Olá! Estou bem, obrigado.", confidence=0.9)
        trace = AgentTrace(question="Olá, tudo bem?")
        # No tools called — but that's fine for a conversational turn
        assert v.validate(output, trace) is True

    def test_data_question_still_requires_tools(self):
        """requires_data=True (default) must still enforce source check."""
        from src.project_name.guardrails.validators import SourceValidator
        from src.project_name.models import QueryOutput
        from src.project_name.observability.tracer import AgentTrace

        v = SourceValidator(question="What is revenue?")  # requires_data=True by default
        output = QueryOutput(answer="Revenue is $100K", confidence=0.9)
        trace = AgentTrace(question="What is revenue?")
        assert v.validate(output, trace) is False
