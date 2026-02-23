#!/usr/bin/env python3
"""
Design test for execution/checkpoint.py

Tests the CheckpointManager for:
- Creating checkpoints after node completion
- Loading workflow state from checkpoints
- Listing available checkpoints
- Getting latest checkpoint for recovery
"""

import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, '..')

from execution.checkpoint import CheckpointManager


class TestCheckpointManagerDesign:
	"""Design test suite for CheckpointManager."""

	def test_checkpoint_manager_initialization(self):
		"""Test CheckpointManager initializes correctly."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)
			assert manager.output_dir.endswith("checkpoints")

	def test_checkpoint_manager_creates_directory(self):
		"""Test that CheckpointManager creates checkpoints/ subdirectory."""
		with tempfile.TemporaryDirectory() as tmpdir:
			CheckpointManager(tmpdir)
			checkpoints_path = Path(tmpdir) / "checkpoints"
			assert checkpoints_path.exists()

	def test_create_checkpoint(self):
		"""Test creating a checkpoint after node completion."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)
			state = {
				"node_outputs": {"node_1": "output_1"},
				"node_status": {"node_1": "completed"},
				"execution_time": 1.23
			}

			checkpoint_path = manager.create("node_1", state)
			assert Path(checkpoint_path).exists()

	def test_checkpoint_file_contains_valid_json(self):
		"""Test that checkpoint file contains valid JSON."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)
			state = {"test_key": "test_value", "number": 42}

			checkpoint_path = manager.create("node_1", state)

			# Read and verify JSON
			with open(checkpoint_path) as f:
				data = json.load(f)
				assert data["node_id"] == "node_1"
				assert data["state"]["test_key"] == "test_value"

	def test_load_checkpoint(self):
		"""Test loading a checkpoint."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)
			original_state = {
				"node_outputs": {"node_1": "result"},
				"completed_nodes": ["node_1"]
			}

			checkpoint_path = manager.create("node_1", original_state)
			loaded_data = manager.load(checkpoint_path)

			assert loaded_data["state"]["node_outputs"]["node_1"] == "result"
			assert "node_1" in loaded_data["state"]["completed_nodes"]

	def test_create_multiple_checkpoints(self):
		"""Test creating multiple checkpoints for different nodes."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)

			# Create checkpoints for multiple nodes
			state1 = {"node_id": "node_1", "output": "result_1"}
			state2 = {"node_id": "node_2", "output": "result_2"}
			state3 = {"node_id": "node_3", "output": "result_3"}

			path1 = manager.create("node_1", state1)
			path2 = manager.create("node_2", state2)
			path3 = manager.create("node_3", state3)

			# Verify all files exist
			assert Path(path1).exists()
			assert Path(path2).exists()
			assert Path(path3).exists()

	def test_checkpoint_naming_convention(self):
		"""Test that checkpoints follow naming convention."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)
			state = {"test": "data"}

			checkpoint_path = manager.create("node_xyz", state)
			filename = Path(checkpoint_path).name

			# Should follow checkpoint_<node_id>_<timestamp>.json format
			assert filename.startswith("checkpoint_node_xyz")
			assert filename.endswith(".json")

	def test_list_checkpoints(self):
		"""Test listing available checkpoints."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)

			# Create several checkpoints
			for i in range(3):
				manager.create(f"node_{i}", {"step": i})

			checkpoints = manager.list_checkpoints()
			# Should have at least 3 checkpoints
			assert len(checkpoints) >= 3

	def test_get_latest_checkpoint(self):
		"""Test retrieving latest checkpoint for recovery."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)

			# Create multiple checkpoints
			manager.create("node_1", {"step": 1})
			manager.create("node_2", {"step": 2})
			manager.create("node_3", {"step": 3})

			# Get latest checkpoint
			latest = manager.get_latest_checkpoint()
			assert latest is not None
			assert Path(latest).exists()

	def test_get_latest_checkpoint_by_node(self):
		"""Test getting latest checkpoint for specific node."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)

			# Create checkpoints
			manager.create("node_1", {"step": 1})
			manager.create("node_2", {"step": 2})

			# Get checkpoint for specific node
			checkpoint = manager.get_latest_checkpoint(node_id="node_1")
			assert checkpoint is not None

	def test_checkpoint_persists_across_restarts(self):
		"""Test that checkpoint persists across process boundaries."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create checkpoint
			manager1 = CheckpointManager(tmpdir)
			original_state = {"persistent_data": "important_value"}
			checkpoint_path = manager1.create("node_1", original_state)

			# Simulate restart by creating new manager instance
			manager2 = CheckpointManager(tmpdir)
			restored_data = manager2.load(checkpoint_path)

			# Should still have the data
			assert restored_data["state"]["persistent_data"] == "important_value"

	def test_checkpoint_includes_metadata(self):
		"""Test that checkpoint includes timestamp and node_id metadata."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)
			state = {"workflow_id": "wf_001"}

			checkpoint_path = manager.create("node_checkpoint", state)
			loaded_data = manager.load(checkpoint_path)

			# Should have metadata
			assert "timestamp" in loaded_data
			assert loaded_data["node_id"] == "node_checkpoint"
			assert "state" in loaded_data

	def test_empty_checkpoint_list(self):
		"""Test listing checkpoints when none exist."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = CheckpointManager(tmpdir)
			checkpoints = manager.list_checkpoints()

			# Should return empty dict
			assert isinstance(checkpoints, dict)
			assert len(checkpoints) == 0


