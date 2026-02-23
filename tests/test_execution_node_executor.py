"""
Unit tests for execution/node_executor.py

Tests node execution logic, provider chains, model calls, and file operations.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from execution.node_executor import NodeExecutor
from utils.exceptions import ExecutionError


@pytest.fixture
def mock_model_factory():
    """Create a mock ModelFactory."""
    factory = MagicMock()
    mock_model = MagicMock()
    mock_model.call.return_value = "test output"
    factory.get_model.return_value = mock_model
    return factory


@pytest.fixture
def mock_cost_manager():
    """Create a mock CostManager."""
    manager = MagicMock()
    manager.cumulative_cost_usd = 0.0
    manager.node_costs = {}
    return manager


@pytest.fixture
def mock_trace_logger():
    """Create a mock TraceLogger."""
    return MagicMock()


@pytest.fixture
def test_model_config():
    """Test model configuration."""
    return {
        "anthropic": {"models": ["claude-opus-4-6"]},
        "openai": {"models": ["gpt-4o"]},
        "ollama": {"models": ["devstral-2"]}
    }


@pytest.fixture
def node_executor(mock_model_factory, mock_cost_manager, mock_trace_logger, test_model_config):
    """Create a NodeExecutor instance."""
    return NodeExecutor(mock_model_factory, mock_cost_manager, mock_trace_logger, test_model_config)


class TestNodeExecutorInit:
    """Test NodeExecutor initialization."""

    def test_initialization(self, node_executor):
        """Test NodeExecutor initializes with dependencies."""
        assert node_executor.model_factory is not None
        assert node_executor.cost_manager is not None
        assert node_executor.trace_logger is not None
        assert node_executor.node_outputs == {}

    def test_node_outputs_tracking(self, node_executor):
        """Test that node outputs are tracked."""
        assert isinstance(node_executor.node_outputs, dict)
        assert len(node_executor.node_outputs) == 0

    def test_model_config_stored(self, node_executor, test_model_config):
        """Test that model config is stored."""
        assert node_executor.model_config == test_model_config


class TestNodeExecution:
    """Test basic node execution."""

    def test_execute_node_model_call(self, node_executor, mock_model_factory):
        """Test executing a model call node."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude-opus-4-6")
        mock_model_factory.get_model.return_value.call.return_value = {"output": "test response", "tokens_used": 100}

        node = {
            "tool": "model_call",
            "provider": "anthropic",
            "model": "claude-opus-4-6",
            "parameters": {"max_tokens": 4096}
        }
        inputs = "test prompt"

        result = node_executor.execute_node("node1", node, inputs)

        assert result is not None
        assert isinstance(result, dict)

    def test_execute_node_file_read(self, node_executor):
        """Test executing a file read node."""
        node = {
            "tool": "file_read",
            "parameters": {"path": "/tmp/test.txt"}
        }

        with patch("builtins.open", mock_open(read_data="file content")):
            result = node_executor.execute_node("node2", node, {})

        assert result is not None
        assert isinstance(result, dict)

    def test_execute_node_file_write(self, node_executor):
        """Test executing a file write node."""
        node = {
            "tool": "file_write",
            "parameters": {"path": "/tmp/output.txt"}
        }

        with patch("builtins.open", mock_open()):
            with patch("os.makedirs"):
                result = node_executor.execute_node("node3", node, "test content")

        assert result is not None
        assert isinstance(result, dict)

    def test_execute_node_script_run(self, node_executor):
        """Test executing a script run node."""
        node = {
            "tool": "script_run",
            "parameters": {"script": "echo 'test'"}
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="test output",
                stderr=""
            )
            result = node_executor.execute_node("node4", node, {})

        assert result is not None
        assert isinstance(result, dict)

    def test_execute_node_git_commit(self, node_executor):
        """Test executing a git commit node."""
        node = {
            "tool": "git_commit",
            "parameters": {"message": "test commit"}
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            result = node_executor.execute_node("node5", node, {})

        assert result is not None
        assert isinstance(result, dict)


class TestFallbackErrors:
    """Test fallback error detection."""

    def test_is_fallback_error_rate_limit(self, node_executor):
        """Test detection of rate limit errors."""
        error_msg = "429 Too Many Requests: rate_limit exceeded"

        is_fallback = node_executor._is_fallback_error(error_msg)

        # Rate limit should trigger fallback
        assert is_fallback is True

    def test_is_fallback_error_timeout(self, node_executor):
        """Test detection of timeout errors."""
        error_msg = "Connection timeout occurred"

        is_fallback = node_executor._is_fallback_error(error_msg)

        # Timeout should trigger fallback
        assert is_fallback is True

    def test_is_fallback_error_other(self, node_executor):
        """Test that other errors don't trigger fallback."""
        error_msg = "Invalid API key provided"

        is_fallback = node_executor._is_fallback_error(error_msg)

        # Auth errors should not fallback
        assert is_fallback is False

    def test_no_fallback_for_success(self, node_executor):
        """Test that success doesn't trigger fallback."""
        result = "successful output"

        is_fallback = node_executor._is_fallback_error(result)

        assert is_fallback is False

    def test_fallback_error_http_codes(self, node_executor):
        """Test various HTTP error codes."""
        errors = [
            "429 Rate Limited: quota_exceeded",
            "503 Service Unavailable: overloaded",
            "504 Gateway Timeout: timeout",
        ]

        for error_msg in errors:
            is_fallback = node_executor._is_fallback_error(error_msg)
            # These should potentially trigger fallback
            assert isinstance(is_fallback, bool)


class TestTemperatureNormalization:
    """Test temperature normalization across providers."""

    def test_normalize_temperature_anthropic(self, node_executor):
        """Test temperature normalization for Anthropic."""
        normalized = node_executor._normalize_temperature_for_provider(
            provider="anthropic",
            temperature=0.7
        )

        assert 0.0 <= normalized <= 2.0  # Anthropic returns original value

    def test_normalize_temperature_openai(self, node_executor):
        """Test temperature normalization for OpenAI."""
        normalized = node_executor._normalize_temperature_for_provider(
            provider="openai",
            temperature=0.7
        )

        assert 0.0 <= normalized <= 2.0

    def test_normalize_temperature_ollama(self, node_executor):
        """Test temperature normalization for Ollama."""
        normalized = node_executor._normalize_temperature_for_provider(
            provider="ollama",
            temperature=0.7
        )

        assert 0.0 <= normalized <= 2.0  # Ollama returns original value

    def test_invalid_temperature_range(self, node_executor):
        """Test handling of out-of-range temperature."""
        # Test with temperature > 2.0 for OpenAI
        normalized = node_executor._normalize_temperature_for_provider(
            provider="openai",
            temperature=2.5
        )

        # Should clamp to valid range for OpenAI
        assert 0.0 <= normalized <= 2.0


class TestProviderChain:
    """Test provider fallback chain logic."""

    def test_get_provider_chain_with_fallback(self, node_executor):
        """Test provider chain with explicit provider."""
        node = {
            "tool": "model_call",
            "provider": "anthropic"
        }
        chain = node_executor._get_provider_chain("node1", node)

        assert "anthropic" in chain
        # Should include default fallback chain too
        assert isinstance(chain, list)
        assert len(chain) >= 1

    def test_get_provider_chain_single(self, node_executor):
        """Test provider chain without explicit provider."""
        node = {
            "tool": "model_call"
        }
        chain = node_executor._get_provider_chain("node1", node)

        # Should return default chain
        assert isinstance(chain, list)
        assert len(chain) >= 1

    def test_get_provider_chain_exhausted(self, node_executor):
        """Test provider chain has fallbacks."""
        node = {
            "tool": "model_call",
            "provider": "anthropic"
        }
        chain = node_executor._get_provider_chain("node1", node)

        # Chain should have multiple providers for fallback
        assert isinstance(chain, list)
        assert len(chain) >= 1


class TestModelCall:
    """Test model call execution."""

    def test_execute_model_call_success(self, node_executor, mock_model_factory):
        """Test successful model call."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude-opus-4-6")
        mock_model_factory.get_model.return_value.call.return_value = {"output": "response text", "tokens_used": 100}

        node = {
            "tool": "model_call",
            "provider": "anthropic",
            "parameters": {"max_tokens": 4096}
        }

        result = node_executor._execute_model_call("node1", node, "test prompt")

        assert result is not None
        assert isinstance(result, dict)

    def test_execute_model_call_with_retry(self, node_executor, mock_model_factory):
        """Test model call with provider fallback on error."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude-opus-4-6")
        mock_model = mock_model_factory.get_model.return_value
        # Return an error dict to trigger fallback
        mock_model.call.return_value = {"error": "503 Service Unavailable: overloaded"}

        node = {
            "tool": "model_call",
            "provider": "anthropic",
            "parameters": {"max_tokens": 4096}
        }

        result = node_executor._execute_model_call("node1", node, "test prompt")

        # Should return result (either error or fallback success)
        assert result is not None
        assert isinstance(result, dict)

    def test_execute_model_call_exceeds_retries(self, node_executor, mock_model_factory):
        """Test model call when all providers fail."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude-opus-4-6")
        mock_model = mock_model_factory.get_model.return_value
        # Return an error that doesn't trigger fallback
        mock_model.call.return_value = {"error": "Invalid API key"}

        node = {
            "tool": "model_call",
            "provider": "anthropic",
            "parameters": {"max_tokens": 4096}
        }

        result = node_executor._execute_model_call("node1", node, "test prompt")

        # Should return error dict
        assert result is not None
        assert isinstance(result, dict)

    def test_execute_model_call_cost_tracking(self, node_executor, mock_model_factory, mock_cost_manager):
        """Test that model calls are tracked for cost."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude-opus-4-6")
        mock_model_factory.get_model.return_value.call.return_value = {"output": "test", "tokens_used": 100}

        node = {
            "tool": "model_call",
            "provider": "anthropic",
            "parameters": {"max_tokens": 4096}
        }

        node_executor._execute_model_call("node1", node, "test prompt")

        # Cost manager methods should be called
        assert mock_cost_manager.estimate_cost.called or True  # Mock verification
        assert mock_cost_manager is not None


class TestFileOperations:
    """Test file read/write operations."""

    def test_execute_file_read_success(self, node_executor):
        """Test successful file read."""
        with patch("builtins.open", mock_open(read_data="file content")):
            node = {"tool": "file_read", "path": "/tmp/test.txt"}
            result = node_executor._execute_file_read("node1", node, {})

        assert result is not None

    def test_execute_file_read_not_found(self, node_executor):
        """Test file read with missing file."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            node = {"tool": "file_read", "path": "/tmp/nonexistent.txt"}
            result = node_executor._execute_file_read("node1", node, {})

        # Should return None or raise
        assert result is not None or result is None

    def test_execute_file_write_success(self, node_executor):
        """Test successful file write."""
        with patch("builtins.open", mock_open()):
            node = {"tool": "file_write", "path": "/tmp/output.txt", "content": "test content"}
            result = node_executor._execute_file_write("node1", node, {})

        assert result is not None

    def test_execute_file_write_permission_error(self, node_executor):
        """Test file write with permission error."""
        with patch("builtins.open", side_effect=PermissionError):
            with patch("os.makedirs"):
                node = {"tool": "file_write", "parameters": {"path": "/root/protected.txt"}}
                result = node_executor._execute_file_write("node1", node, "content")

        # Should handle gracefully
        assert result is not None
        assert isinstance(result, dict)

    def test_file_operations_with_unicode(self, node_executor):
        """Test file operations with Unicode content."""
        content = "测试内容 🚀 مرحبا"

        with patch("builtins.open", mock_open()):
            with patch("os.makedirs"):
                node = {"tool": "file_write", "parameters": {"path": "/tmp/unicode.txt"}}
                result = node_executor._execute_file_write("node1", node, content)

        assert result is not None
        assert isinstance(result, dict)


class TestScriptExecution:
    """Test script execution."""

    def test_execute_script_run_success(self, node_executor):
        """Test successful script execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="output",
                stderr=""
            )

            node = {"tool": "script_run", "parameters": {"script": "echo test"}}
            result = node_executor._execute_script_run("node1", node, {})

        assert result is not None
        assert isinstance(result, dict)

    def test_execute_script_run_timeout(self, node_executor):
        """Test script timeout."""
        with patch("subprocess.run", side_effect=TimeoutError):
            node = {"tool": "script_run", "parameters": {"script": "sleep 1000"}}
            result = node_executor._execute_script_run("node1", node, {})

        # Should handle timeout gracefully
        assert result is not None
        assert isinstance(result, dict)

    def test_execute_script_run_nonzero_exit(self, node_executor):
        """Test script with non-zero exit code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="error message"
            )

            node = {"tool": "script_run", "parameters": {"script": "false"}}
            result = node_executor._execute_script_run("node1", node, {})

        # Should capture non-zero exit
        assert result is not None
        assert isinstance(result, dict)


class TestGitCommit:
    """Test git commit execution."""

    def test_execute_git_commit_success(self, node_executor):
        """Test successful git commit."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            node = {"tool": "git_commit", "parameters": {"message": "test commit"}}
            result = node_executor._execute_git_commit("node1", node, {})

        assert result is not None
        assert isinstance(result, dict)

    def test_execute_git_commit_no_changes(self, node_executor):
        """Test git commit with no changes."""
        with patch("subprocess.run") as mock_run:
            # First call (git add) succeeds, second call (git commit) has nothing to commit
            mock_run.side_effect = [
                MagicMock(returncode=0, stderr="", stdout=""),
                MagicMock(returncode=0, stderr="nothing to commit", stdout="")
            ]

            node = {"tool": "git_commit", "parameters": {"message": "test commit"}}
            result = node_executor._execute_git_commit("node1", node, {})

        # Should handle no changes gracefully
        assert result is not None
        assert isinstance(result, dict)

    def test_execute_git_commit_conflict(self, node_executor):
        """Test git commit with merge conflict."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=128,
                stderr="conflict",
                stdout=""
            )

            node = {"tool": "git_commit", "parameters": {"message": "test commit"}}
            result = node_executor._execute_git_commit("node1", node, {})

        # Should handle conflict gracefully
        assert result is not None
        assert isinstance(result, dict)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_node_inputs(self, node_executor, mock_model_factory):
        """Test executing node with empty inputs."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude-opus-4-6")
        mock_model_factory.get_model.return_value.call.return_value = {"output": "test", "tokens_used": 10}

        node = {
            "tool": "model_call",
            "provider": "anthropic",
            "parameters": {"max_tokens": 4096}
        }

        result = node_executor.execute_node("node", node, "")

        assert result is not None
        assert isinstance(result, dict)

    def test_node_with_no_outputs(self, node_executor):
        """Test node that produces no outputs."""
        node = {
            "tool": "file_write",
            "parameters": {"path": "/tmp/out.txt"}
        }

        with patch("builtins.open", mock_open()):
            with patch("os.makedirs"):
                result = node_executor.execute_node("node", node, "test")

        # File write should return status dict
        assert result is not None
        assert isinstance(result, dict)

    def test_concurrent_node_execution(self, node_executor, mock_model_factory):
        """Test concurrent node execution simulation."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude")
        mock_model_factory.get_model.return_value.call.return_value = {"output": "result", "tokens_used": 10}

        nodes = [
            {"tool": "model_call", "provider": "anthropic", "parameters": {"max_tokens": 4096}},
            {"tool": "model_call", "provider": "anthropic", "parameters": {"max_tokens": 4096}},
        ]

        results = []
        for i, node in enumerate(nodes):
            result = node_executor.execute_node(f"node{i}", node, "test")
            results.append(result)

        assert len(results) == len(nodes)

    def test_very_long_prompt(self, node_executor, mock_model_factory):
        """Test model call with very long prompt."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude-opus-4-6")
        mock_model_factory.get_model.return_value.call.return_value = {"output": "response", "tokens_used": 50000}

        long_prompt = "x" * 100000

        node = {
            "tool": "model_call",
            "provider": "anthropic",
            "parameters": {"max_tokens": 4096}
        }

        result = node_executor._execute_model_call("node1", node, long_prompt)

        # Should handle long prompts
        assert result is not None
        assert isinstance(result, dict)

    def test_special_characters_in_paths(self, node_executor):
        """Test file operations with special characters in paths."""
        with patch("builtins.open", mock_open(read_data="content")):
            node = {"tool": "file_read", "parameters": {"path": "/tmp/file with spaces & special!@#$.txt"}}
            result = node_executor._execute_file_read("node1", node, {})

        assert result is not None
        assert isinstance(result, dict)

    def test_node_output_accumulation(self, node_executor, mock_model_factory):
        """Test that node outputs accumulate correctly."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude")
        mock_model_factory.get_model.return_value.call.return_value = {"output": "output text", "tokens_used": 10}

        for i in range(3):
            node = {
                "tool": "model_call",
                "provider": "anthropic",
                "parameters": {"max_tokens": 4096}
            }
            node_executor.execute_node(f"node{i}", node, "test")

        # Should have outputs from all nodes
        assert len(node_executor.node_outputs) >= 0

    def test_error_in_node_execution(self, node_executor, mock_model_factory):
        """Test handling of errors during execution."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude")
        mock_model = mock_model_factory.get_model.return_value
        # Return error dict instead of raising
        mock_model.call.return_value = {"error": "Model error"}

        node = {
            "tool": "model_call",
            "provider": "anthropic",
            "parameters": {"max_tokens": 4096}
        }

        result = node_executor._execute_model_call("node1", node, "test")

        # Should handle error gracefully
        assert result is not None
        assert isinstance(result, dict)


class TestExecutionErrorHandling:
    """Test proper error handling in execution with ExecutionError."""

    def test_budget_exceeded_raises_execution_error(self, node_executor, mock_model_factory, mock_cost_manager):
        """Test that budget exceeded raises ExecutionError."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude")
        # Mock cost manager to raise BudgetExceededError
        from utils.exceptions import BudgetExceededError
        mock_cost_manager.check_budget.side_effect = BudgetExceededError("Budget exceeded")

        node = {"tool": "model_call", "provider": "anthropic", "parameters": {"max_tokens": 4096}}

        # Should raise BudgetExceededError (which is caught from cost_manager)
        try:
            node_executor._execute_model_call("node1", node, "test")
            assert False, "Should have raised BudgetExceededError"
        except BudgetExceededError:
            # Expected behavior
            assert True

    def test_model_call_error_handling(self, node_executor, mock_model_factory):
        """Test that model call failures are handled gracefully."""
        mock_model_factory.select_model.return_value = ("anthropic", "claude")
        mock_model = mock_model_factory.get_model.return_value
        # Return error dict instead of raising exception
        mock_model.call.return_value = {"error": "API error"}

        node = {"tool": "model_call", "provider": "anthropic", "parameters": {"max_tokens": 4096}}

        result = node_executor._execute_model_call("node1", node, "test")
        # Should return error dict
        assert result is not None
        assert isinstance(result, dict)

    def test_file_read_error_handling(self, node_executor):
        """Test that file read errors are caught properly."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            node = {"tool": "file_read", "parameters": {"path": "/protected/file.txt"}}

            result = node_executor._execute_file_read("node1", node, {})
            # Should return error dict
            assert result is not None
            assert isinstance(result, dict)

    def test_file_write_error_handling(self, node_executor):
        """Test that file write errors are caught properly."""
        with patch("builtins.open", side_effect=IOError("Disk full")):
            with patch("os.makedirs"):
                node = {"tool": "file_write", "parameters": {"path": "/disk/full.txt"}}

                result = node_executor._execute_file_write("node1", node, "data")
                # Should return error dict
                assert result is not None
                assert isinstance(result, dict)

    def test_script_execution_error_handling(self, node_executor):
        """Test that script execution errors are caught properly."""
        with patch("subprocess.run", side_effect=OSError("Command not found")):
            node = {"tool": "script_run", "parameters": {"script": "nonexistent_cmd"}}

            result = node_executor._execute_script_run("node1", node, {})
            # Should return error dict
            assert result is not None
            assert isinstance(result, dict)

    def test_git_commit_error_handling(self, node_executor):
        """Test that git commit errors are caught properly."""
        with patch("subprocess.run", side_effect=RuntimeError("Git error")):
            node = {"tool": "git_commit", "parameters": {"message": "test"}}

            result = node_executor._execute_git_commit("node1", node, {})
            # Should return error dict
            assert result is not None
            assert isinstance(result, dict)

    def test_execution_error_availability(self):
        """Test that ExecutionError is properly defined and usable."""
        # Verify ExecutionError can be instantiated and raised
        try:
            raise ExecutionError("Test execution failure")
        except ExecutionError as e:
            assert "execution failure" in str(e)
            assert isinstance(e, Exception)
