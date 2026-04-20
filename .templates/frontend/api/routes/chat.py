"""
POST /chat — streams agent response as SSE.

SSE event format:
    event: token   data: {"token": "word"}
    event: trace   data: {"tools_called": [...], "latency_ms": 1240, ...}
    event: done    data: {}
    event: error   data: {"message": "...", "attempts": 3}

Never call agent.invoke() directly — always use validated_invoke().
"""

import asyncio
import json
import logging

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from src.project_name.api.schemas import ChatRequest, TraceEvent
from src.project_name.guardrails.retry import GuardrailError, validated_invoke

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat")
async def chat(request_body: ChatRequest, request: Request):
    """
    Stream an agent response for the given question.

    Calls validated_invoke() and streams the answer token by token,
    followed by the full AgentTrace and a done event.
    """
    agent = getattr(request.app.state, "agent", None)

    async def generate():
        if agent is None:
            yield {
                "event": "error",
                "data": json.dumps({
                    "message": "No agent configured. Set app.state.agent in lifespan.",
                    "attempts": 0,
                }),
            }
            return

        try:
            output, trace = await asyncio.to_thread(
                validated_invoke,
                agent=agent,
                question=request_body.question,
            )
        except GuardrailError as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": e.reason, "attempts": e.attempts}),
            }
            return
        except Exception as e:
            logger.error("Unexpected error in /chat", extra={"error": str(e)})
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e), "attempts": 0}),
            }
            return

        # Stream answer word by word
        words = output.answer.split()
        for i, word in enumerate(words):
            token = word if i == 0 else " " + word
            yield {"event": "token", "data": json.dumps({"token": token})}
            await asyncio.sleep(0)  # yield to event loop between tokens

        # Send full trace
        trace_event = TraceEvent(
            tools_called=trace.tools_called,
            total_steps=trace.total_steps,
            latency_ms=trace.latency_ms,
            hallucinated=trace.hallucinated,
            confidence=trace.confidence,
        )
        yield {"event": "trace", "data": trace_event.model_dump_json()}
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(generate())
