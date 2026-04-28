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
from typing import Callable
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


def _extract_confidence(question: str, answer: str, model_name: str) -> float:
    """
    Extract real model confidence via instructor structured output.

    Makes a cheap follow-up call to rate how confident the model is in its
    own answer. This replaces any hardcoded value and gives ConfidenceValidator
    a real signal to act on.
    """
    import instructor
    from anthropic import Anthropic
    from pydantic import BaseModel as _Base, Field as _Field
    from typing import Annotated as _Ann

    class _Conf(_Base):
        confidence: _Ann[float, _Field(ge=0.0, le=1.0)] = _Field(
            description="0.0 = very uncertain, 1.0 = certain the answer is accurate and complete"
        )

    client = instructor.from_anthropic(Anthropic())
    result = client.messages.create(
        model=model_name,
        max_tokens=64,
        response_model=_Conf,
        messages=[{"role": "user", "content": f"Question: {question}\nAnswer: {answer}"}],
        system="Rate your confidence (0.0–1.0) that the answer is accurate and complete.",
    )
    return result.confidence


def validated_invoke(
    agent,
    question: str,
    validators: list[SemanticValidator] | None = None,
    max_retries: int = 3,
    backoff_base: float = 1.5,
    confidence_fn: Callable[[str, str], float] | None = None,
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
        confidence_fn: callable(question, answer) -> float that extracts
                       real confidence. Defaults to _extract_confidence via
                       instructor. Pass a lambda in tests to avoid API calls.

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

    if confidence_fn is None:
        from src.project_name.config import get_settings
        _model = get_settings().model_name
        confidence_fn = lambda q, a: _extract_confidence(q, a, _model)  # noqa: E731

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

                confidence = confidence_fn(question, answer)
                output = QueryOutput(
                    answer=answer,
                    confidence=confidence,
                    sources=tracer.trace.tools_called,
                )
                tracer.set_output(answer, confidence=confidence)

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
