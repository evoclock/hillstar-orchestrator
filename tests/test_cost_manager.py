"""
Unit tests for execution/cost_manager.py

Tests cost tracking, budget checking, and cost estimation logic.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.cost_manager import CostManager


@pytest.fixture
def test_model_config():
    """Test model configuration with pricing."""
    return {
        "anthropic": {
            "models": {
                "claude-opus-4-6": {
                    "input_cost_per_token": 0.015,
                    "output_cost_per_token": 0.075,
                }
            }
        },
        "openai": {
            "models": {
                "gpt-4o": {
                    "input_cost_per_token": 0.005,
                    "output_cost_per_token": 0.015,
                }
            }
        },
        "ollama": {
            "models": {
                "devstral-2:123b-cloud": {
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0,
                }
            }
        },
    }


@pytest.fixture
def cost_manager(test_model_config):
    """Create a CostManager instance for testing."""
    return CostManager(test_model_config)


class TestCostManagerInit:
    """Test CostManager initialization."""

    def test_initialization_with_config(self, cost_manager, test_model_config):
        """Test that CostManager initializes with model config."""
        assert cost_manager.model_config == test_model_config
        assert cost_manager.cumulative_cost_usd == 0.0
        assert cost_manager.node_costs == {}

    def test_zero_initial_cost(self, cost_manager):
        """Test that initial cumulative cost is zero."""
        assert cost_manager.cumulative_cost_usd == 0.0

    def test_node_costs_dict_empty(self, cost_manager):
        """Test that node_costs starts as empty dict."""
        assert isinstance(cost_manager.node_costs, dict)
        assert len(cost_manager.node_costs) == 0


class TestCostEstimation:
    """Test cost estimation logic."""

    def test_estimate_cost_anthropic(self, cost_manager):
        """Test cost estimation for Anthropic models."""
        # Claude Opus: 0.015 per input token, 0.075 per output token
        input_tokens = 1000
        output_tokens = 500

        cost = cost_manager._estimate_cost(
            provider="anthropic",
            model="claude-opus-4-6",
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        expected = (input_tokens * 0.015) + (output_tokens * 0.075)
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_openai(self, cost_manager):
        """Test cost estimation for OpenAI models."""
        # GPT-4o: 0.005 per input, 0.015 per output
        input_tokens = 2000
        output_tokens = 1000

        cost = cost_manager._estimate_cost(
            provider="openai",
            model="gpt-4o",
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        expected = (input_tokens * 0.005) + (output_tokens * 0.015)
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_ollama_free(self, cost_manager):
        """Test that Ollama models have zero cost."""
        cost = cost_manager._estimate_cost(
            provider="ollama",
            model="devstral-2:123b-cloud",
            input_tokens=5000,
            output_tokens=2000
        )

        assert cost == 0.0

    def test_estimate_cost_unknown_model(self, cost_manager):
        """Test cost estimation for unknown model returns 0."""
        cost = cost_manager._estimate_cost(
            provider="anthropic",
            model="unknown-model-xyz",
            input_tokens=1000,
            output_tokens=500
        )

        assert cost == 0.0

    def test_estimate_cost_zero_tokens(self, cost_manager):
        """Test cost with zero tokens."""
        cost = cost_manager._estimate_cost(
            provider="anthropic",
            model="claude-opus-4-6",
            input_tokens=0,
            output_tokens=0
        )

        assert cost == 0.0


class TestBudgetChecking:
    """Test budget limit checking."""

    def test_budget_check_within_limit(self, cost_manager):
        """Test that budget check passes when under limit."""
        cost_manager.cumulative_cost_usd = 5.0

        result = cost_manager._check_budget(
            new_cost=2.0,
            budget_limit=10.0
        )

        assert result is True

    def test_budget_check_exceeds_limit(self, cost_manager):
        """Test that budget check fails when exceeding limit."""
        cost_manager.cumulative_cost_usd = 8.0

        result = cost_manager._check_budget(
            new_cost=5.0,
            budget_limit=10.0
        )

        assert result is False

    def test_budget_check_at_limit(self, cost_manager):
        """Test budget check at exact limit."""
        cost_manager.cumulative_cost_usd = 9.0

        result = cost_manager._check_budget(
            new_cost=1.0,
            budget_limit=10.0
        )

        assert result is True

    def test_budget_check_zero_limit(self, cost_manager):
        """Test budget check with zero limit."""
        result = cost_manager._check_budget(
            new_cost=0.01,
            budget_limit=0.0
        )

        assert result is False

    def test_budget_check_no_limit(self, cost_manager):
        """Test budget check with None limit (unlimited)."""
        cost_manager.cumulative_cost_usd = 1000.0

        result = cost_manager._check_budget(
            new_cost=500.0,
            budget_limit=None
        )

        assert result is True


class TestCostRecording:
    """Test cost recording and tracking."""

    def test_record_cost_single_call(self, cost_manager):
        """Test recording a single cost entry."""
        cost_manager._record_cost(
            node_id="process_data",
            provider="anthropic",
            model="claude-opus-4-6",
            cost=2.50
        )

        assert cost_manager.cumulative_cost_usd == 2.50
        assert "process_data" in cost_manager.node_costs
        assert cost_manager.node_costs["process_data"] == 2.50

    def test_record_cost_accumulation(self, cost_manager):
        """Test that costs accumulate correctly."""
        cost_manager._record_cost("node1", "anthropic", "claude-opus-4-6", 1.0)
        cost_manager._record_cost("node2", "openai", "gpt-4o", 0.5)
        cost_manager._record_cost("node1", "anthropic", "claude-opus-4-6", 0.75)

        assert cost_manager.cumulative_cost_usd == 2.25
        assert cost_manager.node_costs["node1"] == 1.75
        assert cost_manager.node_costs["node2"] == 0.5

    def test_node_costs_tracking(self, cost_manager):
        """Test per-node cost tracking."""
        cost_manager._record_cost("extract", "anthropic", "claude-opus-4-6", 1.20)
        cost_manager._record_cost("analyze", "openai", "gpt-4o", 0.80)
        cost_manager._record_cost("summarize", "anthropic", "claude-opus-4-6", 0.60)

        assert len(cost_manager.node_costs) == 3
        assert cost_manager.node_costs["extract"] == 1.20
        assert cost_manager.node_costs["analyze"] == 0.80
        assert cost_manager.node_costs["summarize"] == 0.60

    def test_record_zero_cost(self, cost_manager):
        """Test recording zero cost (e.g., Ollama)."""
        cost_manager._record_cost("local_process", "ollama", "devstral-2", 0.0)

        assert cost_manager.cumulative_cost_usd == 0.0
        assert cost_manager.node_costs["local_process"] == 0.0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_negative_cost_handled(self, cost_manager):
        """Test that negative costs don't break accumulation."""
        cost_manager._record_cost("node1", "anthropic", "claude-opus-4-6", 5.0)
        # In practice, negative costs shouldn't happen, but test robustness
        cost_manager._record_cost("node2", "anthropic", "claude-opus-4-6", -1.0)

        assert cost_manager.cumulative_cost_usd == 4.0

    def test_very_large_cost(self, cost_manager):
        """Test handling of very large costs."""
        large_cost = 999999.99
        cost_manager._record_cost("expensive_node", "anthropic", "claude-opus-4-6", large_cost)

        assert cost_manager.cumulative_cost_usd == large_cost

    def test_multiple_providers(self, cost_manager):
        """Test mixing multiple providers."""
        cost_manager._record_cost("node1", "anthropic", "claude-opus-4-6", 1.0)
        cost_manager._record_cost("node2", "openai", "gpt-4o", 0.5)
        cost_manager._record_cost("node3", "ollama", "devstral-2", 0.0)

        assert cost_manager.cumulative_cost_usd == 1.5
        assert len(cost_manager.node_costs) == 3

    def test_empty_node_id(self, cost_manager):
        """Test recording cost with empty node ID."""
        cost_manager._record_cost("", "anthropic", "claude-opus-4-6", 1.0)

        assert cost_manager.cumulative_cost_usd == 1.0
        assert "" in cost_manager.node_costs

    def test_cost_precision(self, cost_manager):
        """Test floating-point precision in cost calculations."""
        # Add multiple small costs that might cause floating-point issues
        for i in range(100):
            cost_manager._record_cost(f"node{i}", "openai", "gpt-4o", 0.01)

        expected = 1.0
        assert abs(cost_manager.cumulative_cost_usd - expected) < 0.001
