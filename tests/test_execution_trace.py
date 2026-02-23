#!/usr/bin/env python3
"""
Design test for execution/trace.py

Tests the TraceLogger for:
- Event logging to JSONL files
- Automatic timestamping
- Cost summary extraction
- Event retrieval
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.trace import TraceLogger


class TestTraceLoggerDesign:
	"""Design test suite for TraceLogger."""

	def test_trace_logger_initialization(self):
		"""Test TraceLogger initializes correctly."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)
			assert logger.output_dir.endswith("traces")
			assert logger.events == []

	def test_trace_logger_creates_traces_directory(self):
		"""Test that TraceLogger creates traces/ subdirectory."""
		with tempfile.TemporaryDirectory() as tmpdir:
			TraceLogger(tmpdir)
			traces_path = Path(tmpdir) / "traces"
			assert traces_path.exists()

	def test_log_single_event(self):
		"""Test logging a single event."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)
			event = {"event_type": "node_execution", "node_id": "node_1"}
			logger.log(event)

			# Verify event was recorded
			assert len(logger.events) == 1
			assert logger.events[0]["event_type"] == "node_execution"
			# Verify timestamp was added
			assert "timestamp" in logger.events[0]

	def test_log_event_with_timestamp(self):
		"""Test that events get automatic timestamp if not provided."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)
			event = {"tool": "model_call"}
			logger.log(event)

			# Should have timestamp
			assert "timestamp" in logger.events[0]
			# Should be valid ISO format
			datetime.fromisoformat(logger.events[0]["timestamp"])

	def test_log_event_preserves_existing_timestamp(self):
		"""Test that existing timestamp is preserved."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)
			existing_time = "2026-02-23T12:00:00"
			event = {"tool": "model_call", "timestamp": existing_time}
			logger.log(event)

			# Should preserve original timestamp
			assert logger.events[0]["timestamp"] == existing_time

	def test_trace_file_creation(self):
		"""Test that trace file is created and contains JSONL."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)
			event = {"event": "test"}
			logger.log(event)

			# Verify file exists
			trace_file = Path(logger.finalize())
			assert trace_file.exists()

			# Verify file contains JSON
			with open(trace_file) as f:
				line = f.readline()
				data = json.loads(line)
				assert data["event"] == "test"

	def test_multiple_events_logged(self):
		"""Test logging multiple events."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)

			for i in range(5):
				event = {"event_id": i, "node_id": f"node_{i}"}
				logger.log(event)

			# Verify all events recorded
			assert len(logger.events) == 5
			assert logger.events[0]["event_id"] == 0
			assert logger.events[4]["event_id"] == 4

	def test_get_events(self):
		"""Test retrieving all logged events."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)
			logger.log({"event": "event1"})
			logger.log({"event": "event2"})

			events = logger.get_events()
			assert len(events) == 2
			assert events[0]["event"] == "event1"
			assert events[1]["event"] == "event2"

	def test_cost_summary_extraction(self):
		"""Test extracting cost summary from events."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)

			# Log model call events with costs
			logger.log({
				"tool": "model_call",
				"node_id": "node_1",
				"actual_cost_usd": 0.05
			})
			logger.log({
				"tool": "model_call",
				"node_id": "node_2",
				"actual_cost_usd": 0.03
			})
			logger.log({
				"tool": "file_operation",
				"node_id": "node_3"
				# No cost
			})

			summary = logger.get_cost_summary()
			assert summary["total_cost_usd"] == 0.08
			assert summary["model_calls"] == 2
			assert "node_1" in summary["node_costs"]
			assert summary["node_costs"]["node_1"] == 0.05

	def test_cost_summary_empty(self):
		"""Test cost summary with no model calls."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)
			logger.log({"tool": "file_operation", "node_id": "node_1"})

			summary = logger.get_cost_summary()
			assert summary["total_cost_usd"] == 0.0
			assert summary["model_calls"] == 0
			assert summary["node_costs"] == {}

	def test_finalize_returns_file_path(self):
		"""Test that finalize returns trace file path."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)
			logger.log({"event": "test"})

			path = logger.finalize()
			assert isinstance(path, str)
			assert path.endswith(".jsonl")
			assert Path(path).exists()

	def test_jsonl_format_persisted(self):
		"""Test that events are persisted in valid JSONL format."""
		with tempfile.TemporaryDirectory() as tmpdir:
			logger = TraceLogger(tmpdir)

			# Log multiple events
			events_to_log = [
				{"event": "event1", "value": 1},
				{"event": "event2", "value": 2},
				{"event": "event3", "value": 3}
			]

			for event in events_to_log:
				logger.log(event)

			trace_file = logger.finalize()

			# Verify JSONL format - one JSON object per line
			with open(trace_file) as f:
				lines = f.readlines()
				assert len(lines) == 3

				for i, line in enumerate(lines):
					data = json.loads(line)
					assert data["event"] == f"event{i+1}"


