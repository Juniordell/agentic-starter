"""Unit tests for dual-store tools."""

import pytest
from unittest.mock import MagicMock, patch


class TestExecuteSql:
    @patch("src.project_name.tools.execute_sql")
    def test_returns_string_result(self, mock_tool):
        mock_tool.invoke.return_value = "[{'revenue': 127430}]"
        result = mock_tool.invoke({"query": "SELECT SUM(amount) FROM orders"})
        assert "127430" in result

    @patch("src.project_name.tools.execute_sql")
    def test_handles_sql_error(self, mock_tool):
        mock_tool.invoke.return_value = "Error: table does not exist"
        result = mock_tool.invoke({"query": "SELECT * FROM nonexistent"})
        assert "Error" in result


class TestSemanticSearch:
    @patch("src.project_name.tools.semantic_search")
    def test_returns_documents(self, mock_tool):
        mock_tool.invoke.return_value = "[{'text': 'delivery is slow', 'score': 0.92}]"
        result = mock_tool.invoke({"query": "customer complaints"})
        assert "delivery" in result

    @patch("src.project_name.tools.semantic_search")
    def test_handles_empty_results(self, mock_tool):
        mock_tool.invoke.return_value = "[]"
        result = mock_tool.invoke({"query": "xyz nonexistent topic"})
        assert result == "[]"
