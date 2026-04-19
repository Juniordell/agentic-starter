---
name: langchain
description: >
  LangChain agents, @tool decorator, ReAct pattern, LangGraph state machines.
  Auto-activates when building agents, defining tools, or implementing
  multi-step reasoning pipelines.
---

# LangChain

## Core principle
Tools are the agent's actions. Docstrings are the agent's decision logic.
A bad docstring causes misrouting. A good docstring prevents hallucination.

## Defining tools
```python
from langchain_core.tools import tool

@tool
def execute_sql(query: str) -> str:
    """
    Execute a SQL query against the structured data store (Postgres/SQLite).

    Use this tool for:
    - Exact numeric questions (revenue, counts, averages, totals)
    - Date-range filtering
    - Aggregations (SUM, COUNT, AVG, GROUP BY)
    - Any question requiring precise data from structured tables

    Do NOT use for: free-text search, sentiment, meaning-based queries.
    """
    # implementation
    ...
```

## Building a ReAct agent
```python
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

llm = ChatAnthropic(model="claude-sonnet-4-6")
agent = create_react_agent(model=llm, tools=[execute_sql, semantic_search])
result = agent.invoke({"messages": [("user", question)]})
```

## Negative knowledge
- Do NOT put routing logic in the agent prompt — put it in tool docstrings
- Do NOT use `.run()` on chains — use `.invoke()` (LangChain v0.3+)
- Do NOT build chains for simple single-step calls — use direct API instead
- Do NOT ignore the `messages` key in LangGraph output
