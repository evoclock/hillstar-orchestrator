# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Script
------
runner.py

Path
----
execution/runner.py

Purpose
-------
Workflow Runner: Main orchestration engine with dependency injection.

Executes workflows with full auditability, model selection, checkpoint management,
and trace logging. Uses modular components for cost management, config validation,
model selection, and node execution.

Inputs
------
workflow_path (str): Path to workflow.json file
output_dir (str): Directory for traces and checkpoints

Outputs
-------
Execution result (dict): Final state with workflow_id, status, outputs, trace file, and cost

Assumptions
-----------
- Workflow JSON is valid and follows schema
- Output directory can be created
- Dependencies (checkpoint, trace, graph modules) are available

Parameters
----------
None (via WorkflowRunner constructor)

Failure Modes
-------------
- Invalid workflow JSON JSONDecodeError
- Missing required nodes ExecutionError
- API key unavailable APIKeyError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22 (Refactored with modular components)

Last Edited
-----------
2026-02-22 (Modularized into CostManager, ConfigValidator, ModelFactory, NodeExecutor)
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import json
import os
import time
from threading import Lock
from typing import Any, Optional

from .checkpoint import CheckpointManager
from .graph import WorkflowGraph
from .observability import ExecutionObserver
from .trace import TraceLogger
from .cost_manager import CostManager
from .config_validator import ConfigValidator
from .model_selector import ModelFactory
from .node_executor import NodeExecutor
from .loops import condition_met
from config import HillstarConfig


class WorkflowRunner:
	"""Execute research workflows with full auditability and smart model selection."""

	def __init__(
		self,
		workflow_path: str,
		output_dir: str = "./.hillstar",
		max_concurrency: int | None = None,
	):
		"""
		Args:
			workflow_path: Path to workflow.json file
			output_dir: Directory for traces and checkpoints
			max_concurrency: Maximum number of dependency-ready nodes to run at once
		"""
		# Load .env file so API keys and credentials are available
		ConfigValidator.load_env_file()

		self.workflow_path = workflow_path
		self.output_dir = output_dir
		self._requested_max_concurrency = max_concurrency
		self._single_client_locks: dict[str, Lock] = {}
		self._single_client_locks_guard = Lock()

		# Load workflow
		with open(workflow_path) as f:
			self.workflow_json = json.load(f)

		# Initialize components
		self.graph = WorkflowGraph(self.workflow_json)
		self.trace_logger = TraceLogger(output_dir)
		self.checkpoint_manager = CheckpointManager(output_dir)

		# Compliance tracking
		self._compliance_warnings_issued = False

		# Load and merge configurations
		config_manager = HillstarConfig()
		user_config = config_manager._load_or_init_config()
		workflow_model_config = self.workflow_json.get("model_config", {})
		self.model_config = config_manager.merge_configs(user_config, workflow_model_config)
		configured_concurrency = (
			self._requested_max_concurrency
			if self._requested_max_concurrency is not None
			else self.model_config.get("max_concurrency", 4)
		)
		if (
			isinstance(configured_concurrency, bool)
			or not isinstance(configured_concurrency, int)
			or configured_concurrency < 1
		):
			raise ValueError("max_concurrency must be a positive integer")
		self.max_concurrency = configured_concurrency

		# Initialize modular components with dependency injection
		self.cost_manager = CostManager(self.model_config)
		self.config_validator = ConfigValidator(self.model_config, self.graph, self.trace_logger)
		self.config_validator.validate_model_config()
		self.model_factory = ModelFactory(self.model_config, self.trace_logger, self.config_validator)
		self.node_executor = NodeExecutor(self.model_factory, self.cost_manager, self.trace_logger, self.model_config)

		# Ensure output directory exists and create standard subdirectories
		os.makedirs(output_dir, exist_ok=True)
		self._create_standard_directories(output_dir)

	def _create_standard_directories(self, output_dir: str) -> None:
		"""Create standard .hillstar directory structure."""
		subdirs = ["traces", "logs", "audit", "checkpoints", "data_stores"]
		for subdir in subdirs:
			Path(output_dir, subdir).mkdir(parents=True, exist_ok=True)

	def _extract_step_number(self) -> str | None:
		"""Extract step number from workflow ID."""
		import re
		match = re.match(r"(step_(\d{2})|phase_(\d+)|pre_phase_(\d+))", self.graph.id)
		if match:
			if match.group(2):
				return match.group(2)
			elif match.group(3):
				return match.group(3)
			elif match.group(4):
				return f"pre_{match.group(4)}"
		return None

	def _setup_environment_variables(self) -> None:
		"""Set up environment variables for all executing nodes."""
		output_path = Path(self.output_dir)
		step_num = self._extract_step_number()

		os.environ["HILLSTAR_OUTPUT_DIR"] = str(output_path)
		os.environ["HILLSTAR_TRACES_DIR"] = str(output_path / "traces")
		os.environ["HILLSTAR_LOGS_DIR"] = str(output_path / "logs")
		os.environ["HILLSTAR_CHECKPOINTS_DIR"] = str(output_path / "checkpoints")
		os.environ["HILLSTAR_DATA_STORES_DIR"] = str(output_path / "data_stores")
		os.environ["HILLSTAR_WORKFLOW_ID"] = self.graph.id
		if step_num:
			os.environ["HILLSTAR_STEP"] = step_num
			step_audit_dir = output_path / "audit" / f"step_{step_num}"
			step_audit_dir.mkdir(parents=True, exist_ok=True)
			os.environ["HILLSTAR_AUDIT_DIR"] = str(step_audit_dir)
		else:
			os.environ["HILLSTAR_AUDIT_DIR"] = str(output_path / "audit")

	def _log_compliance_info(self) -> None:
		"""Log compliance information and issue warnings if needed."""
		if self._compliance_warnings_issued:
			return

		compliance_log = {
			"timestamp": datetime.now().isoformat(),
			"event": "compliance_info",
			"message": "Hillstar Compliance Notice",
			"details": {
				"authentication_method": "API_key_based",
				"terminal_pane_status": "not_implemented",
				"orchestration_status": "api_only",
				"user_responsibilities": [
					"Ensure you have accepted all provider Terms of Service",
					"Install provider CLIs separately for manual use",
					"Comply with all provider usage restrictions",
					"Monitor your own compliance with provider terms"
				],
				"platform_responsibilities": [
					"Enforce API authentication for orchestration",
					"Provide cost tracking and budget enforcement",
					"Log compliance-related events"
				],
				"compliance_warnings": [
					"Terminal pane (manual CLI access) not yet implemented",
					"All access currently uses API authentication",
					"Users are responsible for their own provider ToS compliance",
					"Platform provides orchestration services only"
				]
			}
		}

		self.trace_logger.log(compliance_log)
		self._compliance_warnings_issued = True

	def _prepare_concurrent_node(self, node_id: str) -> dict[str, Any]:
		"""Resolve a ready node's inputs without mutating execution state."""
		node = self.graph.nodes[node_id]
		skip_if = node.get("skip_if")
		if skip_if and condition_met(skip_if, self.graph.node_outputs):
			return {
				"node": node,
				"inputs": None,
				"skipped": True,
				"result": self.graph.node_outputs.get(
					skip_if.get("node"), {"skipped": True}
				),
			}

		if self.graph.permissions.get(node_id) == "never":
			raise PermissionError(f"Node {node_id} is blocked by permission policy")

		return {
			"node": node,
			"inputs": self.graph.get_node_inputs(node_id),
			"skipped": False,
		}

	def _single_client_key(self, node: dict[str, Any]) -> str | None:
		"""Return a declared backend key that must be serialized locally.

		Router-routed seats do not declare this metadata in Hillstar; the router
		owns their per-backend queues. Direct/custom workflows may declare
		``singleClient`` on the node or its custom-provider entry.
		"""
		provider = node.get("provider")
		custom_providers = self.model_config.get("custom_providers", {})
		custom = (
			custom_providers.get(provider)
			if isinstance(custom_providers, dict) and provider
			else None
		)
		node_single_client = node.get("singleClient") is True or node.get("single_client") is True
		custom_single_client = isinstance(custom, dict) and (
			custom.get("singleClient") is True or custom.get("single_client") is True
		)
		if not node_single_client and not custom_single_client:
			return None

		backend = (
			node.get("backend_id")
			or node.get("backendId")
			or node.get("backend")
		)
		if backend is None and isinstance(custom, dict):
			backend = custom.get("backend_id") or custom.get("backendId")
		if backend is None and isinstance(custom, dict):
			backend = custom.get("endpoint")
		if backend is None:
			backend = f"{provider}:{node.get('model', '')}"
		return str(backend)

	def _single_client_lock(self, node: dict[str, Any]) -> Lock | None:
		"""Get the process-local lock for a declared single-client backend."""
		key = self._single_client_key(node)
		if key is None:
			return None
		with self._single_client_locks_guard:
			lock = self._single_client_locks.get(key)
			if lock is None:
				lock = Lock()
				self._single_client_locks[key] = lock
			return lock

	def _run_prepared_node(
		self,
		node_id: str,
		node: dict[str, Any],
		inputs: Any,
	) -> dict[str, Any]:
		"""Execute one prepared node and buffer its evidence for ordered commit."""
		started = time.monotonic()
		events: list[dict[str, Any]] = []
		try:
			with self.trace_logger.capture() as captured_events:
				events = captured_events
				lock = self._single_client_lock(node)
				if lock is None:
					result = self.node_executor.execute_node(node_id, node, inputs)
				else:
					with lock:
						result = self.node_executor.execute_node(node_id, node, inputs)
			return {
				"result": result,
				"events": events,
				"duration": time.monotonic() - started,
				"exception": None,
				"skipped": False,
			}
		except Exception as exc:
			self.cost_manager.release_budget(node_id)
			return {
				"result": None,
				"events": events,
				"duration": time.monotonic() - started,
				"exception": exc,
				"skipped": False,
			}

	def _commit_concurrent_node(
		self,
		node_id: str,
		node: dict[str, Any],
		result: Any,
		skipped: bool = False,
	) -> None:
		"""Commit one worker result to graph state in deterministic order."""
		self.graph.node_outputs[node_id] = result
		if skipped:
			self.graph.trace.append({
				"node_id": node_id,
				"tool": node["tool"],
				"status": "skipped",
				"reason": "loop exit condition already met",
			})
			return

		if isinstance(result, dict) and result.get("error"):
			error_msg = result.get("error", "Unknown error")
			raise Exception(f"Node execution error in {node_id}: {error_msg}")

		self.graph.trace.append({
			"node_id": node_id,
			"tool": node["tool"],
			"status": "success",
			"output_keys": list(result.keys()) if isinstance(result, dict) else None,
		})

	def _execute_ready_nodes(
		self,
		execution_order: list[str],
		start_index: int,
		checkpoint_nodes: list[str],
	) -> None:
		"""Execute dependency-ready nodes in bounded, deterministic batches."""
		predecessors = {node_id: set() for node_id in execution_order}
		for edge in self.graph.edges:
			predecessors[edge["to"]].add(edge["from"])

		positions = {node_id: index for index, node_id in enumerate(execution_order)}
		pending = list(execution_order[start_index:])
		completed = set(execution_order[:start_index])
		executor = ThreadPoolExecutor(max_workers=self.max_concurrency)
		active_futures = {}

		try:
			while pending:
				ready = [
					node_id
					for node_id in pending
					if predecessors[node_id].issubset(completed)
				]
				if not ready:
					raise RuntimeError("No dependency-ready nodes remain")

				batch = ready[: self.max_concurrency]
				pending = [node_id for node_id in pending if node_id not in batch]
				outcomes: dict[str, dict[str, Any]] = {}
				active_futures = {}

				for node_id in batch:
					node_index = positions[node_id]
					print(
						f" [{node_index + 1}/{len(execution_order)}] {node_id}...",
						end=" ",
						flush=True,
					)
					self.execution_observer.node_start(node_id, node_index)
					try:
						prepared = self._prepare_concurrent_node(node_id)
					except Exception as exc:
						outcomes[node_id] = {
							"result": None,
							"events": [],
							"duration": 0.0,
							"exception": exc,
							"skipped": False,
						}
						continue

					if prepared["skipped"]:
						outcomes[node_id] = {
							"result": prepared["result"],
							"events": [],
							"duration": 0.0,
							"exception": None,
							"skipped": True,
						}
					else:
						active_futures[node_id] = executor.submit(
							self._run_prepared_node,
							node_id,
							prepared["node"],
							prepared["inputs"],
						)

				for node_id, future in active_futures.items():
					try:
						outcomes[node_id] = future.result()
					except Exception as exc:
						outcomes[node_id] = {
							"result": None,
							"events": [],
							"duration": 0.0,
							"exception": exc,
							"skipped": False,
						}

				# Worker evidence is committed in stable topological order, not
				# completion order.
				for node_id in batch:
					self.trace_logger.commit(outcomes[node_id]["events"])

				failures: list[tuple[str, Exception, float]] = []
				for node_id in batch:
					node = self.graph.nodes[node_id]
					outcome = outcomes[node_id]
					duration = outcome["duration"]
					exception = outcome["exception"]
					if exception is not None:
						print(f" Error: {exception}")
						self.execution_observer.node_failure(
							node_id, str(exception), duration
						)
						failures.append((node_id, exception, duration))
						continue

					try:
						self._commit_concurrent_node(
							node_id,
							node,
							outcome["result"],
							outcome["skipped"],
						)
					except Exception as exc:
						print(f" Error: {exc}")
						self.execution_observer.node_failure(
							node_id, str(exc), duration
						)
						failures.append((node_id, exc, duration))
						continue

					print("")
					self.execution_observer.node_success(node_id, duration)
					completed.add(node_id)
					if node_id in checkpoint_nodes:
						self.checkpoint_manager.create(
							node_id, self.graph.export_state()
						)

				active_futures.clear()
				if failures:
					for node_id, exception, _duration in failures:
						self.trace_logger.log({
							"timestamp": datetime.now().isoformat(),
							"node_id": node_id,
							"status": "error",
							"error": str(exception),
						})
					raise failures[0][1]
		finally:
			for future in active_futures.values():
				future.cancel()
			executor.shutdown(wait=True, cancel_futures=True)

	def execute(self, resume_from: Optional[str] = None) -> dict[str, Any]:
		"""Execute the workflow, optionally resuming from a checkpoint."""
		print(f"Executing workflow: {self.graph.id}")

		execution_order = self.graph.get_execution_order()
		checkpoint_nodes = self.graph.get_checkpoint_nodes()

		self.execution_observer = ExecutionObserver(
			workflow_id=self.graph.id,
			output_dir=self.output_dir,
			total_nodes=len(execution_order),
			use_tqdm=True,
		)

		start_index = 0
		if resume_from:
			checkpoint_file = resume_from
			resume_node_id = None

			if not os.path.exists(resume_from):
				checkpoints = self.checkpoint_manager.list_checkpoints()
				if resume_from in checkpoints:
					checkpoint_file = checkpoints[resume_from]
					resume_node_id = resume_from
				else:
					raise ValueError(f"Checkpoint not found: {resume_from}")
			else:
				checkpoint_data = self.checkpoint_manager.load(checkpoint_file)
				resume_node_id = checkpoint_data.get("node_id")

			if not resume_node_id:
				raise ValueError("Could not determine resume node from checkpoint")

			print(f"Resuming from checkpoint: {resume_node_id}")

			checkpoint_data = self.checkpoint_manager.load(checkpoint_file)
			self.graph.import_state(checkpoint_data["state"])

			try:
				checkpoint_index = execution_order.index(resume_node_id)
				start_index = checkpoint_index + 1
				if start_index >= len(execution_order):
					print(" Workflow already complete (checkpoint was final node)")
					return self._get_execution_result(execution_order)
			except ValueError:
				raise ValueError(f"Checkpoint node not in execution order: {resume_node_id}")

		self._setup_environment_variables()
		self._log_compliance_info()

		try:
			from governance import GovernanceEnforcer
			enforcer = GovernanceEnforcer(self.output_dir)
			enforcer.write_marker(
				workflow_id=self.graph.id,
				workflow_file=self.workflow_path,
				summary="Workflow execution in progress",
			)
		except Exception as e:
			print(f" [governance] Warning: could not write initial marker ({e})")

		try:
			self._execute_ready_nodes(
				execution_order,
				start_index,
				checkpoint_nodes,
			)
		except Exception as exc:
			self.execution_observer.workflow_error(str(exc))
			raise

		self.execution_observer.workflow_complete(self.cost_manager.cumulative_cost_usd)
		return self._get_execution_result(execution_order)

	def _write_step_metadata(self, trace_file: str, execution_order: list) -> None:
		"""Write step metadata and create audit symlinks."""
		step_num = self._extract_step_number()
		if not step_num:
			return

		audit_dir = Path(self.output_dir) / "audit" / f"step_{step_num}"
		audit_dir.mkdir(parents=True, exist_ok=True)

		metadata = {
			"workflow_id": self.graph.id,
			"workflow_file": self.workflow_path,
			"step": step_num,
			"status": "success",
			"executed_at": datetime.now().isoformat(),
			"nodes_executed": len(execution_order),
			"total_nodes": len(execution_order),
			"cumulative_cost_usd": self.cost_manager.cumulative_cost_usd,
			"trace_file": trace_file,
		}

		metadata_file = audit_dir / "metadata.json"
		with open(metadata_file, "w") as f:
			json.dump(metadata, f, indent=2)

		trace_link = audit_dir / f"trace_{step_num}.jsonl"
		trace_link.unlink(missing_ok=True)
		trace_link.symlink_to(Path(trace_file).resolve())

		logs_dir = Path(self.output_dir) / "logs"
		if logs_dir.exists():
			log_files = sorted(logs_dir.glob(f"*{step_num}*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
			if log_files:
				log_link = audit_dir / f"log_{step_num}.log"
				log_link.unlink(missing_ok=True)
				log_link.symlink_to(log_files[0].resolve())

	def _get_execution_result(self, execution_order: list) -> dict[str, Any]:
		"""Generate execution result and finalize workflow."""
		final_state = self.graph.export_state()
		trace_file = self.trace_logger.finalize()

		if self.model_config.get("explainability", {}).get("log_cost_estimates"):
			budget = self.model_config.get("budget", {})
			max_workflow = budget.get("max_workflow_usd")

			summary = {
				"timestamp": datetime.now().isoformat(),
				"type": "budget_summary",
				"cumulative_cost_usd": self.cost_manager.cumulative_cost_usd,
				"node_costs": self.cost_manager.node_costs,
			}

			if max_workflow:
				remaining = max_workflow - self.cost_manager.cumulative_cost_usd
				summary["max_workflow_usd"] = max_workflow
				summary["remaining_budget_usd"] = remaining
				summary["utilization_percent"] = (self.cost_manager.cumulative_cost_usd / max_workflow) * 100

			self.trace_logger.log(summary)

		print("\n Workflow completed")
		print(f" Trace: {trace_file}")
		if self.cost_manager.cumulative_cost_usd > 0:
			print(f" Cost: ${self.cost_manager.cumulative_cost_usd:.4f}")

		try:
			from governance import GovernanceEnforcer
			enforcer = GovernanceEnforcer(self.output_dir)
			enforcer.write_marker(
				workflow_id=self.graph.id,
				workflow_file=self.workflow_path,
				summary=f"{len(execution_order)} nodes executed",
			)
			print(" Governance: commit_ready marker written")
		except Exception as e:
			print(f" Governance: warning — could not write marker ({e})")

		try:
			self._write_step_metadata(trace_file, execution_order)
		except Exception as e:
			print(f" Audit: warning — could not write metadata ({e})")

		return {
			"workflow_id": self.graph.id,
			"status": "success",
			"outputs": final_state["node_outputs"],
			"trace_file": trace_file,
			"cumulative_cost_usd": self.cost_manager.cumulative_cost_usd,
		}
