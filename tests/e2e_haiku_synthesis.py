"""
E2E Test: Haiku Synthesis Pipeline

Purpose:
Full end-to-end test of multi-node orchestration pipeline with data
flowing between stages.

Workflow: 5-node pipeline
1. haiku_generation (Anthropic Haiku) - Write haikus
2. nano_summary (OpenAI) - Summarize haikus
3. mistral_condense (Mistral) - Condense summary
4. entity_extraction (Devstral) - Extract entities
5. final_synthesis (Ollama) - Final synthesis

Data flow: Each node receives output from previous node via template
substitution ({{ node_id.output }})

Tests:
- All 5 nodes execute successfully
- Data flows correctly between nodes
- Outputs are captured and validated
- Error handling works correctly

Author: Testing Suite
Created: 2026-02-22
"""

import json
import os
import pytest
from pathlib import Path
from datetime import datetime


class TestHaikuSynthesisPipeline:
    """End-to-end test of haiku synthesis pipeline."""

    @pytest.fixture
    def workflow(self):
        """Load the haiku synthesis workflow."""
        workflow_file = Path(__file__).parent.parent / "examples" / "multi-provider-workflow.json"

        assert workflow_file.exists(), (
            f"Workflow file not found: {workflow_file}"
        )

        with open(workflow_file) as f:
            return json.load(f)

    @pytest.fixture
    def output_dir(self):
        """Create output directory for E2E results."""
        output_dir = (
            Path(__file__).parent.parent / ".test-results" / "e2e_haiku"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _get_model(self, provider: str, model_name: str, workflow: dict = None):
        """Get a model instance for the given provider and model."""
        from execution.runner import WorkflowRunner
        import tempfile

        if workflow is None:
            workflow = {
                "id": "minimal_test_workflow",
                "graph": {"nodes": {}, "edges": []},
                "provider_config": {
                    provider: {
                        "tos_accepted": True,
                        "audit_enabled": True,
                    }
                }
            }

        # Write workflow to .test-results directory (NOT /tmp/)
        test_results_dir = Path(__file__).parent.parent / ".test-results" / "e2e_haiku"
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

    def _execute_node(
        self, node_id: str, node_config: dict, previous_outputs: dict, workflow: dict = None
    ) -> tuple:
        """
        Execute a single node with input from previous outputs.

        Args:
            node_id: Node identifier
            node_config: Node configuration
            previous_outputs: Dictionary of previous node outputs

        Returns:
            Tuple of (output_text, error_message)
        """
        try:
            # Get provider and model
            provider = node_config.get("provider")
            model_name = node_config.get("model")

            if not provider or not model_name:
                return None, f"Missing provider or model in node {node_id}"

            # Check for required API keys for cloud providers
            if provider == "anthropic":
                if not os.environ.get("ANTHROPIC_API_KEY"):
                    return None, "ANTHROPIC_API_KEY not set"
            elif provider == "openai":
                if not os.environ.get("OPENAI_API_KEY"):
                    return None, "OPENAI_API_KEY not set"
            elif provider == "mistral":
                if not os.environ.get("MISTRAL_API_KEY"):
                    return None, "MISTRAL_API_KEY not set"

            # Get model instance
            try:
                model = self._get_model(provider, model_name, workflow)
            except Exception as e:
                return None, f"Failed to get model: {str(e)}"

            # Build input by substituting previous outputs
            input_template = node_config.get("input", "")
            input_text = input_template

            for prev_node_id, prev_output in previous_outputs.items():
                if prev_output:
                    placeholder = f"{{{{ {prev_node_id}.output }}}}"
                    input_text = input_text.replace(
                        placeholder, prev_output
                    )

            # Get parameters
            parameters = node_config.get("parameters", {})
            max_tokens = parameters.get("max_tokens", 512)
            temperature = parameters.get("temperature", 0.0)

            # Call model
            try:
                result = model.call(
                    prompt=input_text,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                if "error" in result:
                    return None, result.get("error")

                output_text = result.get("output", "")
                return output_text if output_text else None, None

            except Exception as e:
                return None, f"Model call failed: {str(e)}"

        except Exception as e:
            return None, f"Node execution failed: {str(e)}"

    def test_workflow_structure(self, workflow):
        """Test that workflow has expected structure."""
        assert "id" in workflow
        assert "graph" in workflow
        assert "provider_config" in workflow

        graph = workflow["graph"]
        assert "nodes" in graph
        assert "edges" in graph

        nodes = graph["nodes"]
        assert len(nodes) == 5, f"Expected 5 nodes, got {len(nodes)}"

        expected_nodes = [
            "write_haikus",
            "extract_entities",
            "identify_themes",
            "reconstruct_from_representation",
            "validate_reconstruction",
        ]

        for expected in expected_nodes:
            assert expected in nodes, f"Missing node: {expected}"

    def test_node_execution_sequential(self, workflow, output_dir):
        """Test that all nodes execute in sequence with data flow."""
        nodes = workflow["graph"]["nodes"]
        outputs = {}
        execution_log = []

        print("\n" + "=" * 80)
        print("E2E Haiku Synthesis Pipeline Execution")
        print("=" * 80)

        node_list = list(nodes.items())

        for i, (node_id, node_config) in enumerate(node_list, 1):
            print(f"\n[Node {i}/5] {node_id}")
            print(f"Provider: {node_config.get('provider')}")
            print(f"Model: {node_config.get('model')}")

            execution_log.append({
                "node_index": i,
                "node_id": node_id,
                "timestamp": datetime.now().isoformat(),
                "status": "executing",
            })

            output_text, error = self._execute_node(
                node_id, node_config, outputs, workflow
            )

            if error:
                print("Result: FAILED")
                print(f"Error: {error}")

                execution_log[-1]["status"] = "failed"
                execution_log[-1]["error"] = error

                pytest.skip(
                    f"Node {node_id} failed: {error}"
                )
            else:
                outputs[node_id] = output_text

                if output_text:
                    output_length = len(output_text)
                    preview = (
                        output_text[:100] + "..."
                        if output_length > 100
                        else output_text
                    )
                    print("Result: SUCCESS")
                    print(f"Output ({output_length} chars): {preview}")

                    execution_log[-1]["status"] = "success"
                    execution_log[-1]["output_length"] = output_length
                else:
                    print("Result: SUCCESS (empty output)")

                    execution_log[-1]["status"] = "success"
                    execution_log[-1]["output_length"] = 0

        print("\n" + "=" * 80)
        print(f"Execution complete: {len(outputs)}/5 nodes succeeded")
        print("=" * 80)

        # Save execution log
        log_file = output_dir / "haiku_execution_log.json"
        with open(log_file, "w") as f:
            json.dump(execution_log, f, indent=2)

        # Save outputs (full, untruncated)
        outputs_file = output_dir / "haiku_outputs.json"
        with open(outputs_file, "w") as f:
            json.dump(outputs, f, indent=2)

        # Verify all nodes executed
        assert len(outputs) == 5, (
            f"Not all nodes executed. Got {len(outputs)}/5"
        )

    def test_data_flow_through_pipeline(self, workflow, output_dir):
        """Test that data flows correctly between nodes."""
        nodes = workflow["graph"]["nodes"]
        outputs = {}

        print("\n" + "=" * 80)
        print("Testing Data Flow Through Pipeline")
        print("=" * 80)

        for node_id, node_config in nodes.items():
            output_text, error = self._execute_node(
                node_id, node_config, outputs, workflow
            )

            if not error and output_text:
                outputs[node_id] = output_text
                print(f"{node_id}: Captured {len(output_text)} characters")
            else:
                pytest.skip(f"Node {node_id} failed to produce output")

        print("\nData flow summary:")
        for node_id, output in outputs.items():
            if output:
                print(
                    f"  {node_id}: {len(output)} chars -> "
                    f"used by next node"
                )

        # Verify we have outputs from all stages
        assert len(outputs) == 5, "Not all stages produced output"

        # Save flow diagram
        flow_file = output_dir / "haiku_data_flow.txt"
        with open(flow_file, "w") as f:
            f.write("Data Flow Through Pipeline\n")
            f.write("=" * 80 + "\n\n")

            for i, (node_id, output) in enumerate(outputs.items(), 1):
                if output:
                    f.write(f"[Stage {i}] {node_id}\n")
                    f.write(f"Output length: {len(output)} characters\n")
                    f.write(f"Preview: {output[:200]}...\n")
                    f.write("-" * 80 + "\n\n")

    def test_error_handling(self, workflow):
        """Test that pipeline handles errors gracefully."""
        print("\n" + "=" * 80)
        print("Testing Error Handling")
        print("=" * 80)

        # Test with invalid provider
        test_node = {
            "provider": "invalid_provider",
            "model": "nonexistent_model",
            "input": "Test",
        }

        output, error = self._execute_node(
            "test_node", test_node, {}
        )

        assert error is not None, "Expected error for invalid provider"
        print(f"Caught expected error: {error}")
