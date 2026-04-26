"""Root conftest — applies to all tests and evals."""

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip @pytest.mark.llm tests unless --run-llm flag is passed."""
    if config.getoption("--run-llm", default=False):
        return
    skip_llm = pytest.mark.skip(reason="requires real LLM API call — run with --run-llm to enable")
    for item in items:
        if item.get_closest_marker("llm"):
            item.add_marker(skip_llm)


def pytest_addoption(parser):
    parser.addoption(
        "--run-llm",
        action="store_true",
        default=False,
        help="Run tests marked @pytest.mark.llm (requires LLM auth)",
    )
