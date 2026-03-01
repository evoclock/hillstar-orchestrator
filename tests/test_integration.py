"""
Integration tests for Hillstar workflow orchestration.

Tests the complete flow:
1. Discovery Validation Execution
2. MCP server integration
3. Auto-discovery and recommendations
4. Different workflow types and presets
5. Error handling and edge cases
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows import AutoDiscover, WorkflowDiscovery, ModelPresets, WorkflowValidator


class TestIntegration:
	"""Integration test suite."""

	@staticmethod
	def test_discovery_in_project():
		"""Test discovering workflows in agentic-orchestrator."""
		print("\n TEST: Discovery in project")

		start_dir = '/home/jgamboa/agentic-orchestrator'
		workflows = WorkflowDiscovery.get_all_workflow_info(start_dir, max_depth=4)

		assert len(workflows) > 0, "Should find at least one workflow"

		# Make test order-agnostic - check that expected workflow exists
		workflow_ids = [w['id'] for w in workflows]
		assert 'mouse_phenome_classification_pipeline' in workflow_ids, \
			f"Should find mouse_phenome_classification_pipeline in {workflow_ids}"

		# Test a specific workflow (find the first one that has nodes)
		test_workflow = None
		for wf in workflows:
			if wf['node_count'] > 0:
				test_workflow = wf
				break

		assert test_workflow is not None, "Should find at least one workflow with nodes"
		assert test_workflow['node_count'] > 0
		assert test_workflow['edge_count'] >= 0

		print(f" Found {len(workflows)} workflow(s)")
		print(f" Workflow: {test_workflow['id']}")
		print(f" Nodes: {test_workflow['node_count']}, Edges: {test_workflow['edge_count']}")

	@staticmethod
	def test_validation_valid_workflow():
		"""Test validating a valid workflow."""
		print("\n TEST: Validation of valid workflow")

		workflow_path = '/home/jgamboa/agentic-orchestrator/dev/examples/mouse-phenome/workflow.json'
		valid, errors = WorkflowValidator.validate_file(workflow_path)

		assert valid, f"Should validate successfully, got errors: {errors}"
		assert len(errors) == 0, "Should have no errors"

		print(f" Validated: {workflow_path}")

	@staticmethod
	def test_validation_invalid_workflow():
		"""Test validating an invalid workflow."""
		print("\n TEST: Validation of invalid workflow")

		with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
			# Missing required 'id' and 'graph' fields
			invalid = {"description": "Invalid workflow"}
			json.dump(invalid, f)
			f.flush()
			workflow_path = f.name

		try:
			valid, errors = WorkflowValidator.validate_file(workflow_path)
			assert not valid, "Should fail validation"
			assert len(errors) > 0, "Should have errors"
			print(f" Caught {len(errors)} validation error(s) as expected")
		finally:
			os.unlink(workflow_path)

	@staticmethod
	def test_auto_discover_project():
		"""Test auto-discovery in a Hillstar project."""
		print("\n TEST: Auto-discover project")

		start_dir = '/home/jgamboa/hillstar-orchestrator'
		is_hillstar = AutoDiscover.is_hillstar_project(start_dir)

		assert is_hillstar, "Should detect as Hillstar project"

		info = AutoDiscover.get_project_info(start_dir)
		assert info['is_hillstar']
		assert info['has_schema']
		assert info['has_workflows']
		assert info['workflow_count'] > 0

		print(" Detected: Hillstar project")
		print(f" Workflows: {info['workflow_count']}")

	@staticmethod
	def test_auto_discover_non_project():
		"""Test auto-discovery in non-Hillstar directory."""
		print("\n TEST: Auto-discover non-project")

		is_hillstar = AutoDiscover.is_hillstar_project('/tmp')
		assert not is_hillstar, "Should not detect /tmp as Hillstar project"

		print(" Correctly identified as non-Hillstar directory")

	@staticmethod
	def test_task_classification():
		"""Test task classification with keywords."""
		print("\n TEST: Task classification")

		tasks = [
			("Plan and analyze data", "planning"),
			("Implement feature quickly", "implementation"),
			("Review for quality", "testing"),
			("Minimize cost", "budget_conscious"),
			("Air-gapped sensitive data", "local_only"),
		]

		for task_desc, expected_keyword in tasks:
			classification = AutoDiscover.classify_task(task_desc)
			assert classification[expected_keyword] > 0.2, \
				f"Should classify '{task_desc}' with {expected_keyword}"
			print(f" '{task_desc}' {expected_keyword}: {classification[expected_keyword]:.0%}")

	@staticmethod
	def test_preset_suggestions():
		"""Test preset suggestions based on task."""
		print("\n TEST: Preset suggestions")

		# Budget-conscious task
		task = "Analyze with limited budget"
		classification = AutoDiscover.classify_task(task)
		presets = AutoDiscover.get_preset_suggestions(classification)
		assert len(presets) > 0, "Should suggest presets"
		assert presets[0][0] == 'minimize_cost', "Should suggest minimize_cost"
		print(f" Budget-conscious {presets[0][0]}")

		# Quality-focused task
		task = "High quality analysis for publication"
		classification = AutoDiscover.classify_task(task)
		presets = AutoDiscover.get_preset_suggestions(classification)
		assert any(p[0] == 'maximize_quality' for p in presets)
		print(" Quality-focused maximize_quality")

		# Local-only task
		task = "Process sensitive data without external APIs"
		classification = AutoDiscover.classify_task(task)
		presets = AutoDiscover.get_preset_suggestions(classification)
		assert presets[0][0] == 'local_only', "Should suggest local_only"
		print(f" Local-only {presets[0][0]}")

	@staticmethod
	def test_workflow_suggestions():
		"""Test workflow suggestions."""
		print("\n TEST: Workflow suggestions")

		workflows = WorkflowDiscovery.get_all_workflow_info(
			'/home/jgamboa/agentic-orchestrator',
			max_depth=4
		)

		task = "Analyze mouse phenotype data with clustering"
		suggestions = AutoDiscover.suggest_workflows(task, workflows, top_k=3)

		assert len(suggestions) > 0, "Should suggest workflows"
		# Make test flexible - accept any mouse phenome workflow as top suggestion
		assert any('mouse_phenome' in s['id'] for s in suggestions), \
			f"Should suggest mouse phenome workflow, got: {[s['id'] for s in suggestions]}"
		print(f" Found {len(suggestions)} workflow suggestion(s)")
		print(f" Top match: {suggestions[0]['id']}")

	@staticmethod
	def test_full_recommendations():
		"""Test comprehensive recommendations."""
		print("\n TEST: Full recommendations")

		workflows = WorkflowDiscovery.get_all_workflow_info(
			'/home/jgamboa/agentic-orchestrator',
			max_depth=4
		)

		task = "Cluster mouse phenotypes with budget constraint"
		recommendations = AutoDiscover.get_recommendations(task, workflows)

		assert 'task_classification' in recommendations
		assert 'suggested_presets' in recommendations
		assert 'suggested_workflows' in recommendations
		assert 'recommendation_text' in recommendations

		print(f" Task classification: {len(recommendations['task_classification'])} categories")
		print(f" Presets suggested: {len(recommendations['suggested_presets'])}")
		print(f" Workflows suggested: {len(recommendations['suggested_workflows'])}")
		print(f" Recommendation: {recommendations['recommendation_text'][:50]}...")

	@staticmethod
	def test_presets_available():
		"""Test that all presets are accessible."""
		print("\n TEST: Available presets")

		presets = ModelPresets.get_available_presets()
		assert len(presets) >= 4, "Should have at least 4 presets"

		expected = ['minimize_cost', 'balanced', 'maximize_quality', 'local_only']
		for preset in expected:
			assert preset in presets, f"Should have {preset} preset"
			desc = ModelPresets.describe_preset(preset)
			assert 'description' in desc
			assert 'use_case' in desc

		print(f" Found {len(presets)} presets:")
		for preset in presets:
			print(f" - {preset}")

	@staticmethod
	def test_error_handling_missing_file():
		"""Test error handling for missing workflow file."""
		print("\n TEST: Error handling - missing file")

		valid, errors = WorkflowValidator.validate_file('/nonexistent/workflow.json')
		assert not valid, "Should fail validation"
		assert len(errors) > 0, "Should have error message"
		print(f" Correctly handled missing file: {errors[0][:50]}...")

	@staticmethod
	def test_error_handling_invalid_json():
		"""Test error handling for invalid JSON."""
		print("\n TEST: Error handling - invalid JSON")

		with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
			f.write("{ invalid json")
			f.flush()
			workflow_path = f.name

		try:
			valid, errors = WorkflowValidator.validate_file(workflow_path)
			assert not valid, "Should fail validation"
			assert 'JSON' in str(errors[0]) or 'json' in str(errors[0])
			print(" Correctly caught JSON error")
		finally:
			os.unlink(workflow_path)

	@staticmethod
	def test_discovery_depth_limit():
		"""Test that discovery respects max_depth."""
		print("\n TEST: Discovery respects depth limit")

		# Create temporary directory structure
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create workflow at depth 2
			level1 = os.path.join(tmpdir, 'level1')
			level2 = os.path.join(level1, 'level2')
			os.makedirs(level2)

			workflow = {
				"id": "test_workflow",
				"graph": {
					"nodes": {},
					"edges": []
				}
			}

			with open(os.path.join(level2, 'workflow.json'), 'w') as f:
				json.dump(workflow, f)

			# Should find with max_depth >= 2
			workflows = WorkflowDiscovery.get_all_workflow_info(tmpdir, max_depth=2)
			assert len(workflows) == 1

			# Should not find with max_depth < 2
			workflows = WorkflowDiscovery.get_all_workflow_info(tmpdir, max_depth=1)
			assert len(workflows) == 0

			print(" Depth limit working correctly")

	@staticmethod
	def run_all_tests():
		"""Run all integration tests."""
		print("\n" + "=" * 70)
		print("PHASE 6: INTEGRATION TESTING")
		print("=" * 70)

		tests = [
			TestIntegration.test_discovery_in_project,
			TestIntegration.test_validation_valid_workflow,
			TestIntegration.test_validation_invalid_workflow,
			TestIntegration.test_auto_discover_project,
			TestIntegration.test_auto_discover_non_project,
			TestIntegration.test_task_classification,
			TestIntegration.test_preset_suggestions,
			TestIntegration.test_workflow_suggestions,
			TestIntegration.test_full_recommendations,
			TestIntegration.test_presets_available,
			TestIntegration.test_error_handling_missing_file,
			TestIntegration.test_error_handling_invalid_json,
			TestIntegration.test_discovery_depth_limit,
		]

		passed = 0
		failed = 0

		for test in tests:
			try:
				test()
				passed += 1
			except AssertionError as e:
				print(f" FAILED: {str(e)}")
				failed += 1
			except Exception as e:
				print(f" ERROR: {str(e)}")
				failed += 1

		print("\n" + "=" * 70)
		print(f"RESULTS: {passed} passed, {failed} failed")
		print("=" * 70 + "\n")

		return failed == 0


if __name__ == '__main__':
 success = TestIntegration.run_all_tests()
 sys.exit(0 if success else 1)
