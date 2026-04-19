"""
LangChain tools for the dual-store agent (Postgres + Qdrant).

Tool docstrings define routing logic — the agent reads them to decide
which tool to call. Keep docstrings explicit about when to use each tool.
"""

import logging
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient

from src.project_name.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_engine = create_engine(settings.database_url)
_qdrant = QdrantClient(url=settings.qdrant_url)


@tool
def execute_sql(query: str) -> str:
    """
    Execute a SQL query against the structured data store (Postgres).

    Use this tool for:
    - Exact numeric questions (revenue, counts, averages, totals)
    - Date-range filtering
    - Aggregations (SUM, COUNT, AVG, GROUP BY)
    - Any question requiring precise data from structured tables

    Do NOT use for: free-text search, sentiment, meaning-based queries.

    Args:
        query: A safe, read-only SQL SELECT statement.

    Returns:
        Query results as a formatted string.
    """
    try:
        with _engine.connect() as conn:
            result = conn.execute(text(query))
            rows = [dict(row._mapping) for row in result]
            logger.info("SQL executed", extra={"rows_returned": len(rows)})
            return str(rows)
    except Exception as e:
        logger.error("SQL execution failed", extra={"error": str(e)})
        return f"Error: {e}"


@tool
def semantic_search(query: str, limit: int = 5) -> str:
    """
    Search the vector store (Qdrant) using semantic similarity.

    Use this tool for:
    - Sentiment analysis ("what are customers complaining about?")
    - Concept search ("find feedback about delivery")
    - Free-text similarity queries
    - Any question about meaning, not exact data

    Do NOT use for: exact numbers, dates, structured aggregations.

    Args:
        query: Natural language search query.
        limit: Maximum number of results (default 5).

    Returns:
        Semantically similar documents as a formatted string.
    """
    try:
        from fastembed import TextEmbedding
        embedder = TextEmbedding()
        vector = list(embedder.embed([query]))[0].tolist()

        results = _qdrant.search(
            collection_name="memory",
            query_vector=vector,
            limit=limit,
        )
        docs = [{"text": r.payload.get("text", ""), "score": r.score}
                for r in results]
        logger.info("Semantic search done", extra={"results": len(docs)})
        return str(docs)
    except Exception as e:
        logger.error("Semantic search failed", extra={"error": str(e)})
        return f"Error: {e}"
