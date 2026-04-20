---
name: frontend
description: >
  Next.js App Router, Tailwind CSS, TypeScript, SSE streaming, and FastAPI
  integration. Auto-activates when working in frontend/ or src/.../api/.
  Contains patterns for components, hooks, and API routes.
---

# Frontend

## Architecture
- FastAPI: `src/{{project_name}}/api/` on port 8000
- Next.js: `frontend/` on port 3000
- Communication: `/api/*` in Next.js is rewritten to FastAPI via `next.config.ts`
- Never hardcode `localhost:8000` — use the rewrite

## Streaming with streamChat()

```typescript
import { streamChat } from '@/lib/sse'

for await (const event of streamChat(question, abortController.signal)) {
  if (event.type === 'token') append(event.data.token)
  if (event.type === 'trace') console.log(event.data.tools_called)
  if (event.type === 'error') showError(event.data.message)
  if (event.type === 'done') setDone(true)
}
```

## useStream() hook

```typescript
import { useStream } from '@/hooks/useStream'

const { messages, isStreaming, lastTrace, error, sendMessage, abort } = useStream()

// Send a question and stream the response
await sendMessage('What is total revenue?')

// Abort mid-stream
abort()
```

## Primitive components

```tsx
import { Button } from '@/components/primitives/Button'
import { Card } from '@/components/primitives/Card'
import { Input } from '@/components/primitives/Input'
import { Badge } from '@/components/primitives/Badge'
import { Spinner } from '@/components/primitives/Spinner'

// All accept className for Tailwind overrides
<Button variant="primary" size="md" onClick={handleClick}>Send</Button>
<Button variant="ghost" disabled={isStreaming}>Cancel</Button>

<Card className="mt-4">Content here</Card>

<Input placeholder="Ask a question..." onChange={e => setQ(e.target.value)} />

<Badge variant="success">Connected</Badge>
<Badge variant="error">Hallucination detected</Badge>

{isStreaming && <Spinner size="sm" />}
```

## Adding a new API route

**FastAPI side** — add to `src/{{project_name}}/api/routes/`:
```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint() -> dict:
    return {"result": "..."}
```
Register in `main.py`:
```python
from src.{{project_name}}.api.routes.my_endpoint import router as my_router
app.include_router(my_router)
```

**Next.js side** — the rewrite in `next.config.ts` forwards `/api/*` to FastAPI automatically. No Next.js API route needed. Call it via `lib/api.ts`:
```typescript
export async function fetchMyEndpoint() {
  const res = await fetch('/api/my-endpoint')
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}
```

## TypeScript conventions
- No `any` — ever
- All props interfaces extend the relevant HTML element attributes
- Use `Record<Variant, string>` for variant maps, not if/else chains
- `'use client'` only on components that use hooks or browser APIs

## Negative knowledge
- Do NOT use `allow_origins=["*"]` in FastAPI CORS
- Do NOT hardcode `localhost:8000` — only in `.env.local.example`
- Do NOT add shadcn, MUI, or any component library — Tailwind only
- Do NOT buffer SSE responses — stream through
- Do NOT add domain logic to FastAPI routes — routes call `validated_invoke()` only
- Do NOT skip Vitest tests for new primitives
