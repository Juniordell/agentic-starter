"""
validated_invoke — wraps agent calls with semantic validation and retry.

This is the main entry point for all agent invocations.
Never call agent.invoke() directly — always use validated_invoke().

Usage:
    result = validated_invoke(
        agent=agent,
        question="What is total revenue?",
        validators=[ConfidenceValidator(0.7), SourceValidator()],
        max_retries=3,
    )
"""

import time
import logging
from src.project_name.models import QueryOutput
from src.project_name.observability.tracer import AgentTracer, AgentTrace
from src.project_name.guardrails.validators import (
    SemanticValidator,
    ConfidenceValidator,
    SourceValidator,
)

logger = logging.getLogger(__name__)


class GuardrailError(Exception):
    """Raised when the agent fails all retries or violates a hard guardrail."""
    def __init__(self, reason: str, attempts: int = 0) -> None:
        self.reason = reason
        self.attempts = attempts
        super().__init__(f"GuardrailError after {attempts} attempts: {reason}")


def validated_invoke(
    agent,
    question: str,
    validators: list[SemanticValidator] | None = None,
    max_retries: int = 3,
    backoff_base: float = 1.5,
) -> tuple[QueryOutput, AgentTrace]:
    """
    Invoke an agent with semantic validation and automatic retry.

    Args:
        agent: LangChain/LangGraph agent with .invoke() method
        question: the user question
        validators: list of SemanticValidator instances (defaults to
                    ConfidenceValidator + SourceValidator)
        max_retries: maximum number of attempts before raising GuardrailError
        backoff_base: exponential backoff multiplier between retries

    Returns:
        (QueryOutput, AgentTrace) — validated output and its trace

    Raises:
        GuardrailError — if all retries are exhausted
    """

    if validators is None:
        validators = [
            ConfidenceValidator(min_confidence=0.7, question=question),
            SourceValidator(question=question),
        ]

    last_reason = "Unknown failure"

    for attempt in range(1, max_retries + 1):
        logger.info(f"Agent attempt {attempt}/{max_retries}", extra={
            "question": question, "attempt": attempt
        })

        with AgentTracer(question=question) as tracer:
            try:
                raw = agent.invoke({"messages": [("user", question)]})

                # Extract the last AI message content as the answer
                messages = raw.get("messages", [])
                answer = messages[-1].content if messages else ""

                # Build structured output — adjust fields to your domain
                output = QueryOutput(
                    answer=answer,
                    confidence=0.9,   # override with model-provided confidence
                    sources=tracer.trace.tools_called,
                )
                tracer.set_output(answer, confidence=output.confidence)

            except Exception as e:
                logger.error(f"Agent invocation error: {e}")
                last_reason = str(e)
                _sleep_backoff(attempt, backoff_base)
                continue

        # Run semantic validators
        all_valid = True
        for validator in validators:
            if not validator.validate(output, tracer.trace):
                last_reason = validator.failure_reason
                all_valid = False
                break

        if all_valid:
            logger.info("Agent response validated", extra={
                "attempt": attempt,
                "latency_ms": tracer.trace.latency_ms,
                "tools_called": tracer.trace.tools_called,
            })
            return output, tracer.trace

        logger.warning(
            f"Guardrail failed on attempt {attempt}: {last_reason}",
            extra={"question": question, "attempt": attempt}
        )
        _sleep_backoff(attempt, backoff_base)

    raise GuardrailError(reason=last_reason, attempts=max_retries)


def _sleep_backoff(attempt: int, base: float) -> None:
    """Exponential backoff between retries: 1.5s, 2.25s, 3.375s..."""
    delay = base ** attempt
    logger.debug(f"Backoff: sleeping {delay:.2f}s before retry")
    time.sleep(delay)
