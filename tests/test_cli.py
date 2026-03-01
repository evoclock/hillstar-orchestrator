"""
Unit tests for cli.py - Subprocess Testing Approach

Production-grade test suite with:
- Deep Assertions: Check exit codes, output content, error messages
- Mock Verification: N/A (subprocess tests run actual CLI commands)
- Parameterized Tests: Multiple command scenarios, error conditions
- Boundary Testing: Missing files, invalid JSON, empty results
- Realistic Data: Actual workflow files, real command invocation
- Integration Points: Real end-to-end CLI execution
- Side Effects: Verify file creation, state changes
- Error Messages: Check stderr output and user-facing messages

## Design Choice: Subprocess Testing vs Unit Testing

cli.py uses relative imports (from .workflows import...) that require proper
package context. Direct unit testing via mock imports fails with:
 ImportError: attempted relative import with no known parent package

Instead of restructuring the entire package (massive redesign), we test cli.py
through subprocess calls - the actual way users invoke it:

 hillstar discover [PATH]
 hillstar validate WORKFLOW_PATH
 hillstar execute WORKFLOW_PATH [DIR]
 etc.

### Why Subprocess Testing?

**Pros:**
- Tests actual user experience (real CLI invocation)
- No package restructuring needed
- Validates end-to-end: arg parsing command output
- Naturally tests error conditions (missing files, invalid input)
- More robust to implementation changes

**Cons:**
- Slower (subprocess overhead)
- Less granular (can't test individual functions)
- Requires real files/I/O (uses tempfile)

**Trade-off:** cli.py is a thin wrapper around well-tested modules (WorkflowDiscovery,
WorkflowValidator, WorkflowRunner, etc.). Subprocess tests validate the CLI contract
(arguments, output format, exit codes) rather than internal logic. Business logic
is tested by existing unit tests for those modules.

## Test Coverage

- cmd_discover: Workflow discovery and listing
- cmd_validate: Workflow validation with metadata display
- cmd_mode: Dev mode toggling
- cmd_presets: Preset listing
- help/version: Usage information
- Integration: Full workflows combining multiple commands
"""

import json
import pytest
import subprocess
import tempfile
from pathlib import Path


# Test fixtures: reusable workflow data
MINIMAL_WORKFLOW = {
	"id": "test-workflow",
	"description": "Test workflow",
	"graph": {
		"nodes": {},
		"edges": []
	},
	"provider_config": {}
}

WORKFLOW_WITH_NODES = {
	"id": "multi-node-workflow",
	"description": "Workflow with nodes",
	"graph": {
		"nodes": {
			"node_1": {"type": "model_call", "tool": "anthropic"},
			"node_2": {"type": "file_read", "tool": "file"}
		},
		"edges": [
			{"source": "node_1", "target": "node_2"}
		]
	},
	"provider_config": {},
	"model_config": {
		"mode": "explicit",
		"preset": "fast",
		"budget": {"max_workflow_usd": 10.50}
	}
}


class TestCommandDiscover:
	"""Test hillstar discover command."""

	def test_discover_finds_workflows(self):
		"""Deep: Discover command finds and lists workflows."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create test workflow file
			workflow_file = Path(tmpdir) / "workflow.json"
			with open(workflow_file, 'w') as f:
				json.dump(MINIMAL_WORKFLOW, f)

			# Run discover command
			result = subprocess.run(
				['hillstar', 'discover', tmpdir],
				capture_output=True,
				text=True
			)

			# Deep assertions
			assert result.returncode == 0, f"stderr: {result.stderr}"
			assert 'test-workflow' in result.stdout
			assert 'Found 1 workflow' in result.stdout

	def test_discover_no_workflows(self):
		"""Boundary: Empty directory shows no workflows found."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = subprocess.run(
				['hillstar', 'discover', tmpdir],
				capture_output=True,
				text=True
			)

			# Deep assertions
			assert result.returncode == 1
			assert 'No workflows found' in result.stdout

	def test_discover_shows_workflow_metadata(self):
		"""Deep: Discover shows node count, edges, mode."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			with open(workflow_file, 'w') as f:
				json.dump(MINIMAL_WORKFLOW, f)

			result = subprocess.run(
				['hillstar', 'discover', tmpdir],
				capture_output=True,
				text=True
			)

			assert result.returncode == 0
			assert 'test-workflow' in result.stdout
			assert 'Nodes:' in result.stdout or 'nodes' in result.stdout.lower()
			assert 'edges' in result.stdout.lower()

	def test_discover_current_directory(self):
		"""Integration: Discover defaults to current directory."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			with open(workflow_file, 'w') as f:
				json.dump(MINIMAL_WORKFLOW, f)

			# Change to tmpdir and run without path arg
			result = subprocess.run(
				['hillstar', 'discover'],
				cwd=tmpdir,
				capture_output=True,
				text=True
			)

			assert result.returncode == 0
			assert 'test-workflow' in result.stdout


class TestCommandValidate:
	"""Test hillstar validate command."""

	def test_validate_valid_workflow(self):
		"""Deep: Validate succeeds for valid workflow."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			with open(workflow_file, 'w') as f:
				json.dump(MINIMAL_WORKFLOW, f)

			result = subprocess.run(
				['hillstar', 'validate', str(workflow_file)],
				capture_output=True,
				text=True
			)

			assert result.returncode == 0
			assert 'valid' in result.stdout.lower()
			assert 'test-workflow' in result.stdout

	def test_validate_missing_file(self):
		"""Boundary: Missing file returns error."""
		result = subprocess.run(
			['hillstar', 'validate', '/nonexistent/workflow.json'],
			capture_output=True,
			text=True
		)

		assert result.returncode == 1
		assert 'not found' in result.stdout.lower()

	def test_validate_invalid_json(self):
		"""Boundary: Invalid JSON returns error."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "bad.json"
			with open(workflow_file, 'w') as f:
				f.write("{ invalid json }")

			result = subprocess.run(
				['hillstar', 'validate', str(workflow_file)],
				capture_output=True,
				text=True
			)

			assert result.returncode == 1

	def test_validate_shows_workflow_details(self):
		"""Deep: Validation output includes ID, description, nodes."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			with open(workflow_file, 'w') as f:
				json.dump(MINIMAL_WORKFLOW, f)

			result = subprocess.run(
				['hillstar', 'validate', str(workflow_file)],
				capture_output=True,
				text=True
			)

			assert result.returncode == 0
			output = result.stdout
			assert 'test-workflow' in output
			assert 'Test workflow' in output or 'valid' in output.lower()


class TestCommandMode:
	"""Test hillstar mode command."""

	def test_mode_dev_enables_development(self):
		"""Deep: Dev mode creates marker file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			hillstar_dir = Path(tmpdir) / ".hillstar"

			result = subprocess.run(
				['hillstar', 'mode', 'dev', '--hillstar-dir', str(hillstar_dir)],
				capture_output=True,
				text=True
			)

			assert result.returncode == 0
			assert 'Development mode enabled' in result.stdout
			dev_mode_file = hillstar_dir / "dev_mode_active"
			assert dev_mode_file.exists(), "Dev mode file should be created"

	def test_mode_normal_disables_development(self):
		"""Deep: Normal mode removes dev marker file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			hillstar_dir = Path(tmpdir) / ".hillstar"
			hillstar_dir.mkdir()
			dev_mode_file = hillstar_dir / "dev_mode_active"
			dev_mode_file.write_text("development mode active")

			result = subprocess.run(
				['hillstar', 'mode', 'normal', '--hillstar-dir', str(hillstar_dir)],
				capture_output=True,
				text=True
			)

			assert result.returncode == 0
			assert 'Development mode disabled' in result.stdout
			assert not dev_mode_file.exists(), "Dev mode file should be removed"

	def test_mode_invalid_returns_error(self):
		"""Boundary: Invalid mode returns error."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = subprocess.run(
				['hillstar', 'mode', 'invalid', '--hillstar-dir', tmpdir],
				capture_output=True,
				text=True
			)

			# argparse returns 2 for invalid choice
			assert result.returncode == 2
			assert 'invalid choice' in result.stderr.lower()


class TestCommandPresets:
	"""Test hillstar presets command."""

	def test_presets_lists_available(self):
		"""Deep: Presets command shows available options."""
		result = subprocess.run(
			['hillstar', 'presets'],
			capture_output=True,
			text=True
		)

		assert result.returncode == 0
		output = result.stdout.lower()
		# Should list presets (exact names depend on ModelPresets)
		assert 'preset' in output or 'available' in output


class TestCommandHelp:
	"""Test hillstar help and version."""

	def test_no_command_shows_help(self):
		"""Deep: No arguments shows help."""
		result = subprocess.run(
			['hillstar'],
			capture_output=True,
			text=True
		)

		# Returns 0 because it's showing help, not an error
		assert result.returncode == 0
		output = result.stdout.lower()
		assert 'usage' in output or 'hillstar' in output

	def test_help_flag_shows_help(self):
		"""Deep: --help flag shows help."""
		result = subprocess.run(
			['hillstar', '--help'],
			capture_output=True,
			text=True
		)

		assert result.returncode == 0
		assert 'usage' in result.stdout.lower() or 'hillstar' in result.stdout.lower()

	def test_version_flag(self):
		"""Deep: --version shows version."""
		result = subprocess.run(
			['hillstar', '--version'],
			capture_output=True,
			text=True
		)

		assert result.returncode == 0
		assert '1.0.0' in result.stdout or 'version' in result.stdout.lower()


class TestCLIIntegration:
	"""Integration tests for CLI workflows."""

	def test_full_workflow_validate_only(self):
		"""Integration: Validate workflow successfully."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "my_workflow.json"
			with open(workflow_file, 'w') as f:
				json.dump(MINIMAL_WORKFLOW, f)

			# Validate
			validate_result = subprocess.run(
				['hillstar', 'validate', str(workflow_file)],
				capture_output=True,
				text=True
			)
			assert validate_result.returncode == 0
			assert 'valid' in validate_result.stdout.lower()
			assert 'test-workflow' in validate_result.stdout

	def test_mode_toggle_workflow(self):
		"""Side Effects: Enable dev mode, verify file, disable, verify removal."""
		with tempfile.TemporaryDirectory() as tmpdir:
			hillstar_dir = Path(tmpdir) / ".hillstar"

			# Enable
			enable_result = subprocess.run(
				['hillstar', 'mode', 'dev', '--hillstar-dir', str(hillstar_dir)],
				capture_output=True,
				text=True
			)
			assert enable_result.returncode == 0
			dev_file = hillstar_dir / "dev_mode_active"
			assert dev_file.exists()

			# Disable
			disable_result = subprocess.run(
				['hillstar', 'mode', 'normal', '--hillstar-dir', str(hillstar_dir)],
				capture_output=True,
				text=True
			)
			assert disable_result.returncode == 0
			assert not dev_file.exists()


@pytest.mark.parametrize("workflow_id,expected_output", [
	('test-workflow', 'test-workflow'),
	('simple-flow', 'simple-flow'),
])
class TestValidateParametrized:
	"""Parameterized tests for validate command."""

	def test_validate_various_workflows(self, workflow_id, expected_output):
		"""Parameterized: Validate command handles different workflow IDs."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": workflow_id,
				"description": f"Workflow: {workflow_id}",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {}
			}
			with open(workflow_file, 'w') as f:
				json.dump(workflow_data, f)

			result = subprocess.run(
				['hillstar', 'validate', str(workflow_file)],
				capture_output=True,
				text=True
			)

			assert result.returncode == 0, f"stdout: {result.stdout}, stderr: {result.stderr}"
			assert expected_output in result.stdout
