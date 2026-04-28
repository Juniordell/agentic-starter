"""
Agent definition — tools and factory.

Add your real tools here. The stubs below return canned data so the wiring
works immediately after bootstrap. Replace them with real DB/vector queries
before going to production.

Entry point:
    from src.project_name.agent import build_agent
    agent = build_agent()
"""

import json
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from src.project_name.config import get_settings


@tool
def execute_sql(query: str) -> str:
    """
    Query the SQL database for numeric and financial metrics.
    Use for: revenue, counts, totals, averages, rankings, time-series data.
    Never use for qualitative questions or free-text search.
    """
    # Stub — replace with real SQLAlchemy/psycopg query against your DATABASE_URL
    return json.dumps({
        "rows": [
            {"metric": "total_revenue", "value": 127430, "currency": "USD", "period": "Q1 2024"},
            {"metric": "total_orders",  "value": 3842,   "currency": None,  "period": "Q1 2024"},
        ],
        "query": query,
    })


@tool
def semantic_search(query: str) -> str:
    """
    Search the knowledge base for qualitative information and documents.
    Use for: customer feedback, complaints, feature requests, sentiment, free-text.
    Never use for numeric metrics or aggregations.
    """
    # Stub — replace with real Qdrant vector search against your QDRANT_URL
    return json.dumps({
        "results": [
            {"text": "Customers frequently mention fast delivery as a top satisfaction driver.", "score": 0.92},
            {"text": "Common complaints relate to checkout flow complexity.", "score": 0.87},
        ],
        "query": query,
    })


def build_agent(callbacks: list | None = None):
    """
    Build and return the ReAct agent.

    Wire your tools here. LangGraph's create_react_agent handles the
    Think → Act → Observe loop automatically based on tool docstrings.

    Pass callbacks=[TokenCounter()] to capture token usage for evals.
    """
    settings = get_settings()
    llm = ChatAnthropic(model=settings.model_name, callbacks=callbacks or [])
    return create_react_agent(
        model=llm,
        tools=[execute_sql, semantic_search],
        prompt=(
            "You are a data assistant. "
            "Always call a tool before answering questions about data — never answer from memory. "
            "Use execute_sql for numeric metrics and semantic_search for qualitative information."
        ),
    )
