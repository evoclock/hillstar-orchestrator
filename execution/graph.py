"""
Script
------
graph.py

Path
----
python/hillstar/graph.py

Purpose
-------
Graph Execution Engine: DAG-based workflow runner with checkpointing.

Implements topological sort, cycle detection, and state management for
directed acyclic graph (DAG) workflows. Supports node execution, checkpoint
creation, and full auditability via trace logging.

Inputs
------
workflow_json (dict): Workflow definition with nodes, edges, state, permissions

Outputs
-------
Workflow execution state (node_outputs, trace, execution_order)

Assumptions
-----------
- Workflow is a valid DAG (no cycles)
- Node inputs can reference previous node outputs via {{ node_id.output }} syntax
- Permissions are specified per node (ask, always, never)
- Checkpoints created at specified nodes only

Parameters
----------
None (class-based)

Failure Modes
-------------
- Cycle detected in graph ValueError
- Invalid node reference KeyError
- Missing required node ValueError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-08 (error detection in execute_node)
"""

import copy
from collections import defaultdict, deque
from typing import Any, Dict, List


class WorkflowGraph:
	"""Directed Acyclic Graph (DAG) workflow executor."""

	def __init__(self, workflow_json: Dict[str, Any]):
		"""
		Args:
			workflow_json: Workflow definition (nodes + edges)
		"""
		self.id = workflow_json.get("id", "unnamed")
		self.nodes = workflow_json["graph"]["nodes"]
		self.edges = workflow_json["graph"]["edges"]
		self.state = workflow_json.get("state", {})
		self.permissions = workflow_json.get("permissions", {})
		# Checkpoints are defined in state.checkpoints (or top-level for backwards compatibility)
		self.checkpoints = (
			self.state.get("checkpoints", [])
			or workflow_json.get("checkpoints", [])
		)

		# Validate DAG (no cycles)
		self._validate_dag()

		# Execution state
		self.execution_order = self._topological_sort()
		self.node_outputs = {}
		self.trace = []

	def _validate_dag(self) -> None:
		"""Ensure workflow is acyclic (DAG)."""
		graph = defaultdict(list)
		for edge in self.edges:
			graph[edge["from"]].append(edge["to"])

		visited = set()
		rec_stack = set()

		def has_cycle(node):
			visited.add(node)
			rec_stack.add(node)

			for neighbor in graph[node]:
				if neighbor not in visited:
					if has_cycle(neighbor):
						return True
				elif neighbor in rec_stack:
					return True

			rec_stack.remove(node)
			return False

		for node in self.nodes:
			if node not in visited:
				if has_cycle(node):
					raise ValueError(f"Workflow contains cycle: {self.id}")

	def _topological_sort(self) -> List[str]:
		"""Return execution order (topological sort)."""
		graph = defaultdict(list)
		in_degree = {node: 0 for node in self.nodes}

		for edge in self.edges:
			graph[edge["from"]].append(edge["to"])
			in_degree[edge["to"]] += 1

		queue = deque([node for node in self.nodes if in_degree[node] == 0])
		result = []

		while queue:
			node = queue.popleft()
			result.append(node)

			for neighbor in graph[node]:
				in_degree[neighbor] -= 1
				if in_degree[neighbor] == 0:
					queue.append(neighbor)

		if len(result) != len(self.nodes):
			raise ValueError("Topological sort failed (cycle detected)")

		return result

	def get_node_inputs(self, node_id: str) -> Any:
		"""Resolve node inputs, substituting references to previous outputs."""
		node = self.nodes[node_id]
		raw_input = node.get("input")

		if raw_input is None:
			return None

		return self._resolve_references(raw_input)

	def _resolve_references(self, obj: Any) -> Any:
		"""Replace {{ node_id.output }} with actual output values (supports partial substitution)."""
		if isinstance(obj, str):
			import re

			# Handle both full and partial template substitution
			def replace_template(match):
				ref = match.group(1).strip()
				if "." in ref:
					node_id, key = ref.split(".", 1)
					if node_id in self.node_outputs:
						output = self.node_outputs[node_id]
						if key == "output":
							# Extract the "output" field if result is a dict
							if isinstance(output, dict) and "output" in output:
								return str(output["output"]) if output["output"] is not None else ""
							return str(output) if output is not None else ""
						elif isinstance(output, dict):
							val = output.get(key)
							return str(val) if val is not None else ""
				return match.group(0) # Return unchanged if not found

			# Replace all {{ ... }} patterns in the string
			return re.sub(r'\{\{\s*([^}]+)\s*\}\}', replace_template, obj)
		elif isinstance(obj, dict):
			return {k: self._resolve_references(v) for k, v in obj.items()}
		elif isinstance(obj, list):
			return [self._resolve_references(item) for item in obj]
		else:
			return obj

	def execute_node(self, node_id: str, executor_fn) -> Any:
		"""Execute a single node."""
		node = self.nodes[node_id]
		tool = node["tool"]
		inputs = self.get_node_inputs(node_id)

		if node_id in self.permissions:
			perm = self.permissions[node_id]
			if perm == "never":
				raise PermissionError(f"Node {node_id} is blocked by permission policy")

		result = executor_fn(node_id, node, inputs)
		self.node_outputs[node_id] = result

		# Check if result contains an error (indicates node execution failure)
		if isinstance(result, dict) and result.get("error"):
			error_msg = result.get("error", "Unknown error")
			raise Exception(f"Node execution error in {node_id}: {error_msg}")

		self.trace.append({
			"node_id": node_id,
			"tool": tool,
			"status": "success",
			"output_keys": list(result.keys()) if isinstance(result, dict) else None
		})

		return result

	def get_execution_order(self) -> List[str]:
		"""Return the order in which nodes should execute."""
		return self.execution_order

	def get_checkpoint_nodes(self) -> List[str]:
		"""Return nodes where checkpoints should be created."""
		return self.checkpoints

	def export_state(self) -> Dict[str, Any]:
		"""Export complete execution state."""
		return {
			"workflow_id": self.id,
			"node_outputs": copy.deepcopy(self.node_outputs),
			"trace": copy.deepcopy(self.trace),
			"execution_order": self.execution_order
		}

	def import_state(self, state: Dict[str, Any]) -> None:
		"""Import execution state from checkpoint for resumption.

		Args:
			state: State dictionary from checkpoint
		"""
		self.node_outputs = copy.deepcopy(state.get("node_outputs", {}))
		self.trace = copy.deepcopy(state.get("trace", []))
