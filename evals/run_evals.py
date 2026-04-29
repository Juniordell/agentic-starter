"""
Eval runner — measures token economy, hallucination rate, routing precision, latency.

Runs each case in two modes:
  naive   — agent.invoke() directly, no guardrails, no confidence call
  guarded — validated_invoke() with ConfidenceValidator + SourceValidator

This gives you an honest comparison. Guardrails cost tokens and latency.
They earn their keep by reducing hallucinations and catching bad routing.
Don't claim wins without running this first.

Usage:
    uv run python evals/run_evals.py            # dry run with mock agent
    uv run python evals/run_evals.py --llm      # real LLM (costs tokens)
    uv run python evals/run_evals.py --llm --out results.json
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Ensure project root is in sys.path so `from src.project_name.*` works
# when this script is run directly (not via pytest which sets pythonpath).
sys.path.insert(0, str(Path(__file__).parent.parent))

# Claude Sonnet 4.6 pricing (USD per million tokens, as of 2025-Q2)
# Update if pricing changes: https://www.anthropic.com/pricing
_INPUT_PRICE_PER_M = 3.0
_OUTPUT_PRICE_PER_M = 15.0

DATASET_PATH = Path(__file__).parent / "datasets" / "agent_behavior.json"


# ── Token counter callback ────────────────────────────────────────────────────

from langchain_core.callbacks import BaseCallbackHandler


class _TokenCounter(BaseCallbackHandler):
    """
    LangChain callback that accumulates input/output tokens across LLM calls.
    Pass an instance to build_agent(callbacks=[counter]) then reset() per case.
    """

    def __init__(self) -> None:
        super().__init__()
        self.input_tokens = 0
        self.output_tokens = 0

    def reset(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0

    def on_llm_end(self, response, **kwargs) -> None:
        usage = (getattr(response, "llm_output", None) or {}).get("usage", {})
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)


# ── Result model ──────────────────────────────────────────────────────────────

@dataclass
class EvalResult:
    case_id: str
    question: str
    mode: str                            # "naive" | "guarded"
    answer: str | None = None
    tools_called: list[str] = field(default_factory=list)
    expected_tool: str | None = None
    routing_correct: bool | None = None   # None = case has no expected_tool
    hallucinated: bool | None = None      # None = unmeasurable (e.g. dry-run guarded)
    confidence: float | None = None
    agent_input_tokens: int = 0
    agent_output_tokens: int = 0
    confidence_input_tokens: int = 0     # extra call made by _extract_confidence
    confidence_output_tokens: int = 0
    latency_ms: float = 0.0
    retries: int = 0
    error: str | None = None

    @property
    def total_tokens(self) -> int:
        return (self.agent_input_tokens + self.agent_output_tokens
                + self.confidence_input_tokens + self.confidence_output_tokens)

    @property
    def cost_usd(self) -> float:
        total_in = self.agent_input_tokens + self.confidence_input_tokens
        total_out = self.agent_output_tokens + self.confidence_output_tokens
        return (total_in * _INPUT_PRICE_PER_M + total_out * _OUTPUT_PRICE_PER_M) / 1_000_000

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "mode": self.mode,
            "routing_correct": self.routing_correct,
            "hallucinated": self.hallucinated,
            "confidence": self.confidence,
            "total_tokens": self.total_tokens,
            "agent_tokens": self.agent_input_tokens + self.agent_output_tokens,
            "confidence_tokens": self.confidence_input_tokens + self.confidence_output_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "latency_ms": round(self.latency_ms, 1),
            "retries": self.retries,
            "error": self.error,
        }


# ── Confidence with token tracking ───────────────────────────────────────────

def _tracked_confidence(question: str, answer: str, model_name: str) -> tuple[float, int, int]:
    """
    Call the model to rate its own confidence.
    Returns (confidence, input_tokens, output_tokens).

    Uses the raw Anthropic SDK so we get usage directly from the response.
    """
    import re
    from anthropic import Anthropic

    client = Anthropic()
    response = client.messages.create(
        model=model_name,
        max_tokens=64,
        system=(
            'You are a JSON API. Output ONLY a JSON object with a single field.\n'
            'Rate how confident you are (0.0–1.0) that the answer correctly addresses the question.\n'
            'Example output: {"confidence": 0.85}'
        ),
        messages=[{"role": "user", "content": f"Question: {question}\nAnswer: {answer}"}],
    )
    text = response.content[0].text.strip()
    # Strip markdown code fences if the model wraps the JSON
    text = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        confidence = float(json.loads(text)["confidence"])
    except (json.JSONDecodeError, KeyError, ValueError):
        # Regex fallback for partial JSON or trailing text
        m = re.search(r'"confidence"\s*:\s*([\d.]+)', text)
        confidence = float(m.group(1)) if m else 0.5
    return max(0.0, min(1.0, confidence)), response.usage.input_tokens, response.usage.output_tokens


# ── Run modes ─────────────────────────────────────────────────────────────────

def run_naive(agent, case: dict, counter: _TokenCounter) -> EvalResult:
    """Invoke the agent directly — no validators, no confidence call."""
    counter.reset()
    result = EvalResult(case_id=case["id"], question=case["question"], mode="naive")
    start = time.monotonic()

    try:
        raw = agent.invoke(
            {"messages": [("user", case["question"])]},
            config={"callbacks": [counter]},
        )
        messages = raw.get("messages", [])
        result.answer = messages[-1].content if messages else ""

        # Extract tool names from ToolMessage entries in the message list
        result.tools_called = [
            m.name for m in messages
            if hasattr(m, "name") and m.name and hasattr(m, "type") and m.type == "tool"
        ]
        result.hallucinated = bool(result.answer and not result.tools_called)

    except Exception as exc:
        result.error = str(exc)

    result.latency_ms = (time.monotonic() - start) * 1000
    result.agent_input_tokens = counter.input_tokens
    result.agent_output_tokens = counter.output_tokens

    if "expected_tool" in case:
        result.expected_tool = case["expected_tool"]
        result.routing_correct = case["expected_tool"] in result.tools_called

    return result


def run_guarded(agent, case: dict, counter: _TokenCounter, model_name: str) -> EvalResult:
    """Invoke via validated_invoke — confidence extraction + semantic validators."""
    from src.project_name.guardrails.retry import validated_invoke
    from src.project_name.guardrails.validators import ConfidenceValidator, SourceValidator

    counter.reset()
    result = EvalResult(case_id=case["id"], question=case["question"], mode="guarded")
    conf_in = conf_out = 0
    attempt_count = 0

    def _conf_fn(q: str, a: str) -> float:
        nonlocal conf_in, conf_out, attempt_count
        attempt_count += 1
        conf, tin, tout = _tracked_confidence(q, a, model_name)
        conf_in += tin
        conf_out += tout
        return conf

    try:
        output, trace = validated_invoke(
            agent=agent,
            question=case["question"],
            validators=[
                ConfidenceValidator(min_confidence=0.7, question=case["question"]),
                SourceValidator(question=case["question"]),
            ],
            confidence_fn=_conf_fn,
            max_retries=2,
            backoff_base=0.5,
        )
        result.answer = output.answer
        result.tools_called = trace.tools_called
        result.hallucinated = trace.hallucinated
        result.confidence = output.confidence
        result.latency_ms = trace.latency_ms
        result.retries = max(0, attempt_count - 1)

    except Exception as exc:
        result.error = str(exc)
        result.latency_ms = (time.monotonic()) * 0  # already measured in trace

    result.agent_input_tokens = counter.input_tokens
    result.agent_output_tokens = counter.output_tokens
    result.confidence_input_tokens = conf_in
    result.confidence_output_tokens = conf_out

    if "expected_tool" in case:
        result.expected_tool = case["expected_tool"]
        result.routing_correct = case["expected_tool"] in result.tools_called

    return result


# ── Mock agent for dry runs ───────────────────────────────────────────────────

def _mock_agent(case: dict):
    """Returns a fake agent that simulates tool calls based on case tags."""
    from unittest.mock import MagicMock

    agent = MagicMock()
    tags = case.get("tags", [])

    class _FakeMsg:
        def __init__(self, content, name=None, type="ai"):
            self.content = content
            self.name = name
            self.type = type

    if "sql" in tags:
        msgs = [
            _FakeMsg('{"rows": [{"value": 127430}]}', name="execute_sql", type="tool"),
            _FakeMsg("Total revenue is $127,430."),
        ]
    elif "semantic" in tags:
        msgs = [
            _FakeMsg('{"results": [{"text": "Delivery complaints."}]}', name="semantic_search", type="tool"),
            _FakeMsg("Customers complain mainly about delivery times."),
        ]
    elif "hallucination" in tags:
        # Simulate the bad case: answers without calling a tool
        msgs = [_FakeMsg("I don't have data on that customer.")]
    else:
        msgs = [_FakeMsg("Here is the information you requested.")]

    agent.invoke.return_value = {"messages": msgs}
    return agent


# ── Report ────────────────────────────────────────────────────────────────────

def _fmt_bool(val: bool | None) -> str:
    if val is None:
        return "—"
    return "✓" if val else "✗"


def _fmt_tokens(n: int) -> str:
    return str(n) if n else "—"


def print_report(naive: list[EvalResult], guarded: list[EvalResult]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        _rich = True
    except ImportError:
        _rich = False

    pairs = list(zip(naive, guarded))

    if _rich:
        console = Console()
        table = Table(
            title="Naive vs. Guarded",
            box=box.SIMPLE_HEAD,
            show_footer=True,
        )
        table.add_column("Case", style="bold")
        table.add_column("Naive Route", justify="center")
        table.add_column("Naive Hall.", justify="center")
        table.add_column("Naive Tok.", justify="right")
        table.add_column("Guard Route", justify="center")
        table.add_column("Guard Conf.", justify="right")
        table.add_column("Guard Tok.", justify="right")
        table.add_column("Overhead", justify="right")
        table.add_column("Retries", justify="center")

        for n, g in pairs:
            overhead = (
                f"+{((g.total_tokens / n.total_tokens) - 1) * 100:.0f}%"
                if n.total_tokens > 0 else "—"
            )
            table.add_row(
                n.case_id,
                _fmt_bool(n.routing_correct),
                "✗" if n.hallucinated else "✓",
                _fmt_tokens(n.total_tokens),
                _fmt_bool(g.routing_correct),
                f"{g.confidence:.2f}" if g.confidence is not None else "—",
                _fmt_tokens(g.total_tokens),
                overhead,
                str(g.retries),
            )

        console.print(table)
        _print_summary(naive, guarded, console)
    else:
        # Fallback plain text
        print(f"\n{'Case':<25} {'N-Route':>7} {'N-Hall':>6} {'N-Tok':>6} {'G-Route':>7} {'G-Conf':>7} {'G-Tok':>6} {'Overhead':>9} {'Ret':>3}")
        print("-" * 80)
        for n, g in pairs:
            overhead = (
                f"+{((g.total_tokens / n.total_tokens) - 1) * 100:.0f}%"
                if n.total_tokens > 0 else "—"
            )
            print(
                f"{n.case_id:<25} {_fmt_bool(n.routing_correct):>7} "
                f"{'✗' if n.hallucinated else '✓':>6} {_fmt_tokens(n.total_tokens):>6} "
                f"{_fmt_bool(g.routing_correct):>7} "
                f"{f'{g.confidence:.2f}' if g.confidence is not None else '—':>7} "
                f"{_fmt_tokens(g.total_tokens):>6} {overhead:>9} {g.retries:>3}"
            )
        _print_summary(naive, guarded)


def _print_summary(
    naive: list[EvalResult],
    guarded: list[EvalResult],
    console=None,
) -> None:
    n_cases = len(naive)
    if n_cases == 0:
        return

    def _pct(results, fn):
        # Exclude errored cases — they have no meaningful signal
        scored = [r for r in results if r.error is None and fn(r) is not None]
        if not scored:
            return "—"
        hits = sum(1 for r in scored if fn(r))
        return f"{hits}/{len(scored)} ({hits/len(scored):.0%})"

    def _avg(results, fn):
        vals = [fn(r) for r in results if r.error is None and fn(r) is not None]
        return f"{sum(vals)/len(vals):.0f}" if vals else "—"

    lines = [
        "",
        "── Summary " + "─" * 50,
        f"  Routing accuracy  naive {_pct(naive, lambda r: r.routing_correct):<15}  "
        f"guarded {_pct(guarded, lambda r: r.routing_correct)}",
        f"  Hallucination     naive {_pct(naive, lambda r: r.hallucinated):<15}  "
        f"guarded {_pct(guarded, lambda r: r.hallucinated)}",
        f"  Avg tokens/query  naive {_avg(naive, lambda r: r.total_tokens or None):<15}  "
        f"guarded {_avg(guarded, lambda r: r.total_tokens or None)}",
        f"  Total cost        naive ${sum(r.cost_usd for r in naive):.6f}          "
        f"guarded ${sum(r.cost_usd for r in guarded):.6f}",
        f"  Avg latency (ms)  naive {_avg(naive, lambda r: r.latency_ms or None):<15}  "
        f"guarded {_avg(guarded, lambda r: r.latency_ms or None)}",
        "",
        "  ⚠  Guardrails cost more tokens per call. They save tokens only when they",
        "     catch a hallucination that would've triggered a user re-run.",
        "",
    ]
    out = "\n".join(lines)
    if console:
        console.print(out)
    else:
        print(out)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import logging
    from dotenv import load_dotenv
    load_dotenv()
    # Suppress tracer/guardrail logs so they don't pollute the report output
    logging.getLogger("src").setLevel(logging.ERROR)

    parser = argparse.ArgumentParser(description="Eval runner — naive vs. guarded")
    parser.add_argument("--llm", action="store_true", help="Use real LLM (costs tokens)")
    parser.add_argument("--out", metavar="FILE", help="Save results to JSON file")
    args = parser.parse_args()

    with open(DATASET_PATH) as f:
        dataset = json.load(f)
    cases = dataset["cases"]

    if args.llm:
        from src.project_name.agent import build_agent
        from src.project_name.config import get_settings
        counter = _TokenCounter()
        agent = build_agent(callbacks=[counter])
        model_name = get_settings().model_name
        print(f"Running {len(cases)} cases with real LLM ({model_name})…\n")
    else:
        counter = _TokenCounter()
        model_name = "mock"
        print(f"Running {len(cases)} cases in DRY RUN mode (mock agent).\n"
              "Pass --llm to run with the real model.\n")

    naive_results: list[EvalResult] = []
    guarded_results: list[EvalResult] = []

    for case in cases:
        agent = build_agent(callbacks=[counter]) if args.llm else _mock_agent(case)
        print(f"  {case['id']}…", end=" ", flush=True)

        # Naive run
        counter.reset()
        naive = run_naive(agent, case, counter)
        naive_results.append(naive)

        # Guarded run (reuse same agent)
        counter.reset()
        if args.llm:
            guarded = run_guarded(agent, case, counter, model_name)
        else:
            # Dry run: guarded with mock confidence.
            # SourceValidator is omitted — it requires real tracer tool recording,
            # which only happens with a real LangGraph agent. Use --llm to test it.
            from src.project_name.guardrails.retry import validated_invoke
            from src.project_name.guardrails.validators import ConfidenceValidator
            g = EvalResult(case_id=case["id"], question=case["question"], mode="guarded")
            try:
                output, trace = validated_invoke(
                    agent=agent,
                    question=case["question"],
                    validators=[
                        ConfidenceValidator(min_confidence=0.7, question=case["question"]),
                    ],
                    confidence_fn=lambda q, a: 0.85,
                    max_retries=1,
                    backoff_base=0.0,
                )
                g.answer = output.answer
                g.tools_called = trace.tools_called
                # hallucinated left as None — mock tracer can't record tool calls,
                # so trace.hallucinated is always True and would be misleading.
                g.confidence = output.confidence
                g.latency_ms = trace.latency_ms
            except Exception as exc:
                g.error = str(exc)
            # Routing can't be measured in dry-run: mock agent doesn't populate
            # the AgentTracer, so tools_called is always empty. Use --llm.
            if "expected_tool" in case:
                g.expected_tool = case["expected_tool"]
                g.routing_correct = None  # unmeasurable without real LangGraph calls
            guarded = g
        guarded_results.append(guarded)

        status = "✓" if not naive.error and not guarded.error else "✗"
        print(status)

    print()
    print_report(naive_results, guarded_results)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps({
            "naive": [r.to_dict() for r in naive_results],
            "guarded": [r.to_dict() for r in guarded_results],
        }, indent=2))
        print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
