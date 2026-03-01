"""
Script
------
node_executor.py

Path
----
execution/node_executor.py

Purpose
-------
Node Executor: Execute individual workflow nodes with support for model calls, file operations, and scripting.

Extracted from WorkflowRunner to separate node execution logic from orchestration.
Handles model calls with fallback, file read/write, script execution, and git commits.

Inputs
------
node_id (str): Unique node identifier
node (dict): Node definition with tool, parameters, provider, model
inputs (Any): Input data from previous nodes
error_msg (str): Error message to check for fallback triggers
provider (str): Provider name for temperature normalization

Outputs
-------
result (dict): Node execution result with output, error, or return code
node_outputs (dict): Storage for successful node outputs
None (side effects): Executes scripts, writes files, creates commits

Assumptions
-----------
- Model instances are available from ModelFactory
- Node definitions follow workflow schema
- File paths are accessible and writable
- Git is available for commit operations

Parameters
----------
None (per-node via node definition)

Failure Modes
-------------
- Model call fails Fallback to next provider
- File not found Return error dict
- Script timeout Return timeout error
- Git commit fails Return git error
- Unknown tool Return unknown tool error

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
"""

import os
import subprocess
from datetime import datetime
from typing import Any
from .model_selector import ModelFactory
from .cost_manager import CostManager
from .trace import TraceLogger
from config.model_selector import ModelSelector


class NodeExecutor:
	"""Execute individual workflow nodes with comprehensive error handling."""

	def __init__(
		self,
		model_factory: ModelFactory,
		cost_manager: CostManager,
		trace_logger: TraceLogger,
		model_config: dict,
	):
		"""
		Args:
			model_factory: ModelFactory for model instantiation
			cost_manager: CostManager for cost tracking
			trace_logger: TraceLogger for execution logging
			model_config: Model configuration dict
		"""
		self.model_factory = model_factory
		self.cost_manager = cost_manager
		self.trace_logger = trace_logger
		self.model_config = model_config
		self.node_outputs: dict = {} # node_id -> output text

	def execute_node(self, node_id: str, node: dict, inputs: Any) -> dict[str, Any]:
		"""Execute a single node."""
		tool = node["tool"]

		if tool == "model_call":
			return self._execute_model_call(node_id, node, inputs)
		elif tool == "file_read":
			return self._execute_file_read(node_id, node, inputs)
		elif tool == "file_write":
			return self._execute_file_write(node_id, node, inputs)
		elif tool == "script_run":
			return self._execute_script_run(node_id, node, inputs)
		elif tool == "git_commit":
			return self._execute_git_commit(node_id, node, inputs)
		else:
			return {"error": f"Unknown tool: {tool}"}

	def _is_fallback_error(self, error_msg: str) -> bool:
		"""Check if an error is a fallback-triggering error (quota, rate limit, context length)."""
		fallback_keywords = [
			"rate_limit",
			"quota_exceeded",
			"usage_limit",
			"token_limit",
			"context_length",
			"context_too_long",
			"max_tokens",
			"request_too_large",
			"overloaded",
			"service_unavailable",
			"timeout",
			"api call failed", # Transient API errors
			"temporary failure",
			"connection reset",
			"broken pipe",
		]
		error_lower = str(error_msg).lower()
		return any(keyword in error_lower for keyword in fallback_keywords)

	def _normalize_temperature_for_provider(self, provider: str, temperature: float) -> float:
		"""Normalize temperature for provider constraints.

		Some providers have different temperature constraints:
		- OpenAI: Some models only support temperature=1.0 (e.g., gpt-5-nano)
		- Mistral: Supports wider range
		- Anthropic: Supports very low values
		"""
		# OpenAI-based providers should use more reasonable temperatures
		# Most OpenAI models support 0.0-2.0, but some restrict to 1.0
		if provider in ("openai", "openai_mcp"):
			# Clamp to OpenAI's supported range, with slight bias toward 1.0 for compatibility
			if temperature < 0.0:
				return 0.0
			elif temperature > 2.0:
				return 2.0
			# For very low temperatures, use a reasonable default
			elif temperature < 0.1:
				return 1.0 # Use OpenAI's default for restrictive models
			return temperature

		# Other providers can use the provided temperature
		return temperature

	def _get_provider_chain(self, node_id: str, node: dict) -> list:
		"""Build provider chain: explicit/preferred providers first, then fallback chain.

		Fallback allows testing other providers if primary choice fails.
		User's explicit provider choice is always attempted first.
		"""
		preferred = []

		# If node has explicit provider, prioritize it but allow fallback to test others
		if node.get("provider"):
			preferred = [node.get("provider")]

		# If config has provider_preference, use that as secondary preference
		config_prefs = self.model_config.get("provider_preference", [])
		if config_prefs:
			config_preferred = self.model_factory.resolve_provider_preference(config_prefs)
			for p in config_preferred:
				if p not in preferred:
					preferred.append(p)

		# Default fallback chain: Anthropic OpenAI Ollama (incl. Devstral)
		# Note: Mistral (Vibe CLI + API) coming soon
		default_chain = ["anthropic", "openai", "ollama"]

		# Combine: explicit/preferred first, then remaining from default
		chain = preferred.copy()
		for provider in default_chain:
			if provider not in chain:
				chain.append(provider)

		return chain

	def _execute_model_call(self, node_id: str, node: dict, inputs: Any) -> dict:
		"""Execute model call with smart selection, budget checking, and provider fallback.

		Provider fallback chain: Tries providers in order, falling back on quota/rate limit errors.
		Supports automatic file output writing via the 'outputs' field in node definition:
		"outputs": {"output_key": "path/to/file.txt"} will write model output to the file.
		"""
		parameters = node.get("parameters", {})
		prompt = str(inputs) if inputs else ""

		# Get provider chain for fallback
		provider_chain = self._get_provider_chain(node_id, node)
		fallback_attempts = []

		# Try each provider in the chain
		for attempt, provider in enumerate(provider_chain):
			# Select model for this provider
			provider_to_use = provider
			node_copy = node.copy()
			node_copy["provider"] = provider_to_use
			_, model_name = self.model_factory.select_model(node_id, node_copy)

			# Estimate cost for this provider
			input_estimate = len(prompt.split()) * 1.3 # ~1.3 tokens per word
			output_estimate = parameters.get("max_tokens", 4096)
			estimated_cost = self.cost_manager.estimate_cost(
				provider_to_use,
				model_name,
				int(input_estimate),
				output_estimate,
			)

			# Check budget
			try:
				self.cost_manager.check_budget(estimated_cost, node_id)
			except Exception as e:
				# Log error and re-raise (budget errors don't trigger fallback)
				self.trace_logger.log({
					"timestamp": datetime.now().isoformat(),
					"node_id": node_id,
					"status": "budget_exceeded",
					"estimated_cost": estimated_cost,
					"cumulative_cost": self.cost_manager.cumulative_cost_usd,
					"error": str(e),
				})
				raise

			# Get model (pass codex_mcp-specific params if present)
			model_kwargs = {}
			if provider_to_use == "codex_mcp":
				for param in ("sandbox", "approval_policy", "cwd", "timeout"):
					if param in parameters:
						model_kwargs[param] = parameters[param]
			model = self.model_factory.get_model(provider_to_use, model_name, **model_kwargs)

			# Use config temperature or ModelSelector's default
			sampling_params = self.model_config.get("sampling_params", {})
			temperature = parameters.get("temperature")
			if temperature is None:
				temperature = sampling_params.get("temperature", ModelSelector.get_temperature())

			# Adjust temperature for provider constraints
			temperature = self._normalize_temperature_for_provider(provider_to_use, temperature)

			# Call model
			result = model.call(
				prompt=prompt,
				max_tokens=parameters.get("max_tokens", 4096),
				temperature=temperature,
				system=parameters.get("system"),
			)

			# Check for errors in result (e.g., from model provider failures)
			if isinstance(result, dict) and result.get("error"):
				error_msg = result.get("error", "Unknown error")

				# Check if this is a fallback-triggering error
				if self._is_fallback_error(error_msg) and attempt < len(provider_chain) - 1:
					# Log fallback attempt
					next_provider = provider_chain[attempt + 1]
					self.trace_logger.log({
						"timestamp": datetime.now().isoformat(),
						"node_id": node_id,
						"event": "provider_fallback",
						"from_provider": provider_to_use,
						"from_model": model_name,
						"to_provider": next_provider,
						"reason": error_msg,
						"attempt": attempt + 1,
						"total_attempts": len(provider_chain),
					})
					fallback_attempts.append({
						"provider": provider_to_use,
						"error": error_msg,
					})
					# Try next provider
					continue

				# Error is not fallback-triggering or we're out of providers
				# Log final error
				final_log = {
					"timestamp": datetime.now().isoformat(),
					"node_id": node_id,
					"tool": "model_call",
					"provider": provider_to_use,
					"model": model_name,
					"status": "error",
					"error": error_msg,
					"estimated_cost_usd": estimated_cost,
				}
				if fallback_attempts:
					final_log["fallback_attempts"] = fallback_attempts
				self.trace_logger.log(final_log)

				# Return error dict (will be caught by graph.execute_node)
				return result

			# Success - record cost and log
			actual_tokens_used = result.get("tokens_used", 0)
			if actual_tokens_used > 0:
				actual_cost = self.cost_manager.estimate_cost(
					provider_to_use,
					model_name,
					actual_tokens_used // 2, # Rough split (could be refined)
					actual_tokens_used // 2,
				)
			else:
				actual_cost = estimated_cost

			self.cost_manager.record_cost(node_id, actual_cost)

			# Log successful execution (with fallback history if applicable)
			selection_log = {
				"timestamp": datetime.now().isoformat(),
				"node_id": node_id,
				"tool": "model_call",
				"provider": provider_to_use,
				"model": model_name,
				"temperature": temperature,
				"output_length": len(result.get("output", "")),
				"tokens_used": result.get("tokens_used", 0),
				"estimated_cost_usd": estimated_cost,
				"actual_cost_usd": actual_cost,
				"cumulative_cost_usd": self.cost_manager.cumulative_cost_usd,
			}
			if fallback_attempts:
				selection_log["fallback_attempts"] = fallback_attempts

			# Add selection reasoning if enabled
			if self.model_config.get("explainability", {}).get("log_selection_reasoning"):
				selection_log["selection_mode"] = self.model_config.get("mode", "explicit")
				selection_log["complexity_hint"] = node.get("complexity", "moderate")
				selection_log["has_explicit_provider"] = bool(node.get("provider"))
				selection_log["has_explicit_model"] = bool(node.get("model"))

			self.trace_logger.log(selection_log)

			# Handle output file writing for model_call nodes
			outputs_spec = node.get("outputs", {})
			if outputs_spec and isinstance(outputs_spec, dict):
				# Get the model output (typically the main text response)
				model_output = result.get("output", "")

				# Write each output to its specified file path
				for output_key, output_path in outputs_spec.items():
					if output_path and model_output:
						try:
							# Create directories if needed
							os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
							# Write output to file
							with open(output_path, "w") as f:
								f.write(model_output)
							# Log file write in trace
							self.trace_logger.log({
								"timestamp": datetime.now().isoformat(),
								"node_id": node_id,
								"event": "output_file_written",
								"output_key": output_key,
								"file_path": output_path,
								"bytes_written": len(model_output),
							})
						except Exception as e:
							# Log warning but don't fail the workflow
							self.trace_logger.log({
								"timestamp": datetime.now().isoformat(),
								"node_id": node_id,
								"event": "output_file_write_failed",
								"output_key": output_key,
								"file_path": output_path,
								"error": str(e),
							})

			# Store node output for data flow between nodes
			if not result.get("error"):
				self.node_outputs[node_id] = result.get("output", "")

			return result

		# All providers exhausted - should not reach here
		return {
			"error": "All provider fallback attempts exhausted",
			"fallback_attempts": fallback_attempts,
		}

	def _execute_file_read(self, node_id: str, node: dict, inputs: Any) -> dict:
		"""Read file."""
		file_path = inputs if inputs else node.get("parameters", {}).get("path")

		if not file_path:
			return {"error": "file_read requires file path"}

		try:
			with open(file_path) as f:
				content = f.read()
			return {"output": content, "file_path": file_path}
		except Exception as e:
			return {"error": str(e)}

	def _execute_file_write(self, node_id: str, node: dict, inputs: Any) -> dict:
		"""Write file."""
		file_path = node.get("parameters", {}).get("path")
		content = inputs

		if not file_path or content is None:
			return {"error": "file_write requires path and content"}

		try:
			os.makedirs(os.path.dirname(file_path), exist_ok=True)
			with open(file_path, "w") as f:
				f.write(str(content))
			return {"output": f"Wrote {len(content)} bytes to {file_path}"}
		except Exception as e:
			return {"error": str(e)}

	def _execute_script_run(self, node_id: str, node: dict, inputs: Any) -> dict:
		"""Run script with optional working directory support."""
		script = node.get("parameters", {}).get("script")
		cwd = node.get("cwd") # Support cwd parameter for working directory
		timeout = node.get("timeout", 1800) # Default 30 minutes, configurable per node

		if not script:
			return {"error": "script_run requires script parameter"}

		try:
			# Parse script command - if it contains spaces, use shell=True to interpret it
			# Otherwise, assume it's a direct executable path
			use_shell = " " in script or any(c in script for c in ["|", ">", "<", "&"])

			result = subprocess.run(
				script if use_shell else [script],
				input=str(inputs) if inputs else "",
				capture_output=True,
				text=True,
				timeout=timeout,
				cwd=cwd, # Set working directory if specified
				shell=use_shell, # Use shell for complex commands
			)
			return {
				"output": result.stdout,
				"error": result.stderr if result.returncode != 0 else None,
				"return_code": result.returncode,
			}
		except Exception as e:
			return {"error": str(e)}

	def _execute_git_commit(self, node_id: str, node: dict, inputs: Any) -> dict:
		"""Execute git commit with message and optional author/email.

		Note: Uses --no-verify to skip pre-commit hooks since Hillstar itself
		is the authority managing workflow execution governance.
		"""
		message = node.get("parameters", {}).get("message")
		author_name = node.get("parameters", {}).get("author_name", "Claude Code")
		author_email = node.get("parameters", {}).get("author_email", "noreply@anthropic.com")
		cwd = node.get("cwd") # Support working directory specification

		if not message:
			return {"error": "git_commit requires message parameter"}

		try:
			# Stage all changes
			git_add = subprocess.run(
				["git", "add", "-A"],
				capture_output=True,
				text=True,
				timeout=30,
				cwd=cwd,
			)

			if git_add.returncode != 0:
				return {
					"error": f"git add failed: {git_add.stderr}",
					"return_code": git_add.returncode,
				}

			# Commit with author info, skipping pre-commit hook
			# (Hillstar workflow execution IS the governance authority)
			git_commit = subprocess.run(
				[
					"git",
					"commit",
					"-m",
					message,
					f"--author={author_name} <{author_email}>",
					"--no-verify", # Skip pre-commit hook (Hillstar manages governance)
				],
				capture_output=True,
				text=True,
				timeout=30,
				cwd=cwd,
			)

			# If nothing to commit, return success with info
			if "nothing to commit" in git_commit.stderr.lower():
				return {
					"output": "nothing to commit",
					"return_code": 0,
				}

			# If there was an error (other than nothing to commit), return error
			if git_commit.returncode != 0:
				return {
					"error": git_commit.stderr,
					"return_code": git_commit.returncode,
				}

			# Success
			return {
				"output": git_commit.stdout,
				"commit_message": message,
				"author": f"{author_name} <{author_email}>",
				"return_code": 0,
			}

		except Exception as e:
			return {"error": str(e)}
