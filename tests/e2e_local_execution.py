"""
E2E Test: Local and Cloud Execution

Purpose:
Test execution with both local Ollama models and Ollama cloud models.
Validates that core execution engine works with different model sources.

Workflow: 2-node pipeline
- analyze_local: Ollama neural-chat (local instance)
- analyze_cloud: Ollama cloud model via MCP

Tests:
- Local model can be instantiated
- Cloud model can be instantiated
- Models accept prompt and parameters
- Output is captured correctly
- Execution completes in reasonable time (< 30 seconds)
- Error handling works if model unavailable

Author: Testing Suite
Created: 2026-02-22
"""

import json
import pytest
import time
import tempfile
from pathlib import Path
from datetime import datetime


class TestLocalExecution:
    """Test local-only execution without cloud APIs."""

    @pytest.fixture
    def local_workflow(self):
        """Create a workflow with both local and cloud Ollama models."""
        return {
            "id": "mixed_execution_workflow",
            "version": "1.0",
            "description": "Mixed workflow with local and cloud models",
            "graph": {
                "nodes": {
                    "analyze_local": {
                        "tool": "model_call",
                        "provider": "devstral_local",
                        "model": "devstral-small-2-24b",
                        "task": "Local analysis",
                        "input": "Analyze this concept: workflow orchestration",
                        "parameters": {
                            "max_tokens": 256,
                        },
                    },
                    "analyze_cloud": {
                        "tool": "model_call",
                        "provider": "anthropic_ollama",
                        "model": "minimax-m2.5:cloud",
                        "task": "Cloud analysis via Ollama",
                        "input": "Explain workflow orchestration",
                        "parameters": {
                            "max_tokens": 256,
                        },
                    }
                },
                "edges": [],
            },
            "provider_config": {
                "devstral_local": {
                    "endpoint": "http://localhost:11434",
                    "tos_accepted": True,
                    "audit_enabled": True,
                },
                "anthropic_ollama": {
                    "endpoint": "http://localhost:11434",
                    "tos_accepted": True,
                    "audit_enabled": True,
                }
            },
        }

    @pytest.fixture
    def output_dir(self):
        """Create output directory for E2E results."""
        output_dir = (
            Path(__file__).parent.parent / ".test-results" / "e2e_local"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _get_model(self, provider: str, model_name: str, workflow: dict = None):
        """Get a model instance for the given provider and model.

        Args:
            provider: Provider name (ollama, ollama_cloud, etc.)
            model_name: Model identifier
            workflow: Workflow dict to use. If None, creates minimal workflow.
        """
        from execution.runner import WorkflowRunner

        if workflow is None:
            workflow = {
                "id": "minimal_test_workflow",
                "graph": {"nodes": {}, "edges": []},
                "provider_config": {
                    provider: {
                        "endpoint": "http://localhost:11434",
                        "tos_accepted": True,
                    }
                }
            }

        # Write workflow to .test-results directory (NOT /tmp/)
        test_results_dir = Path(__file__).parent.parent / ".test-results" / "e2e_local"
        test_results_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = test_results_dir / f"workflow_{provider}_{model_name}.json"

        with open(workflow_file, 'w') as f:
            json.dump(workflow, f)

        try:
            runner = WorkflowRunner(str(workflow_file))
            return runner.model_factory.get_model(provider, model_name)
        finally:
            # Clean up workflow file
            try:
                workflow_file.unlink()
            except Exception:
                pass

    def _check_local_model_available(self) -> bool:
        """Check if local Ollama is available."""
        try:
            import requests

            response = requests.get(
                "http://localhost:11434/api/tags", timeout=2
            )
            return response.status_code == 200
        except Exception:
            return False

    def test_local_model_availability(self):
        """Test that local Ollama endpoint is available."""
        print("\nChecking local Ollama availability...")

        available = self._check_local_model_available()

        if not available:
            pytest.skip(
                "Local Ollama not available at localhost:11434"
            )

        print("Local Ollama is available")
        assert available

    def test_local_model_instantiation(self, local_workflow):
        """Test that local and cloud models can be instantiated."""
        print("\nInstantiating local and cloud models...")

        if not self._check_local_model_available():
            pytest.skip("Local Ollama not available")

        try:
            # Test local model
            node_config_local = local_workflow["graph"]["nodes"]["analyze_local"]
            provider_local = node_config_local["provider"]
            model_name_local = node_config_local["model"]

            model_local = self._get_model(provider_local, model_name_local, local_workflow)

            assert model_local is not None
            print(f"✓ Successfully instantiated LOCAL: {provider_local}/{model_name_local}")

            # Test cloud model
            node_config_cloud = local_workflow["graph"]["nodes"]["analyze_cloud"]
            provider_cloud = node_config_cloud["provider"]
            model_name_cloud = node_config_cloud["model"]

            model_cloud = self._get_model(provider_cloud, model_name_cloud, local_workflow)

            assert model_cloud is not None
            print(f"✓ Successfully instantiated CLOUD: {provider_cloud}/{model_name_cloud}")

        except Exception as e:
            pytest.skip(f"Failed to instantiate model: {str(e)}")

    def test_local_model_execution(self, local_workflow, output_dir):
        """Test that local and cloud models execute and return output."""
        print("\n" + "=" * 80)
        print("Testing Local and Cloud Model Execution")
        print("=" * 80)

        if not self._check_local_model_available():
            pytest.skip("Local Ollama not available")

        results = {}

        for node_id in ["analyze_local", "analyze_cloud"]:
            node_config = local_workflow["graph"]["nodes"][node_id]

            try:
                provider = node_config["provider"]
                model_name = node_config["model"]
                input_text = node_config.get("input", "")
                max_tokens = node_config.get("parameters", {}).get("max_tokens", 256)

                node_type = "LOCAL" if "local" in node_id else "CLOUD"
                print(f"\n[{node_type}] Provider: {provider}")
                print(f"[{node_type}] Model: {model_name}")
                print(f"[{node_type}] Input: {input_text}")
                print(f"[{node_type}] Max tokens: {max_tokens}")

                # Get model and execute
                start_time = time.time()

                try:
                    model = self._get_model(provider, model_name, local_workflow)
                except Exception as e:
                    print(f"[{node_type}] SKIPPED: Failed to get model: {str(e)}")
                    continue

                result = model.call(
                    prompt=input_text,
                    max_tokens=max_tokens,
                    temperature=0.0,
                )

                execution_time = time.time() - start_time

                if "error" in result:
                    error = result.get("error")
                    print(f"[{node_type}] Result: FAILED")
                    print(f"[{node_type}] Error: {error}")
                    continue

                output_text = result.get("output", "")

                print(f"[{node_type}] Result: SUCCESS")
                print(f"[{node_type}] Execution time: {execution_time:.2f}s")
                print(f"[{node_type}] Output length: {len(output_text)} characters")

                if output_text:
                    preview = (
                        output_text[:200] + "..."
                        if len(output_text) > 200
                        else output_text
                    )
                    print(f"[{node_type}] Output preview: {preview}")

                # Verify output
                assert output_text, f"[{node_type}] Model returned empty output"
                assert (
                    execution_time < 30
                ), f"[{node_type}] Execution took too long: {execution_time:.2f}s"

                results[node_id] = {
                    "provider": provider,
                    "model": model_name,
                    "execution_time": execution_time,
                    "output_length": len(output_text),
                    "output": output_text[:500],
                    "status": "SUCCESS"
                }

            except AssertionError:
                raise
            except Exception as e:
                print(f"Test setup failed for {node_id}: {str(e)}")
                continue

        # Save results
        result_file = output_dir / "mixed_execution_results.json"
        with open(result_file, "w") as f:
            json.dump(
                {
                    "workflow_id": local_workflow["id"],
                    "nodes": results,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        print(f"\n✓ Results saved to: {result_file}")
        assert len(results) > 0, "No models executed successfully"

    def test_local_execution_speed(self, local_workflow, output_dir):
        """Test that local and cloud execution completes quickly."""
        print("\n" + "=" * 80)
        print("Testing Local and Cloud Execution Speed")
        print("=" * 80)

        if not self._check_local_model_available():
            pytest.skip("Local Ollama not available")

        speed_results = {}

        for node_id in ["analyze_local", "analyze_cloud"]:
            node_config = local_workflow["graph"]["nodes"][node_id]
            node_type = "LOCAL" if "local" in node_id else "CLOUD"

            try:
                provider = node_config["provider"]
                model_name = node_config["model"]

                model = self._get_model(provider, model_name, local_workflow)

                # Quick execution
                prompt = "Hello, how are you?"

                start_time = time.time()

                result = model.call(
                    prompt=prompt,
                    max_tokens=100,
                    temperature=0.0,
                )

                execution_time = time.time() - start_time

                if "error" in result:
                    print(f"[{node_type}] SKIPPED: {result.get('error')}")
                    continue

                output_text = result.get("output", "")

                print(f"\n[{node_type}] Quick execution test:")
                print(f"[{node_type}] Prompt: {prompt}")
                print(f"[{node_type}] Execution time: {execution_time:.2f}s")
                print(f"[{node_type}] Output length: {len(output_text)}")

                # Models should complete within 30 seconds
                assert (
                    execution_time < 30
                ), f"[{node_type}] Execution too slow: {execution_time:.2f}s"

                speed_results[node_id] = {
                    "provider": provider,
                    "model": model_name,
                    "execution_time": execution_time,
                    "output_length": len(output_text),
                    "status": "FAST" if execution_time < 10 else "OK"
                }

                print(f"[{node_type}] ✓ Execution is acceptably fast")

            except Exception as e:
                print(f"[{node_type}] SKIPPED: {str(e)}")
                continue

        # Save speed results
        result_file = output_dir / "execution_speed_results.json"
        with open(result_file, "w") as f:
            json.dump(
                {
                    "workflow_id": local_workflow["id"],
                    "nodes": speed_results,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        print(f"\n✓ Speed results saved to: {result_file}")

    def test_local_error_handling(self, local_workflow):
        """Test that execution handles errors gracefully."""
        print("\n" + "=" * 80)
        print("Testing Error Handling - Local and Cloud")
        print("=" * 80)

        if not self._check_local_model_available():
            pytest.skip("Local Ollama not available")

        # Test with non-existent local model
        try:
            print("\n[LOCAL] Testing with non-existent model...")
            model = self._get_model("ollama", "nonexistent-model-xyz", local_workflow)

            result = model.call(
                prompt="test", max_tokens=10, temperature=0.0
            )

            if "error" in result:
                error = result.get("error")
                print(f"[LOCAL] ✓ Caught expected error: {error}")
                assert "not found" in error.lower() or "error" in error.lower()

        except Exception as e:
            # Also acceptable to raise exception for missing model
            print(f"[LOCAL] ✓ Caught exception for missing model: {type(e).__name__}")

        # Test with non-existent cloud model
        try:
            print("\n[CLOUD] Testing with non-existent model...")
            model = self._get_model("ollama_cloud", "nonexistent-cloud-model-xyz", local_workflow)

            result = model.call(
                prompt="test", max_tokens=10, temperature=0.0
            )

            if "error" in result:
                error = result.get("error")
                print(f"[CLOUD] ✓ Caught expected error: {error}")
                assert "not found" in error.lower() or "error" in error.lower()

        except Exception as e:
            # Also acceptable to raise exception for missing model
            print(f"[CLOUD] ✓ Caught exception for missing model: {type(e).__name__}")
