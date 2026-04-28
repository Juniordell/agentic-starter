"""
CLI entry point.

Usage:
    python -m project_name "What is total revenue?"
    uv run python -m project_name "What are customers complaining about?"
"""

import sys
import logging

logging.basicConfig(level=logging.WARNING)


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('Usage: python -m project_name "your question here"')
        sys.exit(1)

    from src.project_name.agent import build_agent
    from src.project_name.guardrails.retry import validated_invoke

    print(f"\nQuestion: {question}")
    print("Thinking...\n")

    agent = build_agent()
    output, trace = validated_invoke(agent=agent, question=question)

    print(f"Answer:     {output.answer}")
    print(f"Confidence: {output.confidence:.0%}")
    print(f"Sources:    {', '.join(output.sources) or 'none'}")
    print(f"Latency:    {trace.latency_ms:.0f}ms")


if __name__ == "__main__":
    main()
