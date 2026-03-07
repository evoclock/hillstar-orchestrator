"""
Script
------
validator.py

Path
----
python/hillstar/validator.py

Purpose
-------
Workflow validation: Check workflows against schema, registry, and constraints.

Validates:
- JSON schema compliance
- Provider registry integration
- Provider/model availability
- Model configuration coherence
- Budget constraints
- Graph connectivity
- Compliance requirements

Inputs
------
workflow (dict): Workflow JSON
config: HillstarConfig with ProviderRegistry
registry: ProviderRegistry instance

Outputs
-------
(valid: bool, errors: List[str])

Assumptions
-----------
- Workflow is valid JSON
- ProviderRegistry is properly initialized

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-14
"""

import json
import os
from typing import Any, Optional, Tuple
from importlib.resources import files

from config.provider_registry import ProviderRegistry


class WorkflowValidator:
	"""Validate Hillstar workflows against schema, registry, and constraints."""

	@staticmethod
	def _get_schema_path():
		"""Get workflow schema path using importlib (works in installed packages)."""
		try:
			# Python 3.9+ with importlib.resources
			schema_file = files('hillstar.schemas').joinpath('workflow-schema.json')
			return str(schema_file)
		except Exception:
			# Fallback for dev environments
			return os.path.join(
				os.path.dirname(__file__),
				"../../schemas/workflow-schema.json"
			)

	SCHEMA_PATH = None # Set dynamically in load_schema()

	def __init__(self, registry: Optional[ProviderRegistry] = None):
		"""Initialize validator with optional registry."""
		self.registry = registry or ProviderRegistry()

	def load_schema(self) -> dict[str, Any]:
		"""Load the workflow schema (from installed package or dev environment)."""
		schema_path = self._get_schema_path()

		if not os.path.exists(schema_path):
			raise IOError(f"Schema not found: {schema_path}\n"
			f"Ensure python/hillstar/schemas/workflow-schema.json exists")

		with open(schema_path) as f:
			return json.load(f)

	# ==================== JSON Schema Compliance ====================

	def validate_schema(self, workflow: dict[str, Any]) -> Tuple[bool, list[str]]:
		"""
		Validate workflow against JSON schema.

		Args:
			workflow: Workflow dictionary

		Returns:
			(valid: bool, errors: List[str])
		"""
		errors = []

		# Required top-level fields (provider_config is optional --
		# compliance enforcement happens in validate_compliance for
		# cloud providers that require it; local-only workflows
		# do not need provider_config at all)
		required_fields = ["id", "graph"]
		for field in required_fields:
			if field not in workflow:
				errors.append(f"Missing required field: {field}")

		# Validate graph structure
		graph = workflow.get("graph", {})
		if "graph" in workflow:
			if "nodes" not in graph:
				errors.append("Graph missing 'nodes' field")
			if "edges" not in graph:
				errors.append("Graph missing 'edges' field")

		# Validate edges reference valid nodes
		if "nodes" in graph and "edges" in graph:
			node_ids = set(graph["nodes"].keys())
			for edge in graph["edges"]:
				if edge.get("from") not in node_ids:
					errors.append(f"Edge references missing node: {edge.get('from')}")
				if edge.get("to") not in node_ids:
					errors.append(f"Edge references missing node: {edge.get('to')}")

		# Validate each node has a tool
		if "nodes" in graph:
			for node_id, node in graph["nodes"].items():
				if "tool" not in node:
					errors.append(f"Node '{node_id}' missing required 'tool' field")

		return len(errors) == 0, errors

	# ==================== Model Configuration Coherence ====================

	def validate_model_config(
		self,
		model_config: dict[str, Any],
	) -> Tuple[bool, list[str]]:
		"""
		Validate model_config section for coherence.

		Args:
			model_config: The model_config dictionary

		Returns:
			(valid: bool, errors: List[str])
		"""
		errors = []

		if not model_config:
			return True, []

		# Validate mode
		mode = model_config.get("mode", "explicit")
		if mode not in ["explicit", "auto", "preset"]:
			errors.append(f"Invalid mode: {mode}. Must be explicit, auto, or preset")

		# Validate preset if mode=preset
		if mode == "preset":
			preset = model_config.get("preset")
			if not preset:
				errors.append("mode=preset requires 'preset' field")
			else:
				valid_presets = [
					"minimize_cost",
					"balanced",
					"maximize_quality",
					"local_only",
				]
				if preset not in valid_presets:
					errors.append(
						f"Unknown preset: {preset}. "
						f"Valid: {', '.join(valid_presets)}"
					)

		# Validate budget constraints
		budget = model_config.get("budget", {})
		if budget:
			max_per_task = budget.get("max_per_task_usd")
			max_workflow = budget.get("max_workflow_usd")

			if max_per_task and max_workflow:
				if max_per_task > max_workflow:
					errors.append(
						f"max_per_task_usd ({max_per_task}) "
						f"cannot exceed max_workflow_usd ({max_workflow})"
					)

		# Validate provider preferences
		provider_prefs = model_config.get("provider_preferences", {})
		if provider_prefs:
			allowlist = set(provider_prefs.get("allowlist", []))
			blocklist = set(provider_prefs.get("blocklist", []))

			if allowlist and blocklist:
				overlap = allowlist & blocklist
				if overlap:
					errors.append(
						f"Providers in both allowlist and blocklist: {overlap}"
					)

			# Validate providers against registry
			if allowlist:
				available = set(self.registry.list_providers())
				invalid = allowlist - available
				if invalid:
					errors.append(
						f"Unknown providers in allowlist: {', '.join(invalid)}. "
						f"Available: {', '.join(sorted(available))}"
					)

		# Validate sampling params
		sampling = model_config.get("sampling_params", {})
		if sampling:
			temp = sampling.get("temperature")
			if temp is not None:
				if not (0.0 <= temp <= 2.0):
					errors.append(
						f"Invalid temperature: {temp}. Must be 0.0 to 2.0"
					)

			max_tokens = sampling.get("max_tokens")
			if max_tokens is not None and max_tokens < 1:
				errors.append(
					f"Invalid max_tokens: {max_tokens}. Must be >= 1"
				)

		return len(errors) == 0, errors

	# ==================== Graph Connectivity ====================

	def validate_graph_connectivity(
		self,
		workflow: dict[str, Any],
	) -> Tuple[bool, list[str]]:
		"""
		Validate workflow graph connectivity (no disconnected components).

		Args:
			workflow: Workflow dictionary

		Returns:
			(valid: bool, errors: List[str])
		"""
		errors = []

		graph = workflow.get("graph", {})
		nodes = graph.get("nodes", {})
		edges = graph.get("edges", [])

		if not nodes:
			return True, []

		# Build adjacency list
		adj: dict[str, set[str]] = {node_id: set() for node_id in nodes}
		for edge in edges:
			from_node = edge.get("from")
			to_node = edge.get("to")
			if from_node in adj and to_node in adj:
				adj[from_node].add(to_node)
				adj[to_node].add(from_node) # Undirected for connectivity check

		# Find connected components using BFS
		visited = set()
		for start_node in nodes:
			if start_node in visited:
				continue

			# BFS to find component
			component = set()
			queue = [start_node]
			while queue:
				current = queue.pop(0)
				if current in visited:
					continue
				visited.add(current)
				component.add(current)
				for neighbor in adj[current]:
					if neighbor not in visited:
						queue.append(neighbor)

			# Check if component has edges (connected to others)
			isolated_nodes = [n for n in component if not adj[n]]
			if len(component) > 1 and isolated_nodes:
				# Node with no edges in a multi-node component
				errors.append(
					f"Node(s) {isolated_nodes} have no connections in graph"
				)

		# Check for nodes that exist but have no edges at all
		isolated = [n for n, neighbors in adj.items() if not neighbors]
		if len(nodes) > 1 and isolated:
			errors.append(
				f"Isolated nodes (no edges): {', '.join(isolated)}"
			)

		return len(errors) == 0, errors

	# ==================== Provider Registry Integration ====================

	def validate_providers(
		self,
		workflow: dict[str, Any],
	) -> Tuple[bool, list[str]]:
		"""
		Validate all referenced providers and models against registry.

		Args:
			workflow: Workflow dictionary

		Returns:
			(valid: bool, errors: List[str])
		"""
		errors = []

		# Get all available providers from registry
		available_providers = set(self.registry.list_providers())

		# Check model_config for provider preferences
		model_config = workflow.get("model_config", {})
		provider_prefs = model_config.get("provider_preferences", {})
		allowlist = set(provider_prefs.get("allowlist", []))

		if allowlist:
			# Check allowlist only contains valid providers
			invalid = allowlist - available_providers
			if invalid:
				errors.append(
					f"Unknown providers in provider_preferences.allowlist: {invalid}"
				)

		# Validate each node
		graph = workflow.get("graph", {})
		for node_id, node in graph.get("nodes", {}).items():
			if node.get("tool") != "model_call":
				continue

			provider = node.get("provider")
			model = node.get("model")

			if provider:
				# Check provider exists in registry
				if provider not in available_providers:
					errors.append(
						f"Node '{node_id}': Unknown provider '{provider}'"
					)
				else:
					# Provider exists - validate model if specified
					if model:
						provider_config = self.registry.get_provider(provider)
						available_models = set(
							provider_config.get("models", {}).keys() if provider_config else []
						)
						if model not in available_models:
							errors.append(
								f"Node '{node_id}': Unknown model '{model}' "
								f"for provider '{provider}'. "
								f"Available: {', '.join(sorted(available_models))}"
							)

			# Check provider/model compatibility
			if provider and model:
				provider_config = self.registry.get_provider(provider)
				if provider_config:
					models = provider_config.get("models", {})
					if models and model not in models:
						errors.append(
							f"Node '{node_id}': Model '{model}' not in "
							f"provider '{provider}' registry"
						)

		return len(errors) == 0, errors

	# ==================== Compliance Checks ====================

	def validate_compliance(
		self,
		workflow: dict[str, Any],
	) -> Tuple[bool, list[str]]:
		"""
		Validate compliance requirements for all providers.

		Args:
			workflow: Workflow dictionary

		Returns:
			(valid: bool, errors: List[str])
		"""
		issues = []

		# Get workflow's provider config (where users accept compliance requirements)
		workflow_provider_config = workflow.get("provider_config", {})

		for node_id, node in workflow.get("graph", {}).get("nodes", {}).items():
			if node.get("tool") != "model_call":
				continue

			provider = node.get("provider")
			if not provider:
				continue

			provider_registry_config = self.registry.get_provider(provider)
			if not provider_registry_config:
				continue

			compliance = provider_registry_config.get("compliance", {})
			if not compliance:
				continue

			# Get the provider's acceptance config from the workflow
			provider_acceptance = workflow_provider_config.get(provider, {})

			# Check ToS acceptance
			requires_tos = compliance.get("requires_tos_acceptance", False)
			if requires_tos and not provider_acceptance.get("tos_accepted", False):
				issues.append(
					f"Node '{node_id}': Provider '{provider}' requires "
					f"ToS acceptance. See: {compliance.get('tos_url', 'N/A')}"
				)

			# Check audit requirement
			if compliance.get("audit_required", False) and not provider_acceptance.get("audit_enabled", False):
				issues.append(
					f"Node '{node_id}': Provider '{provider}' requires audit logging"
				)

			# Restricted use cases are informational, not blocking
			# (User can acknowledge by setting usage_type in their config)
			restricted = compliance.get("restricted_use_cases", [])
			if restricted and not provider_acceptance.get("restricted_use_acknowledged", False):
				# Only issue warning if not acknowledged
				issues.append(
					f"Node '{node_id}': Provider '{provider}' restricted for: "
					f"{', '.join(restricted)}"
				)

		return len(issues) == 0, issues

	# ==================== Complete Validation ====================

	def validate_complete(
		self,
		workflow: dict[str, Any],
	) -> Tuple[bool, list[str]]:
		"""
		Run all validations.

		Args:
			workflow: Workflow dictionary

		Returns:
			(valid: bool, errors: List[str])
		"""
		all_errors = []

		# Schema validation (JSON structure)
		schema_valid, schema_errors = self.validate_schema(workflow)
		all_errors.extend(schema_errors)

		# Model config validation (coherence)
		model_config = workflow.get("model_config", {})
		config_valid, config_errors = self.validate_model_config(model_config)
		all_errors.extend(config_errors)

		# Graph connectivity
		connectivity_valid, conn_errors = self.validate_graph_connectivity(workflow)
		all_errors.extend(conn_errors)

		# Provider validation (registry integration)
		provider_valid, provider_errors = self.validate_providers(workflow)
		all_errors.extend(provider_errors)

		# Compliance validation
		compliance_valid, compliance_errors = self.validate_compliance(workflow)
		all_errors.extend(compliance_errors)

		return len(all_errors) == 0, all_errors

	@staticmethod
	def validate_file(workflow_path: str) -> Tuple[bool, list[str]]:
		"""
		Validate a workflow file.

		Args:
			workflow_path: Path to workflow.json

		Returns:
			(valid: bool, errors: List[str])
		"""
		try:
			with open(workflow_path) as f:
				workflow = json.load(f)
		except json.JSONDecodeError as e:
			return False, [f"Invalid JSON: {e}"]
		except IOError as e:
			return False, [f"Cannot read file: {e}"]

		return WorkflowValidator.validate_complete_static(workflow)

	# ==================== Static Methods for Backward Compatibility ====================

	@staticmethod
	def validate_schema_static(workflow: dict[str, Any]) -> Tuple[bool, list[str]]:
		"""Static wrapper for validate_schema."""
		return WorkflowValidator().validate_schema(workflow)

	@staticmethod
	def validate_model_config_static(model_config: dict[str, Any]) -> Tuple[bool, list[str]]:
		"""Static wrapper for validate_model_config."""
		return WorkflowValidator().validate_model_config(model_config)

	@staticmethod
	def validate_providers_static(workflow: dict[str, Any]) -> Tuple[bool, list[str]]:
		"""Static wrapper for validate_providers."""
		return WorkflowValidator().validate_providers(workflow)

	@staticmethod
	def validate_complete_static(workflow: dict[str, Any]) -> Tuple[bool, list[str]]:
		"""Static wrapper for validate_complete."""
		return WorkflowValidator().validate_complete(workflow)

	@staticmethod
	def validate_file_static(workflow_path: str) -> Tuple[bool, list[str]]:
		"""Static wrapper for file validation."""
		validator = WorkflowValidator()
		return validator.validate_file(workflow_path)
