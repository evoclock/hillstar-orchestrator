# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Script
------
trace.py

Path
----
python/hillstar/trace.py

Purpose
-------
Trace Logger: Comprehensive audit trail for workflow execution.

Logs all events (node execution, errors, model calls) to JSONL file for auditability
and reproducibility. Timestamps all events automatically.

Inputs
------
output_dir (str): Directory to store trace files

Outputs
-------
Trace file (JSONL): One JSON object per line, each representing an event

Assumptions
-----------
- Output directory exists or can be created
- Write permissions to output_dir

Parameters
----------
None (append-only logging)

Failure Modes
-------------
- No write permissions IOError
- Disk full IOError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-08 (enforce traces/ subdirectory)
"""

import json
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Iterator, List


class TraceLogger:
	"""Log all workflow executions for auditability and reproducibility."""

	def __init__(self, output_dir: str):
		"""
		Args:
			output_dir: Directory to store trace files (will use output_dir/traces/)
		"""
		# Use traces/ subdirectory for organized output
		traces_dir = Path(output_dir) / "traces"
		traces_dir.mkdir(parents=True, exist_ok=True)

		self.output_dir = str(traces_dir)
		self.trace_file = str(
			traces_dir / f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
		)
		self.events: List[Dict] = []
		self._lock = threading.RLock()
		self._local = threading.local()

	def log(self, event: Dict[str, Any]) -> None:
		"""
		Log a single event.

		Worker threads may capture events during concurrent execution. The
		orchestrator commits those buffers in deterministic node order.

		Args:
			event: Event dictionary (will be timestamped if not present)
		"""
		if "timestamp" not in event:
			event["timestamp"] = datetime.now().isoformat()

		buffer = getattr(self._local, "buffer", None)
		if buffer is not None:
			buffer.append(event)
			return

		self._append_events([event])

	@contextmanager
	def capture(self) -> Iterator[List[Dict[str, Any]]]:
		"""Capture events for one worker and return them without writing yet."""
		previous = getattr(self._local, "buffer", None)
		buffer: List[Dict[str, Any]] = []
		self._local.buffer = buffer
		try:
			yield buffer
		finally:
			if previous is None:
				del self._local.buffer
			else:
				self._local.buffer = previous

	def commit(self, events: List[Dict[str, Any]]) -> None:
		"""Append a captured event buffer in the caller's chosen order."""
		if events:
			self._append_events(events)

	def _append_events(self, events: List[Dict[str, Any]]) -> None:
		"""Append events atomically to memory and the JSONL trace."""
		with self._lock:
			self.events.extend(events)
			with open(self.trace_file, "a") as f:
				for event in events:
					f.write(json.dumps(event) + "\n")

	def finalize(self) -> str:
		"""
		Finalize trace and return file path.

		Returns:
			Path to trace file
		"""
		return self.trace_file

	def get_events(self) -> List[Dict]:
		"""Get all logged events."""
		return self.events

	def get_cost_summary(self) -> Dict[str, Any]:
		"""Extract cost summary from logged events."""
		total_cost = 0.0
		node_costs = {}
		model_calls = 0

		for event in self.events:
			if event.get("tool") == "model_call" and "actual_cost_usd" in event:
				node_id = event.get("node_id")
				cost = event.get("actual_cost_usd", 0)
				total_cost += cost
				node_costs[node_id] = cost
				model_calls += 1

		return {
			"total_cost_usd": total_cost,
			"model_calls": model_calls,
			"node_costs": node_costs,
		}
