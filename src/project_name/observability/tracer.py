"""
Agent observability — trace every invocation.

Tracks tools called, steps taken, latency, and hallucination signals.
Use AgentTracer as a context manager around every agent.invoke() call.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentStep:
    """A single step in the agent's ReAct loop."""
    step_num: int
    thought: str | None = None
    tool_called: str | None = None
    tool_input: dict | None = None
    tool_output: str | None = None
    latency_ms: float = 0.0


@dataclass
class AgentTrace:
    """Complete trace of a single agent invocation."""
    question: str
    steps: list[AgentStep] = field(default_factory=list)
    tools_called: list[str] = field(default_factory=list)
    final_answer: str | None = None
    confidence: float | None = None
    total_steps: int = 0
    latency_ms: float = 0.0
    hallucinated: bool = False
    error: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0

    def mark_hallucinated(self) -> None:
        """Flag this trace as hallucinated — answered without querying sources."""
        self.hallucinated = True
        logger.warning(
            "Hallucination detected",
            extra={
                "question": self.question,
                "tools_called": self.tools_called,
                "total_steps": self.total_steps,
            }
        )

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "tools_called": self.tools_called,
            "total_steps": self.total_steps,
            "latency_ms": round(self.latency_ms, 2),
            "confidence": self.confidence,
            "hallucinated": self.hallucinated,
            "error": self.error,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


class AgentTracer:
    """
    Context manager that wraps an agent invocation and produces a trace.

    Usage:
        with AgentTracer(question="What is revenue?") as tracer:
            result = agent.invoke({"messages": [("user", question)]})
            tracer.set_output(result, confidence=result.get("confidence"))

        trace = tracer.trace
        print(trace.tools_called)
        print(trace.latency_ms)
    """

    def __init__(self, question: str) -> None:
        self.question = question
        self.trace = AgentTrace(question=question)
        self._start_time: float = 0.0

    def __enter__(self) -> "AgentTracer":
        self._start_time = time.monotonic()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        elapsed = (time.monotonic() - self._start_time) * 1000
        self.trace.latency_ms = elapsed

        if exc_type is not None:
            self.trace.error = str(exc_val)
            logger.error(
                "Agent invocation failed",
                extra={"question": self.question, "error": str(exc_val)}
            )

        logger.info(
            "Agent trace complete",
            extra=self.trace.to_dict()
        )

    def record_tool_call(self, tool_name: str, tool_input: dict,
                         tool_output: str, latency_ms: float = 0.0) -> None:
        """Record a tool call during agent execution."""
        step = AgentStep(
            step_num=len(self.trace.steps) + 1,
            tool_called=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            latency_ms=latency_ms,
        )
        self.trace.steps.append(step)
        self.trace.tools_called.append(tool_name)
        self.trace.total_steps += 1

    def set_output(self, answer: str, confidence: float | None = None) -> None:
        """Set the final answer and confidence from the agent output."""
        self.trace.final_answer = answer
        self.trace.confidence = confidence

        # Hallucination heuristic: answered but called no tools
        if not self.trace.tools_called and answer:
            self.trace.mark_hallucinated()
