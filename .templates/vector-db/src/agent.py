"""
Dual-store agent: routes questions to Postgres (SQL) or Qdrant (semantic).

Use validated_invoke() — never call agent.invoke() directly.
"""

import logging
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from src.project_name.config import get_settings
from src.project_name.guardrails.retry import validated_invoke
from src.project_name.observability.tracer import AgentTracer
from .tools import execute_sql, semantic_search

logger = logging.getLogger(__name__)


def build_agent():
    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.model_name,
        anthropic_api_key=settings.anthropic_api_key,
    )
    return create_react_agent(
        model=llm,
        tools=[execute_sql, semantic_search],
        prompt=(
            "You are a data analyst with access to two stores:\n"
            "1. Postgres (execute_sql) — exact, structured data\n"
            "2. Qdrant (semantic_search) — meaning-based search\n\n"
            "Always query a data source before answering. "
            "Never answer from memory alone."
        ),
    )


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def ask(question: str):
    """Ask the agent a question with full guardrails and tracing."""
    output, trace = validated_invoke(
        agent=get_agent(),
        question=question,
        max_retries=3,
    )
    logger.info("Question answered", extra={
        "tools_called": trace.tools_called,
        "latency_ms": trace.latency_ms,
        "hallucinated": trace.hallucinated,
    })
    return output
