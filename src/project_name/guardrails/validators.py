"""
Semantic validators — go beyond schema to validate content correctness.

Schema validation (Pydantic) checks structure.
Semantic validation checks meaning and correctness.

Usage:
    validators = [
        ConfidenceValidator(min_confidence=0.7),
        SourceValidator(),
    ]
    for validator in validators:
        if not validator.validate(output, trace):
            raise GuardrailError(validator.failure_reason)
"""

import logging
from abc import ABC, abstractmethod
from src.project_name.models import QueryOutput
from src.project_name.observability.tracer import AgentTrace

logger = logging.getLogger(__name__)


class SemanticValidator(ABC):
    """Base class for semantic validators."""

    def __init__(self, question: str = "") -> None:
        self.question = question
        self.failure_reason: str = ""

    @abstractmethod
    def validate(self, output: QueryOutput, trace: AgentTrace) -> bool:
        """Return True if valid, False if guardrail triggered."""
        ...


class ConfidenceValidator(SemanticValidator):
    """
    Rejects responses where the model expressed low confidence.
    Low confidence = higher hallucination risk.
    """

    def __init__(self, min_confidence: float = 0.7, **kwargs) -> None:
        super().__init__(**kwargs)
        self.min_confidence = min_confidence

    def validate(self, output: QueryOutput, trace: AgentTrace) -> bool:
        if output.confidence < self.min_confidence:
            self.failure_reason = (
                f"Confidence {output.confidence:.2f} below threshold "
                f"{self.min_confidence:.2f}"
            )
            logger.warning("ConfidenceValidator failed", extra={
                "confidence": output.confidence,
                "threshold": self.min_confidence,
                "question": self.question,
            })
            return False
        return True


class SourceValidator(SemanticValidator):
    """
    Rejects responses that claim to have data but cite no sources.
    A model that answers without sources likely hallucinated the data.

    Set requires_data=False for conversational turns (greetings, clarifications)
    that don't need to query any data source.
    """

    def __init__(self, requires_data: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self.requires_data = requires_data

    def validate(self, output: QueryOutput, trace: AgentTrace) -> bool:
        if not self.requires_data:
            return True
        # If the agent called no tools, it answered from memory = hallucination risk
        if not trace.tools_called and output.answer:
            self.failure_reason = (
                "Agent answered without querying any data source. "
                "Possible hallucination."
            )
            logger.warning("SourceValidator failed", extra={
                "tools_called": trace.tools_called,
                "question": self.question,
            })
            return False
        return True


class ToolRoutingValidator(SemanticValidator):
    """
    Validates that the agent used the expected tool for a given question type.
    Catches misrouting — e.g., using semantic search for a numeric question.

    Usage:
        validator = ToolRoutingValidator(
            question="What is total revenue?",
            expected_tool="execute_sql",
            trigger_keywords=["revenue", "total", "count", "average"]
        )
    """

    def __init__(self, expected_tool: str,
                 trigger_keywords: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self.expected_tool = expected_tool
        self.trigger_keywords = trigger_keywords

    def validate(self, output: QueryOutput, trace: AgentTrace) -> bool:
        question_lower = self.question.lower()
        triggered = any(kw in question_lower for kw in self.trigger_keywords)

        if triggered and self.expected_tool not in trace.tools_called:
            self.failure_reason = (
                f"Question contains keywords {self.trigger_keywords} "
                f"but agent did not call '{self.expected_tool}'. "
                f"Tools called: {trace.tools_called}"
            )
            logger.warning("ToolRoutingValidator failed", extra={
                "expected_tool": self.expected_tool,
                "tools_called": trace.tools_called,
                "question": self.question,
            })
            return False
        return True
