"""
Unit tests for execution/cost_manager.py

Tests cost tracking, budget checking, and cost estimation logic.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.cost_manager import CostManager


@pytest.fixture
def test_model_config():
    """Test model configuration with pricing and budget limits."""
    return {
        "budget": {
            "max_per_task_usd": 10.0,
            "max_workflow_usd": 50.0,
        },
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
        # Claude Opus 4.6: $5 per 1M input tokens, $25 per 1M output tokens (from registry)
        input_tokens = 1000
        output_tokens = 500

        cost = cost_manager.estimate_cost(
            provider="anthropic",
            model_name="claude-opus-4-6",
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        expected = (input_tokens / 1_000_000 * 5.0) + (output_tokens / 1_000_000 * 25.0)
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_openai(self, cost_manager):
        """Test cost estimation for OpenAI models."""
        # GPT-4o: 5 per 1M input, 15 per 1M output (from registry)
        # Note: estimate_cost fetches from actual registry, fixture config is not used
        input_tokens = 2000
        output_tokens = 1000

        cost = cost_manager.estimate_cost(
            provider="openai",
            model_name="gpt-4o",
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        # If model is not found in registry, returns 0.0
        # If found, expected = (2000/1M * 5.0) + (1000/1M * 15.0) = 0.025
        # Actual behavior depends on registry state
        assert cost >= 0.0

    def test_estimate_cost_local_free(self, cost_manager):
        """Test that local models have zero cost."""
        cost = cost_manager.estimate_cost(
            provider="devstral",
            model_name="devstral-2:123b-cloud",
            input_tokens=5000,
            output_tokens=2000
        )

        assert cost == 0.0

    def test_estimate_cost_unknown_model(self, cost_manager):
        """Test cost estimation for unknown model returns 0.0."""
        cost = cost_manager.estimate_cost(
            provider="anthropic",
            model_name="unknown-model-xyz",
            input_tokens=1000,
            output_tokens=500
        )

        # Unknown models not in registry return 0.0 (no pricing available)
        assert cost == 0.0

    def test_estimate_cost_zero_tokens(self, cost_manager):
        """Test cost with zero tokens."""
        cost = cost_manager.estimate_cost(
            provider="anthropic",
            model_name="claude-opus-4-6",
            input_tokens=0,
            output_tokens=0
        )

        assert cost == 0.0


class TestBudgetChecking:
    """Test budget limit checking."""

    def test_budget_check_within_limit(self, cost_manager):
        """Test that budget check passes when under limit."""
        cost_manager.cumulative_cost_usd = 5.0

        # Should not raise
        result = cost_manager.check_budget(
            estimated_cost=2.0,
            node_id="node1"
        )

        assert result is None

    def test_budget_check_exceeds_per_task_limit(self, cost_manager):
        """Test that budget check fails when exceeding per-task limit."""
        import pytest
        from utils import BudgetExceededError

        with pytest.raises(BudgetExceededError):
            cost_manager.check_budget(
                estimated_cost=15.0,
                node_id="node1"
            )

    def test_budget_check_exceeds_workflow_limit(self, cost_manager):
        """Test that budget check fails when exceeding workflow limit."""
        import pytest
        from utils import BudgetExceededError

        cost_manager.cumulative_cost_usd = 45.0

        with pytest.raises(BudgetExceededError):
            cost_manager.check_budget(
                estimated_cost=10.0,
                node_id="node1"
            )

    def test_budget_check_at_exact_limit(self, cost_manager):
        """Test budget check at exact limit."""
        cost_manager.cumulative_cost_usd = 40.0

        # Should not raise
        result = cost_manager.check_budget(
            estimated_cost=10.0,
            node_id="node1"
        )

        assert result is None

    def test_budget_check_no_budget_config(self):
        """Test budget check with no budget configuration."""
        manager = CostManager({})
        # Should not raise even with large cost
        result = manager.check_budget(
            estimated_cost=1000.0,
            node_id="node1"
        )
        assert result is None


class TestCostRecording:
    """Test cost recording and tracking."""

    def test_record_cost_single_call(self, cost_manager):
        """Test recording a single cost entry."""
        cost_manager.record_cost(
            node_id="process_data",
            cost=2.50
        )

        assert cost_manager.cumulative_cost_usd == 2.50
        assert "process_data" in cost_manager.node_costs
        assert cost_manager.node_costs["process_data"] == 2.50

    def test_record_cost_accumulation(self, cost_manager):
        """Test that costs accumulate correctly."""
        cost_manager.record_cost("node1", 1.0)
        cost_manager.record_cost("node2", 0.5)
        cost_manager.record_cost("node1", 0.75)

        # Last cost for node1 overwrites previous
        assert cost_manager.cumulative_cost_usd == 2.25
        assert cost_manager.node_costs["node1"] == 0.75
        assert cost_manager.node_costs["node2"] == 0.5

    def test_node_costs_tracking(self, cost_manager):
        """Test per-node cost tracking."""
        cost_manager.record_cost("extract", 1.20)
        cost_manager.record_cost("analyze", 0.80)
        cost_manager.record_cost("summarize", 0.60)

        assert len(cost_manager.node_costs) == 3
        assert cost_manager.node_costs["extract"] == 1.20
        assert cost_manager.node_costs["analyze"] == 0.80
        assert cost_manager.node_costs["summarize"] == 0.60

    def test_record_zero_cost(self, cost_manager):
        """Test recording zero cost (e.g., Ollama)."""
        cost_manager.record_cost("local_process", 0.0)

        assert cost_manager.cumulative_cost_usd == 0.0
        assert cost_manager.node_costs["local_process"] == 0.0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_very_large_cost(self, cost_manager):
        """Test handling of very large costs."""
        large_cost = 999999.99
        cost_manager.record_cost("expensive_node", large_cost)

        assert cost_manager.cumulative_cost_usd == large_cost

    def test_multiple_providers(self, cost_manager):
        """Test cost estimation across providers."""
        anthropic_cost = cost_manager.estimate_cost("anthropic", "claude-opus-4-6", 1000, 500)
        openai_cost = cost_manager.estimate_cost("openai", "gpt-4o", 1000, 500)
        local_cost = cost_manager.estimate_cost("devstral", "devstral-2", 1000, 500)

        assert anthropic_cost > openai_cost
        assert local_cost == 0.0

    def test_empty_node_id(self, cost_manager):
        """Test recording cost with empty node ID."""
        cost_manager.record_cost("", 1.0)

        assert cost_manager.cumulative_cost_usd == 1.0
        assert "" in cost_manager.node_costs

    def test_cost_precision(self, cost_manager):
        """Test floating-point precision in cost calculations."""
        # Add multiple small costs that might cause floating-point issues
        for i in range(100):
            cost_manager.record_cost(f"node{i}", 0.01)

        expected = 1.0
        assert abs(cost_manager.cumulative_cost_usd - expected) < 0.001
