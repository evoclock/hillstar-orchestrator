"""
Script
------
cost_manager.py

Path
----
execution/cost_manager.py

Purpose
-------
Cost Manager: Handle cost estimation, budget checking, and cost tracking for workflow execution.

Extracted from WorkflowRunner to enable modular unit testing and cost policy changes
without affecting node execution or model selection logic.

Inputs
------
model_config (dict): Model configuration with pricing and budget information
provider (str): Provider name (anthropic, openai, local, devstral, etc.)
model_name (str): Model identifier
input_tokens (int): Estimated input tokens for cost calculation
output_tokens (int): Estimated output tokens for cost calculation
estimated_cost (float): Cost to check against budget limits
node_id (str): Node identifier for error reporting
cost (float): Actual cost to record

Outputs
-------
estimated_cost (float): USD cost estimate for model call
None (methods modify internal state): cumulative_cost_usd, node_costs dict

Assumptions
-----------
- Pricing data is accurate and up-to-date
- Budget constraints are coherent (max_per_task <= max_workflow)
- Token estimates are reasonable approximations

Parameters
----------
None (per-workflow via model_config)

Failure Modes
-------------
- Unknown model → Use fallback pricing
- Missing budget config → No budget enforcement
- Negative costs → Treated as 0.0

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
"""

from utils import BudgetExceededError


class CostManager:
    """Manage cost estimation, budget enforcement, and cost tracking for models."""

    def __init__(self, model_config: dict):
        """
        Args:
            model_config: Model configuration dict with pricing and budget info
        """
        self.model_config = model_config
        self.cumulative_cost_usd = 0.0
        self.node_costs: dict = {}  # node_id -> cost_usd

    def estimate_cost(
        self,
        provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Estimate cost of a model call.

        Args:
            provider: Provider name (anthropic, openai, local, devstral)
            model_name: Model name
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens

        Returns:
            Estimated cost in USD
        """
        # Pricing per 1M tokens
        pricing = {
            "claude-haiku-4-5": {"input": 0.80, "output": 4.0},
            "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
            "claude-opus-4-6": {"input": 15.0, "output": 75.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-4o": {"input": 5.0, "output": 15.0},
        }

        # Local/free models
        if provider in ["devstral", "local", "ollama"]:
            return 0.0

        # Get pricing for model
        model_pricing = pricing.get(model_name)
        if not model_pricing:
            # Fallback pricing for unknown models
            if provider == "openai":
                model_pricing = {"input": 5.0, "output": 15.0}
            else:
                model_pricing = {"input": 3.0, "output": 15.0}

        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        return input_cost + output_cost

    def check_budget(
        self,
        estimated_cost: float,
        node_id: str,
    ) -> None:
        """
        Check if cost would exceed budget limits.

        Args:
            estimated_cost: Estimated cost of this call in USD
            node_id: Node ID for logging

        Raises:
            BudgetExceededError: If budget would be exceeded
        """
        budget = self.model_config.get("budget", {})
        max_per_task = budget.get("max_per_task_usd")
        max_workflow = budget.get("max_workflow_usd")

        if max_per_task and estimated_cost > max_per_task:
            raise BudgetExceededError(
                f"Node {node_id}: estimated cost ${estimated_cost:.4f} "
                f"exceeds per-task limit ${max_per_task}"
            )

        if max_workflow and (self.cumulative_cost_usd + estimated_cost) > max_workflow:
            remaining = max_workflow - self.cumulative_cost_usd
            raise BudgetExceededError(
                f"Node {node_id}: estimated cost ${estimated_cost:.4f} "
                f"would exceed workflow limit. Remaining: ${remaining:.4f}"
            )

    def record_cost(self, node_id: str, cost: float) -> None:
        """Record actual cost for a node."""
        self.node_costs[node_id] = cost
        self.cumulative_cost_usd += cost
