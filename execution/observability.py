"""
Script
------
observability.py

Path
----
python/hillstar/execution/observability.py

Purpose
-------
Comprehensive observability layer for workflow execution with progress tracking,
timestamping, PID logging, hashing, and trace generation.

Inputs
------
- workflow_id (str): Current workflow identifier
- output_dir (str): Directory for logs and traces
- total_nodes (int): Total number of nodes to execute

Outputs
-------
- Real-time progress output to stdout and log files
- Trace file with detailed execution metadata

Assumptions
-----------
- Output directories exist or can be created
- Write permissions to output_dir

Parameters
----------
- verbose: Enable detailed logging
- use_tqdm: Use tqdm progress bars (True by default)

Failure Modes
-------------
- No write permissions → IOError
- Disk full → IOError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-08

Last Edited
-----------
2026-02-17
"""

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


class TqdmFileWrapper:
    """Wrapper that captures tqdm output to log files while displaying on terminal.

    Strips ANSI escape codes before writing to log files for cleaner output,
    while preserving colored/animated bar on stdout/stderr for real-time viewing.
    """

    def __init__(self, log_file_path: Path, audit_log_file_path: Path):
        """Initialize wrapper with log file paths.

        Args:
            log_file_path: Backwards-compat log file location
            audit_log_file_path: Audit directory log file location
        """
        self.log_file = log_file_path
        self.audit_log_file = audit_log_file_path
        # Pattern to match ANSI escape sequences (colors, formatting, cursor control)
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self.original_stderr = sys.stderr

    def write(self, text: str):
        """Write text to log files (with ANSI stripped) and original stderr.

        Args:
            text: Raw text from tqdm (may contain ANSI escape codes)
        """
        # Write colored version to stderr for terminal display
        self.original_stderr.write(text)

        # Strip ANSI codes and write clean version to log files
        clean_text = self.ansi_escape.sub('', text)
        if clean_text.strip():  # Only write non-empty lines
            with open(self.log_file, 'a') as f:
                f.write(clean_text)
            with open(self.audit_log_file, 'a') as f:
                f.write(clean_text)

    def flush(self):
        """Flush the original stderr."""
        self.original_stderr.flush()


class ExecutionObserver:
    """Real-time monitoring and logging of workflow execution."""

    def __init__(
        self,
        workflow_id: str,
        output_dir: str,
        total_nodes: int,
        use_tqdm: bool = True,
    ):
        """
        Initialize execution observer.

        Args:
            workflow_id: Workflow identifier
            output_dir: Base output directory
            total_nodes: Total nodes in workflow
            use_tqdm: Use tqdm progress bars
        """
        self.workflow_id = workflow_id
        self.output_dir = Path(output_dir)
        self.total_nodes = total_nodes
        self.use_tqdm = use_tqdm and HAS_TQDM
        self.pid = os.getpid()
        self.start_time = datetime.now()
        self.workflow_start_epoch = time.time()

        # Extract step number from workflow_id (e.g., "step_04_populate_mpd" → "04")
        self.step_num = self._extract_step_number(workflow_id)

        # Create directories
        self.logs_dir = self.output_dir / "logs"
        self.traces_dir = self.output_dir / "traces"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.traces_dir.mkdir(parents=True, exist_ok=True)

        # Create audit/step_XX/ directory for structured audit trail
        self.audit_dir = self.output_dir / "audit" / f"step_{self.step_num}"
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Log file (both in logs/ for backwards compat and audit/)
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        self.log_file = self.logs_dir / f"execution_{self.workflow_id}_{timestamp}.log"
        self.audit_log_file = self.audit_dir / f"log_{self.step_num}.log"

        # Trace file (detailed execution audit - both locations)
        # Backwards-compat includes step for better discoverability, sorted by timestamp
        self.trace_file = self.traces_dir / f"trace_step_{self.step_num}_{timestamp}.jsonl"
        self.audit_trace_file = self.audit_dir / f"trace_{self.step_num}.jsonl"

        # Initialize progress bar with file wrapper for logging
        self.progress_bar = None
        self.tqdm_wrapper = None
        if self.use_tqdm:
            # Create wrapper that captures tqdm output to log files
            self.tqdm_wrapper = TqdmFileWrapper(self.log_file, self.audit_log_file)
            self.progress_bar = tqdm(
                total=total_nodes,
                desc=f"Executing {workflow_id}",
                unit="node",
                ncols=100,
                bar_format="{desc} |{bar}| [{n_fmt}/{total_fmt}] {postfix}",
                file=self.tqdm_wrapper,  # Direct output to wrapper for logging
            )

        # Node tracking
        self.nodes_completed = 0
        self.nodes_failed = 0
        self.node_times: Dict[str, float] = {}
        self.node_outputs: Dict[str, Dict[str, Any]] = {}

        # Log initialization
        self._log_entry(
            event_type="workflow_start",
            message=f"Workflow execution started: {workflow_id}",
            details={
                "workflow_id": workflow_id,
                "pid": self.pid,
                "timestamp": self.start_time.isoformat(),
                "total_nodes": total_nodes,
            },
        )

        # Print header
        self._print_header()

    @staticmethod
    def _extract_step_number(workflow_id: str) -> str:
        """
        Extract step number from workflow_id.

        Examples:
            "step_04_populate_mpd" → "04"
            "step_05_publication_extraction" → "05"
            "unknown_workflow" → "00"
        """
        match = re.search(r"step_(\d+)", workflow_id)
        return match.group(1) if match else "00"

    def _print_header(self):
        """Print execution header to stdout and log file."""
        separator = "=" * 80
        header_lines = [
            "",
            separator,
            f"[RUN]  Executing: {self.workflow_id}",
            f"[DIR] Output:    {self.output_dir.absolute()}",
            f" PID:       {self.pid}",
            f"⏱ Started:   {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            separator,
            "",
        ]

        # Print to stdout
        for line in header_lines:
            print(line)

        # Also write to log file (human-readable header)
        with open(self.log_file, "a") as f:
            for line in header_lines:
                f.write(line + "\n")

    def node_start(self, node_id: str, node_index: int):
        """Record node execution start."""
        self.node_start_time = time.time()
        self.current_node_id = node_id

        progress_msg = f"[{node_index}/{self.total_nodes}] {node_id}"

        if self.progress_bar:
            self.progress_bar.set_postfix_str(progress_msg)
        else:
            print(f"  {progress_msg}...", end=" ", flush=True)

        self._log_entry(
            event_type="node_start",
            node_id=node_id,
            node_index=node_index,
            details={"epoch_seconds": time.time()},
        )

    def node_success(
        self,
        node_id: str,
        duration_seconds: float,
        output_hash: Optional[str] = None,
        output_summary: Optional[Dict] = None,
    ):
        """Record node execution success."""
        self.nodes_completed += 1
        self.node_times[node_id] = duration_seconds

        if output_summary:
            self.node_outputs[node_id] = output_summary

        if self.progress_bar:
            self.progress_bar.update(1)
        else:
            print(f" ({duration_seconds:.2f}s)")

        self._log_entry(
            event_type="node_success",
            node_id=node_id,
            details={
                "duration_seconds": duration_seconds,
                "output_hash": output_hash,
                "epoch_seconds": time.time(),
                "output_summary": output_summary,
            },
        )

    def node_failure(
        self,
        node_id: str,
        error_msg: str,
        duration_seconds: float,
    ):
        """Record node execution failure."""
        self.nodes_failed += 1
        self.node_times[node_id] = duration_seconds

        if self.progress_bar:
            self.progress_bar.set_postfix_str(f" {node_id}")
        else:
            print(f" Error: {error_msg} ({duration_seconds:.2f}s)")

        self._log_entry(
            event_type="node_failure",
            node_id=node_id,
            details={
                "duration_seconds": duration_seconds,
                "error": error_msg,
                "epoch_seconds": time.time(),
            },
        )

    def workflow_complete(self, cumulative_cost_usd: float = 0.0):
        """Record workflow completion."""
        elapsed = time.time() - self.workflow_start_epoch

        if self.progress_bar:
            self.progress_bar.close()

        # Build summary output (both stdout and log file)
        separator = "=" * 80
        summary_lines = [
            "",
            separator,
            f" Workflow completed: {self.workflow_id}",
            f"   Nodes executed: {self.nodes_completed}/{self.total_nodes}",
        ]
        if self.nodes_failed > 0:
            summary_lines.append(f"   Nodes failed:   {self.nodes_failed}")
        summary_lines.extend([
            f"   Total time:     {elapsed:.2f}s ({elapsed / 60:.2f}m)",
        ])
        if cumulative_cost_usd > 0:
            summary_lines.append(f"   Cost:           ${cumulative_cost_usd:.4f}")

        trace_path = self.trace_file.relative_to(self.output_dir.parent)
        log_path = self.log_file.relative_to(self.output_dir.parent)
        summary_lines.extend([
            f"   Trace file:     {trace_path}",
            f"   Log file:       {log_path}",
            separator,
            "",
        ])

        # Print to stdout
        for line in summary_lines:
            print(line)

        # Also write to log file (human-readable summary)
        with open(self.log_file, "a") as f:
            for line in summary_lines:
                f.write(line + "\n")

        self._log_entry(
            event_type="workflow_complete",
            details={
                "workflow_id": self.workflow_id,
                "nodes_completed": self.nodes_completed,
                "nodes_failed": self.nodes_failed,
                "total_time_seconds": elapsed,
                "cumulative_cost_usd": cumulative_cost_usd,
                "trace_file": str(self.trace_file),
                "log_file": str(self.log_file),
                "node_times": self.node_times,
                "epoch_seconds": time.time(),
            },
        )

        # Write metadata.json to audit directory
        metadata = {
            "workflow_id": self.workflow_id,
            "step_number": self.step_num,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "pid": self.pid,
            "total_nodes": self.total_nodes,
            "nodes_completed": self.nodes_completed,
            "nodes_failed": self.nodes_failed,
            "total_time_seconds": elapsed,
            "cumulative_cost_usd": cumulative_cost_usd,
            "node_times": self.node_times,
            "log_file": str(self.audit_log_file),
            "trace_file": str(self.audit_trace_file),
        }
        metadata_file = self.audit_dir / f"metadata_{self.step_num}.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)


    def workflow_error(self, error_msg: str):
        """Record workflow error."""
        elapsed = time.time() - self.workflow_start_epoch

        if self.progress_bar:
            self.progress_bar.close()

        # Build error summary output (both stdout and log file)
        separator = "=" * 80
        error_lines = [
            "",
            separator,
            f" Workflow failed: {self.workflow_id}",
            f"   Error: {error_msg}",
            f"   Time:  {elapsed:.2f}s",
            f"   Trace: {self.trace_file.relative_to(self.output_dir.parent)}",
            separator,
            "",
        ]

        # Print to stdout
        for line in error_lines:
            print(line)

        # Also write to log file (human-readable error summary)
        with open(self.log_file, "a") as f:
            for line in error_lines:
                f.write(line + "\n")

        self._log_entry(
            event_type="workflow_error",
            details={
                "workflow_id": self.workflow_id,
                "error": error_msg,
                "total_time_seconds": elapsed,
                "nodes_completed": self.nodes_completed,
                "nodes_failed": self.nodes_failed,
                "epoch_seconds": time.time(),
            },
        )

        # Write error metadata.json to audit directory
        metadata = {
            "workflow_id": self.workflow_id,
            "step_number": self.step_num,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "pid": self.pid,
            "total_nodes": self.total_nodes,
            "nodes_completed": self.nodes_completed,
            "nodes_failed": self.nodes_failed,
            "total_time_seconds": elapsed,
            "error": error_msg,
            "node_times": self.node_times,
            "log_file": str(self.audit_log_file),
            "trace_file": str(self.audit_trace_file),
        }
        metadata_file = self.audit_dir / f"metadata_{self.step_num}.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)


    def _log_entry(
        self,
        event_type: str,
        message: Optional[str] = None,
        node_id: Optional[str] = None,
        node_index: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Write event to trace file and log file."""
        timestamp = datetime.now().isoformat()
        epoch = time.time()

        # Build log entry
        entry = {
            "timestamp": timestamp,
            "epoch_seconds": epoch,
            "event_type": event_type,
            "pid": self.pid,
            "workflow_id": self.workflow_id,
        }

        if node_id:
            entry["node_id"] = node_id
        if node_index:
            entry["node_index"] = node_index
        if message:
            entry["message"] = message
        if details:
            entry.update(details)

        # Write to trace file (JSONL format) - both backwards-compat and audit locations
        with open(self.trace_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        with open(self.audit_trace_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Also write to log file (human-readable format) - both locations
        log_line = f"[{timestamp}] {event_type.upper()}"
        if node_id:
            log_line += f" {node_id}"
        if message:
            log_line += f": {message}"
        if details:
            log_line += f" | {json.dumps(details)}"

        with open(self.log_file, "a") as f:
            f.write(log_line + "\n")
        with open(self.audit_log_file, "a") as f:
            f.write(log_line + "\n")

    @staticmethod
    def hash_output(data: Any) -> str:
        """Generate SHA256 hash of output for auditability."""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
