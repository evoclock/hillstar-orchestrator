"""
Script
------
checkpoint.py

Path
----
python/hillstar/checkpoint.py

Purpose
-------
Checkpoint Manager: Save and restore workflow state for replay and recovery.

Creates JSON checkpoints after specified nodes complete, allowing workflows
to be resumed from intermediate states. Supports full state export/import.

Inputs
------
output_dir (str): Directory to store checkpoints
node_id (str): Node completing execution
state (dict): Workflow state to save

Outputs
-------
Checkpoint files (JSON): One checkpoint per node

Assumptions
-----------
- Output directory exists or can be created
- Write permissions to output_dir

Parameters
----------
None (per-node checkpointing)

Failure Modes
-------------
- No write permissions IOError
- Corrupt checkpoint file json.JSONDecodeError
- Missing checkpoint FileNotFoundError

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
from datetime import datetime
from typing import Dict, Any, Optional


class CheckpointManager:
	"""Manage workflow checkpoints for replay and recovery."""

	def __init__(self, output_dir: str):
		"""
		Args:
			output_dir: Directory to store checkpoints
		"""
		self.output_dir = os.path.join(output_dir, "checkpoints")
		os.makedirs(self.output_dir, exist_ok=True)

	def create(self, node_id: str, state: Dict[str, Any]) -> str:
		"""
		Create a checkpoint after node execution.

		Args:
			node_id: Node that just completed
			state: Workflow state to save

		Returns:
			Path to checkpoint file
		"""
		checkpoint = {
			"timestamp": datetime.now().isoformat(),
			"node_id": node_id,
			"state": state,
		}

		checkpoint_file = os.path.join(
			self.output_dir,
			f"checkpoint_{node_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
		)

		with open(checkpoint_file, "w") as f:
			json.dump(checkpoint, f, indent=2)

		return checkpoint_file

	def list_checkpoints(self) -> Dict[str, str]:
		"""List all available checkpoints."""
		checkpoints = {}

		for filename in os.listdir(self.output_dir):
			if filename.startswith("checkpoint_") and filename.endswith(".json"):
				filepath = os.path.join(self.output_dir, filename)
				try:
					with open(filepath) as f:
						data = json.load(f)
					node_id = data.get("node_id")
					if node_id:
						checkpoints[node_id] = filepath
				except json.JSONDecodeError:
					pass

		return checkpoints

	def load(self, checkpoint_file: str) -> Dict[str, Any]:
		"""
		Load a checkpoint.

		Args:
			checkpoint_file: Path to checkpoint file

		Returns:
			Checkpoint data
		"""
		with open(checkpoint_file) as f:
			return json.load(f)

	def get_latest_checkpoint(self, node_id: Optional[str] = None) -> Optional[str]:
		"""
		Get most recent checkpoint.

		Args:
			node_id: Optionally filter by node (get all if None)

		Returns:
			Path to latest checkpoint or None
		"""
		checkpoints = self.list_checkpoints()

		if node_id and node_id in checkpoints:
			return checkpoints[node_id]

		if checkpoints:
			latest = max(
				checkpoints.items(),
				key=lambda x: os.path.getmtime(x[1])
			)
			return latest[1]

		return None
