---
name: qdrant
description: >
  Qdrant vector store, embeddings, semantic search, and RAG pipeline.
  Auto-activates when implementing semantic search, vector similarity,
  or retrieval-augmented generation.
---

# Qdrant

## Core principle
Qdrant stores meaning, not data. Use it for questions about concepts,
sentiment, and free-text similarity — not for exact numbers.

## Connection
```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
```

## Upsert vectors
```python
from qdrant_client.models import PointStruct

client.upsert(
    collection_name="memory",
    points=[
        PointStruct(id=1, vector=[0.1, 0.2, ...], payload={"text": "..."}),
    ]
)
```

## Semantic search
```python
results = client.search(
    collection_name="memory",
    query_vector=embed(query),
    limit=5,
)
for hit in results:
    print(hit.payload["text"], hit.score)
```

## Routing rule
- Exact number / date → Postgres (SQL)
- Meaning / text / sentiment → Qdrant (semantic search)
- Hybrid → both stores

## Negative knowledge
- Do NOT store structured numeric data in Qdrant — use Postgres
- Do NOT use cosine similarity for non-normalized vectors
- Do NOT hardcode collection names — use config
