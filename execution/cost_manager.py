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

Pricing fetched from provider_registry.default.json (source of truth) via get_registry().

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
- Pricing data is fetched from provider_registry.default.json (source of truth)
- Budget constraints are coherent (max_per_task <= max_workflow)
- Token estimates are reasonable approximations

Parameters
----------
None (per-workflow via model_config)

Failure Modes
-------------
- Unknown model Return 0.0 (no pricing available)
- Missing budget config No budget enforcement
- Registry unavailable Return 0.0 for cost estimation

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-24
"""

from utils import BudgetExceededError
from config.provider_registry import get_registry


class CostManager:
	"""Manage cost estimation, budget enforcement, and cost tracking for models."""

	def __init__(self, model_config: dict):
		"""
		Args:
			model_config: Model configuration dict with budget info
		"""
		self.model_config = model_config
		self.cumulative_cost_usd = 0.0
		self.node_costs: dict = {} # node_id -> cost_usd

	def estimate_cost(
		self,
		provider: str,
		model_name: str,
		input_tokens: int,
		output_tokens: int,
	) -> float:
		"""
		Estimate cost of a model call using provider_registry pricing.

		Args:
			provider: Provider name (anthropic, openai, local, devstral_local, etc.)
			model_name: Model name/API ID
			input_tokens: Estimated input tokens
			output_tokens: Estimated output tokens

		Returns:
			Estimated cost in USD (0.0 if pricing not available)
		"""
		# Local/free models have no charge
		if provider in ["devstral_local", "local", "ollama"]:
			return 0.0

		try:
			# Get pricing from registry (source of truth)
			registry = get_registry()
			model_config = registry.get_model(provider, model_name)

			# If model not found in registry, return 0.0
			if not model_config:
				return 0.0

			# Extract pricing from model config
			pricing = model_config.get("pricing", {})
			input_cost_per_1m = pricing.get("input_per_1m_usd")
			output_cost_per_1m = pricing.get("output_per_1m_usd")

			# If pricing not available, return 0.0
			if input_cost_per_1m is None or output_cost_per_1m is None:
				return 0.0

			# Calculate cost based on tokens (pricing is per 1M tokens)
			input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
			output_cost = (output_tokens / 1_000_000) * output_cost_per_1m
			return input_cost + output_cost

		except Exception:
			# If registry is unavailable, return 0.0
			# This allows execution to continue without cost tracking
			return 0.0

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
