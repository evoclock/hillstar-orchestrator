"""
Script
------
discovery.py

Path
----
python/hillstar/discovery.py

Purpose
-------
Workflow discovery: Find and analyze workflow.json files in project directory.

Scans directory tree for workflow.json files and extracts metadata.
Used by MCP server to discover available workflows.

Inputs
------
start_path (str): Directory to search from (default: current directory)

Outputs
-------
List[str]: Absolute paths to workflow.json files
Dict: Workflow metadata (id, description, nodes, edges)

Assumptions
-----------
- workflow.json files are valid JSON
- Valid according to workflow-schema.json

Parameters
----------
None (per-workflow)

Failure Modes
-------------
- Invalid JSON ValueError
- Missing required fields KeyError
- Unreadable files IOError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
"""

import json
import os
from typing import Any, Dict, List


class WorkflowDiscovery:
	"""Find and analyze Hillstar workflows in a directory tree."""

	@staticmethod
	def find_workflows(
		start_path: str = ".",
		max_depth: int = 5,
	) -> List[str]:
		"""
		Find all workflow.json files in directory tree.

		Args:
			start_path: Directory to search from
			max_depth: Maximum directory depth to search

		Returns:
			List of absolute paths to workflow.json files
		"""
		workflows = []
		start_path = os.path.abspath(start_path)

		for root, dirs, files in os.walk(start_path):
			# Check depth
			depth = root[len(start_path):].count(os.sep)
			if depth > max_depth:
				dirs[:] = [] # Don't recurse further
				continue

			# Skip hidden directories
			dirs[:] = [d for d in dirs if not d.startswith('.')]

			# Look for workflow.json, step_*.json, phase_*.json, pre_phase_*.json
			candidates = []
			if 'workflow.json' in files:
				candidates.append('workflow.json')
			for f in files:
				if f.endswith('.json') and any(
					f.startswith(pfx) for pfx in ('step_', 'phase_', 'pre_phase_')
				):
					candidates.append(f)

			for candidate in candidates:
				workflow_path = os.path.join(root, candidate)
				try:
					if WorkflowDiscovery._is_valid_workflow(workflow_path):
						workflows.append(workflow_path)
				except Exception:
					pass

		return sorted(workflows)

	@staticmethod
	def get_workflow_info(workflow_path: str) -> Dict[str, Any]:
		"""
		Extract metadata from a workflow file.

		Args:
			workflow_path: Absolute path to workflow.json

		Returns:
			Dictionary with workflow metadata

		Raises:
			ValueError: If workflow is invalid
			IOError: If file cannot be read
		"""
		if not os.path.exists(workflow_path):
			raise IOError(f"Workflow file not found: {workflow_path}")

		try:
			with open(workflow_path) as f:
				workflow = json.load(f)
		except json.JSONDecodeError as e:
			raise ValueError(f"Invalid JSON in {workflow_path}: {e}")

		# Extract metadata
		return {
			"path": os.path.abspath(workflow_path),
			"filename": os.path.basename(workflow_path),
			"directory": os.path.dirname(workflow_path),
			"id": workflow.get("id", "unknown"),
			"version": workflow.get("version", "1.0"),
			"description": workflow.get("description", ""),
			"node_count": len(workflow.get("graph", {}).get("nodes", {})),
			"edge_count": len(workflow.get("graph", {}).get("edges", [])),
			"uses_custom_provider": bool(
				workflow.get("model_config", {}).get("custom_providers")
			),
			"preset": workflow.get("model_config", {}).get("preset"),
			"mode": workflow.get("model_config", {}).get("mode", "explicit"),
			"has_budget": bool(
				workflow.get("model_config", {}).get("budget")
			),
			"checkpoints": len(workflow.get("state", {}).get("checkpoints", [])),
		}

	@staticmethod
	def get_all_workflow_info(
		start_path: str = ".",
		max_depth: int = 5,
	) -> List[Dict[str, Any]]:
		"""
		Find all workflows and return their metadata.

		Args:
			start_path: Directory to search from
			max_depth: Maximum directory depth

		Returns:
			List of workflow metadata dictionaries
		"""
		workflows = WorkflowDiscovery.find_workflows(start_path, max_depth)
		info_list = []

		for workflow_path in workflows:
			try:
				info = WorkflowDiscovery.get_workflow_info(workflow_path)
				info_list.append(info)
			except Exception:
				# Skip workflows with errors
				continue

		return info_list

	@staticmethod
	def _is_valid_workflow(workflow_path: str) -> bool:
		"""Check if file looks like a valid workflow."""
		try:
			with open(workflow_path) as f:
				workflow = json.load(f)

			# Minimal validation: has id and graph
			return "id" in workflow and "graph" in workflow
		except Exception:
			return False

	@staticmethod
	def find_in_current_project() -> List[Dict[str, Any]]:
		"""Find all workflows in current project (with .hillstar/ or spec/ indicators)."""
		# Look for indicators of Hillstar project
		current_dir = os.getcwd()

		# Check if we're in a Hillstar project
		has_hillstar_indicators = (
			os.path.exists(os.path.join(current_dir, "python/hillstar/schemas/workflow-schema.json"))
			or os.path.exists(os.path.join(current_dir, ".hillstar"))
			or os.path.exists(os.path.join(current_dir, "workflow.json"))
		)

		if has_hillstar_indicators:
			return WorkflowDiscovery.get_all_workflow_info(current_dir, max_depth=3)
		else:
			# Still look, but don't assume we're in a Hillstar project
			return WorkflowDiscovery.get_all_workflow_info(current_dir, max_depth=2)
