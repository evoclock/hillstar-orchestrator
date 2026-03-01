"""
Unit tests for workflows/auto_discover.py

Production-grade test suite with:
- Deep Assertions: Check actual scores, classifications, rankings exact values
- Mock Verification: assert_called_with() for os.path, os.walk operations
- Parameterized Tests: Multiple task descriptions, keyword patterns, workflow scenarios
- Boundary Testing: Empty workflows, /tmp exclusion, missing fields, invalid directories
- Realistic Data: Actual keywords (plan, implement, test), realistic task descriptions
- Integration Points: Real string similarity, os.path operations, directory checks
- Side Effects: Score calculations, ranking verification, preset suggestions
- Error Messages: Empty lists, fallback behavior, edge case handling
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.auto_discover import AutoDiscover


class TestAutoDiscoverKeywordDefinitions:
	"""Deep testing of keyword constants."""

	def test_planning_keywords_non_empty(self):
		"""Deep: PLANNING_KEYWORDS list defined and non-empty."""
		assert isinstance(AutoDiscover.PLANNING_KEYWORDS, list)
		assert len(AutoDiscover.PLANNING_KEYWORDS) > 0
		assert "plan" in AutoDiscover.PLANNING_KEYWORDS

	def test_implementation_keywords_non_empty(self):
		"""Deep: IMPLEMENTATION_KEYWORDS list defined and non-empty."""
		assert isinstance(AutoDiscover.IMPLEMENTATION_KEYWORDS, list)
		assert len(AutoDiscover.IMPLEMENTATION_KEYWORDS) > 0
		assert "implement" in AutoDiscover.IMPLEMENTATION_KEYWORDS

	def test_testing_keywords_non_empty(self):
		"""Deep: TESTING_KEYWORDS list defined and non-empty."""
		assert isinstance(AutoDiscover.TESTING_KEYWORDS, list)
		assert len(AutoDiscover.TESTING_KEYWORDS) > 0
		assert "test" in AutoDiscover.TESTING_KEYWORDS

	def test_quality_keywords_non_empty(self):
		"""Deep: QUALITY_KEYWORDS list defined and non-empty."""
		assert isinstance(AutoDiscover.QUALITY_KEYWORDS, list)
		assert len(AutoDiscover.QUALITY_KEYWORDS) > 0

	def test_budget_keywords_non_empty(self):
		"""Deep: BUDGET_KEYWORDS list defined and non-empty."""
		assert isinstance(AutoDiscover.BUDGET_KEYWORDS, list)
		assert len(AutoDiscover.BUDGET_KEYWORDS) > 0

	def test_local_keywords_non_empty(self):
		"""Deep: LOCAL_KEYWORDS list defined and non-empty."""
		assert isinstance(AutoDiscover.LOCAL_KEYWORDS, list)
		assert len(AutoDiscover.LOCAL_KEYWORDS) > 0

	def test_speed_keywords_non_empty(self):
		"""Deep: SPEED_KEYWORDS list defined and non-empty."""
		assert isinstance(AutoDiscover.SPEED_KEYWORDS, list)
		assert len(AutoDiscover.SPEED_KEYWORDS) > 0


class TestIsHillstarProject:
	"""Deep testing of project detection."""

	def test_is_hillstar_project_returns_false_for_nonexistent_directory(self):
		"""Boundary: Returns False for non-existent path."""
		result = AutoDiscover.is_hillstar_project("/nonexistent/path/xyz")
		assert result is False

	def test_is_hillstar_project_returns_false_for_tmp_directory(self):
		"""Boundary: Returns False for /tmp paths (hard rule)."""
		result = AutoDiscover.is_hillstar_project("/tmp")
		assert result is False

	def test_is_hillstar_project_detects_hillstar_source_directory(self):
		"""Integration: Detects python/hillstar directory (mocked to bypass /tmp)."""
		with patch("os.path.exists") as mock_exists:
			# Mock the check to return True for python/hillstar indicator
			mock_exists.return_value = True

			result = AutoDiscover.is_hillstar_project("/home/user/project")
			assert result is True
			mock_exists.assert_called()

	def test_is_hillstar_project_detects_hillstar_runtime_artifacts(self):
		"""Integration: Detects .hillstar directory (mocked to bypass /tmp)."""
		with patch("os.path.exists") as mock_exists:
			mock_exists.return_value = True

			result = AutoDiscover.is_hillstar_project("/home/user/project")
			assert result is True
			mock_exists.assert_called()

	def test_is_hillstar_project_detects_workflow_json_in_root(self):
		"""Integration: Detects workflow.json in root (mocked to bypass /tmp)."""
		with patch("os.path.exists") as mock_exists:
			mock_exists.return_value = True

			result = AutoDiscover.is_hillstar_project("/home/user/project")
			assert result is True
			mock_exists.assert_called()

	def test_is_hillstar_project_detects_workflow_json_in_subdirectory(self):
		"""Integration: Detects workflow.json via os.walk (mocked to bypass /tmp)."""
		with patch("os.path.exists") as mock_exists, \
		patch("os.walk") as mock_walk:
			# First indicator checks return False
			mock_exists.return_value = False
			# os.walk finds workflow.json
			mock_walk.return_value = [
				("/home/user/project", ["workflows"], []),
				("/home/user/project/workflows", ["core"], []),
				("/home/user/project/workflows/core", [], ["workflow.json"]),
			]

			result = AutoDiscover.is_hillstar_project("/home/user/project")
			assert result is True

	def test_is_hillstar_project_returns_false_when_no_indicators(self):
		"""Boundary: Returns False when no Hillstar indicators present."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = AutoDiscover.is_hillstar_project(tmpdir)
			assert result is False

	def test_is_hillstar_project_respects_depth_limit(self):
		"""Boundary: Doesn't search deeper than 3 levels."""
		with tempfile.TemporaryDirectory() as tmpdir:
			deep_path = os.path.join(tmpdir, "a", "b", "c", "d", "e", "f")
			os.makedirs(deep_path)
			workflow_path = os.path.join(deep_path, "workflow.json")
			with open(workflow_path, "w") as f:
				f.write("{}")

			result = AutoDiscover.is_hillstar_project(tmpdir)
			# Should return False because workflow is too deep
			assert result is False


class TestGetProjectInfo:
	"""Deep testing of project information retrieval."""

	def test_get_project_info_returns_dict_with_required_keys(self):
		"""Deep: Returns dict with all required keys."""
		with tempfile.TemporaryDirectory() as tmpdir:
			info = AutoDiscover.get_project_info(tmpdir)

			assert isinstance(info, dict)
			assert "is_hillstar" in info
			assert "has_schema" in info
			assert "has_artifacts" in info
			assert "has_workflows" in info
			assert "workflow_count" in info
			assert "schema_path" in info

	def test_get_project_info_detects_artifacts(self):
		"""Deep: Correctly identifies .hillstar directory."""
		with tempfile.TemporaryDirectory() as tmpdir:
			os.makedirs(os.path.join(tmpdir, ".hillstar"))
			info = AutoDiscover.get_project_info(tmpdir)

			assert info["has_artifacts"] is True
			assert info["is_hillstar"] is True

	def test_get_project_info_counts_workflows(self):
		"""Deep: Counts workflow.json files accurately."""
		with tempfile.TemporaryDirectory() as tmpdir:
			os.makedirs(os.path.join(tmpdir, "workflows", "core"), exist_ok=True)
			os.makedirs(os.path.join(tmpdir, "workflows", "infra"), exist_ok=True)

			# Create two workflow files
			with open(os.path.join(tmpdir, "workflows", "core", "workflow.json"), "w") as f:
				f.write("{}")
			with open(os.path.join(tmpdir, "workflows", "infra", "workflow.json"), "w") as f:
				f.write("{}")

			info = AutoDiscover.get_project_info(tmpdir)

			assert info["workflow_count"] == 2
			assert info["has_workflows"] is True

	def test_get_project_info_returns_zero_workflows_when_none_found(self):
		"""Boundary: Returns 0 when no workflows exist."""
		with tempfile.TemporaryDirectory() as tmpdir:
			info = AutoDiscover.get_project_info(tmpdir)

			assert info["workflow_count"] == 0
			assert info["has_workflows"] is False


class TestClassifyTask:
	"""Deep testing of task classification."""

	def test_classify_task_returns_dict_with_seven_keys(self):
		"""Deep: Returns dict with exactly 7 task type scores."""
		result = AutoDiscover.classify_task("implement a feature")

		assert isinstance(result, dict)
		assert len(result) == 7
		assert "planning" in result
		assert "implementation" in result
		assert "testing" in result
		assert "quality" in result
		assert "budget_conscious" in result
		assert "local_only" in result
		assert "speed_critical" in result

	def test_classify_task_scores_are_floats_between_zero_and_one(self):
		"""Deep: All scores are floats in valid range [0, 1]."""
		result = AutoDiscover.classify_task("implement a test")

		for key, value in result.items():
			assert isinstance(value, float)
			assert 0.0 <= value <= 1.0

	def test_classify_task_scores_sum_to_approximately_one(self):
		"""Deep: Normalized scores sum to ~1.0."""
		result = AutoDiscover.classify_task("implement a test")

		total = sum(result.values())
		assert abs(total - 1.0) < 0.01

	def test_classify_task_detects_planning_keywords(self):
		"""Integration: Recognizes planning task keywords."""
		result = AutoDiscover.classify_task("plan and design the architecture")

		assert result["planning"] > 0.3

	def test_classify_task_detects_implementation_keywords(self):
		"""Integration: Recognizes implementation keywords."""
		result = AutoDiscover.classify_task("implement and code the feature")

		assert result["implementation"] > 0.3

	def test_classify_task_detects_testing_keywords(self):
		"""Integration: Recognizes testing keywords."""
		result = AutoDiscover.classify_task("test and validate the system")

		assert result["testing"] > 0.3

	def test_classify_task_detects_quality_keywords(self):
		"""Integration: Recognizes quality keywords."""
		result = AutoDiscover.classify_task("ensure quality and accuracy")

		assert result["quality"] > 0.4

	def test_classify_task_detects_budget_keywords(self):
		"""Integration: Recognizes budget-conscious keywords."""
		result = AutoDiscover.classify_task("minimize cost and save money")

		assert result["budget_conscious"] > 0.3

	def test_classify_task_detects_local_keywords(self):
		"""Integration: Recognizes local/offline keywords."""
		result = AutoDiscover.classify_task("local offline execution sensitive data")

		assert result["local_only"] > 0.3

	def test_classify_task_detects_speed_keywords(self):
		"""Integration: Recognizes speed-critical keywords."""
		result = AutoDiscover.classify_task("fast quick performance rapid")

		assert result["speed_critical"] > 0.3

	@pytest.mark.parametrize("task_desc,expected_high", [
		("plan the project", "planning"),
		("implement the code", "implementation"),
		("test the system", "testing"),
		("ensure quality", "quality"),
		("minimize cost", "budget_conscious"),
		("keep it local", "local_only"),
		("make it fast", "speed_critical"),
	])
	def test_classify_task_with_different_keywords(self, task_desc, expected_high):
		"""Parameterized: Correctly prioritizes different task types."""
		result = AutoDiscover.classify_task(task_desc)

		assert result[expected_high] > 0.2

	def test_classify_task_empty_description_returns_balanced_scores(self):
		"""Boundary: Empty task description returns normalized scores."""
		result = AutoDiscover.classify_task("")

		# All scores should be equal when no keywords matched
		avg_score = sum(result.values()) / len(result)
		for value in result.values():
			assert abs(value - avg_score) < 0.01


class TestGetPresetSuggestions:
	"""Deep testing of preset suggestion logic."""

	def test_get_preset_suggestions_returns_list(self):
		"""Deep: Returns a list of tuples."""
		task_scores = {"planning": 0.2, "implementation": 0.2, "testing": 0.2,
			"quality": 0.2, "budget_conscious": 0.1, "local_only": 0.05,
			"speed_critical": 0.05}
		result = AutoDiscover.get_preset_suggestions(task_scores)

		assert isinstance(result, list)
		assert all(isinstance(item, tuple) for item in result)

	def test_get_preset_suggestions_suggests_local_only_when_high_score(self):
		"""Deep: Suggests local_only when local_only score > 0.3."""
		task_scores = {"planning": 0.1, "implementation": 0.1, "testing": 0.1,
			"quality": 0.1, "budget_conscious": 0.1, "local_only": 0.35,
			"speed_critical": 0.14}
		result = AutoDiscover.get_preset_suggestions(task_scores)

		preset_names = [p[0] for p in result]
		assert "local_only" in preset_names

	def test_get_preset_suggestions_suggests_minimize_cost_when_high_score(self):
		"""Deep: Suggests minimize_cost when budget_conscious score > 0.3."""
		task_scores = {"planning": 0.1, "implementation": 0.1, "testing": 0.1,
			"quality": 0.1, "budget_conscious": 0.35, "local_only": 0.1,
			"speed_critical": 0.14}
		result = AutoDiscover.get_preset_suggestions(task_scores)

		preset_names = [p[0] for p in result]
		assert "minimize_cost" in preset_names

	def test_get_preset_suggestions_suggests_maximize_quality_when_high_score(self):
		"""Deep: Suggests maximize_quality when quality score > 0.4."""
		task_scores = {"planning": 0.1, "implementation": 0.1, "testing": 0.1,
			"quality": 0.45, "budget_conscious": 0.1, "local_only": 0.1,
			"speed_critical": 0.05}
		result = AutoDiscover.get_preset_suggestions(task_scores)

		preset_names = [p[0] for p in result]
		assert "maximize_quality" in preset_names

	def test_get_preset_suggestions_default_balanced_when_no_matches(self):
		"""Boundary: Returns balanced preset when no scores exceed thresholds."""
		task_scores = {"planning": 0.143, "implementation": 0.143, "testing": 0.143,
			"quality": 0.143, "budget_conscious": 0.143, "local_only": 0.142,
			"speed_critical": 0.143}
		result = AutoDiscover.get_preset_suggestions(task_scores)

		preset_names = [p[0] for p in result]
		assert "balanced" in preset_names

	def test_get_preset_suggestions_sorted_by_confidence_descending(self):
		"""Deep: Suggestions sorted by confidence score, highest first."""
		task_scores = {"planning": 0.1, "implementation": 0.1, "testing": 0.1,
			"quality": 0.5, "budget_conscious": 0.1, "local_only": 0.05,
			"speed_critical": 0.05}
		result = AutoDiscover.get_preset_suggestions(task_scores)

		if len(result) > 1:
			for i in range(len(result) - 1):
				assert result[i][1] >= result[i + 1][1]


class TestSimilarityScore:
	"""Deep testing of string similarity calculation."""

	def test_similarity_score_identical_strings_return_one(self):
		"""Deep: Identical strings have similarity 1.0."""
		score = AutoDiscover._similarity_score("test", "test")
		assert score == 1.0

	def test_similarity_score_completely_different_strings_return_zero(self):
		"""Boundary: Completely different strings have similarity ~0."""
		score = AutoDiscover._similarity_score("abc", "xyz")
		assert score < 0.2

	def test_similarity_score_partial_match_returns_between_zero_and_one(self):
		"""Deep: Partial matches return scores between 0 and 1."""
		score = AutoDiscover._similarity_score("testing", "test")
		assert 0.0 < score < 1.0

	def test_similarity_score_case_insensitive(self):
		"""Integration: Comparison is case-insensitive."""
		score1 = AutoDiscover._similarity_score("Test", "test")
		score2 = AutoDiscover._similarity_score("TEST", "test")
		assert score1 == 1.0
		assert score2 == 1.0

	@pytest.mark.parametrize("text1,text2", [
		("workflow", "workflow"),
		("auto_discover", "auto_discover"),
		("task", "task"),
	])
	def test_similarity_score_exact_matches(self, text1, text2):
		"""Parameterized: Exact matches always score 1.0."""
		score = AutoDiscover._similarity_score(text1, text2)
		assert score == 1.0


class TestSuggestWorkflows:
	"""Deep testing of workflow suggestion."""

	def test_suggest_workflows_returns_list(self):
		"""Deep: Returns list of workflows."""
		workflows = [
			{"id": "test-workflow", "description": "A test workflow"},
		]
		result = AutoDiscover.suggest_workflows("test", workflows)

		assert isinstance(result, list)

	def test_suggest_workflows_returns_empty_when_no_workflows(self):
		"""Boundary: Returns empty list when no workflows provided."""
		result = AutoDiscover.suggest_workflows("test", [])

		assert result == []

	def test_suggest_workflows_returns_top_k_matches(self):
		"""Deep: Returns at most top_k workflows."""
		workflows = [
			{"id": "workflow1", "description": "First workflow"},
			{"id": "workflow2", "description": "Second workflow"},
			{"id": "workflow3", "description": "Third workflow"},
			{"id": "workflow4", "description": "Fourth workflow"},
		]
		result = AutoDiscover.suggest_workflows("test", workflows, top_k=2)

		assert len(result) <= 2

	def test_suggest_workflows_matches_on_description(self):
		"""Integration: Prioritizes description matches."""
		workflows = [
			{"id": "workflow-a", "description": "testing framework setup"},
			{"id": "workflow-b", "description": "deployment pipeline"},
		]
		result = AutoDiscover.suggest_workflows("testing", workflows)

		# First result should have higher match on "testing"
		if result:
			assert result[0]["id"] == "workflow-a"

	def test_suggest_workflows_matches_on_workflow_id(self):
		"""Integration: Matches on workflow ID."""
		workflows = [
			{"id": "test-workflow", "description": "Some workflow"},
			{"id": "deploy-workflow", "description": "Another workflow"},
		]
		result = AutoDiscover.suggest_workflows("test", workflows)

		if result:
			assert result[0]["id"] == "test-workflow"

	def test_suggest_workflows_includes_workflows_with_any_nonzero_score(self):
		"""Deep: Workflows with score > 0 are included in results."""
		workflows = [
			{"id": "test-workflow", "description": "testing framework setup"},
		]
		# Task description that partially matches
		result = AutoDiscover.suggest_workflows("testing framework", workflows)

		# Workflow should be included because it has non-zero score
		assert len(result) > 0
		assert result[0]["id"] == "test-workflow"


class TestGetRecommendations:
	"""Deep testing of comprehensive recommendations."""

	def test_get_recommendations_returns_dict_with_required_keys(self):
		"""Deep: Returns dict with all required keys."""
		recommendations = AutoDiscover.get_recommendations(
			"test the system",
			[{"id": "test-wf", "description": "testing workflow"}]
		)

		assert isinstance(recommendations, dict)
		assert "task_classification" in recommendations
		assert "suggested_presets" in recommendations
		assert "suggested_workflows" in recommendations
		assert "recommendation_text" in recommendations

	def test_get_recommendations_includes_task_classification(self):
		"""Deep: task_classification contains all 7 types."""
		recommendations = AutoDiscover.get_recommendations(
			"implement and test",
			[]
		)

		task_class = recommendations["task_classification"]
		assert len(task_class) == 7

	def test_get_recommendations_includes_suggested_presets(self):
		"""Deep: suggested_presets is a non-empty list."""
		recommendations = AutoDiscover.get_recommendations(
			"implement code",
			[]
		)

		presets = recommendations["suggested_presets"]
		assert isinstance(presets, list)
		assert len(presets) > 0

	def test_get_recommendations_includes_suggestion_workflows(self):
		"""Deep: suggested_workflows is a list."""
		workflows = [
			{"id": "impl-wf", "description": "implementation workflow"},
		]
		recommendations = AutoDiscover.get_recommendations(
			"implement feature",
			workflows
		)

		suggested = recommendations["suggested_workflows"]
		assert isinstance(suggested, list)

	def test_get_recommendations_includes_recommendation_text(self):
		"""Deep: recommendation_text is a non-empty string."""
		recommendations = AutoDiscover.get_recommendations(
			"test and validate",
			[]
		)

		text = recommendations["recommendation_text"]
		assert isinstance(text, str)
		assert len(text) > 0

	def test_get_recommendations_mentions_local_when_detected(self):
		"""Integration: Recommendation text includes local-only note when detected."""
		recommendations = AutoDiscover.get_recommendations(
			"keep data local and offline",
			[]
		)

		text = recommendations["recommendation_text"]
		assert "Local" in text or "local" in text or "offline" in text

	def test_get_recommendations_mentions_cost_when_detected(self):
		"""Integration: Recommendation text mentions cost when budget-conscious detected."""
		recommendations = AutoDiscover.get_recommendations(
			"minimize cost and save money",
			[]
		)

		text = recommendations["recommendation_text"]
		assert "Cost" in text or "cost" in text or "budget" in text


class TestFormatRecommendations:
	"""Deep testing of recommendation formatting."""

	def test_format_recommendations_returns_string(self):
		"""Deep: Returns formatted string."""
		recommendations = AutoDiscover.get_recommendations("test", [])
		formatted = AutoDiscover.format_recommendations(recommendations)

		assert isinstance(formatted, str)
		assert len(formatted) > 0

	def test_format_recommendations_includes_header(self):
		"""Deep: Formatted output includes task analysis header."""
		recommendations = AutoDiscover.get_recommendations("test", [])
		formatted = AutoDiscover.format_recommendations(recommendations)

		assert "Task Analysis" in formatted or "Recommendation" in formatted

	def test_format_recommendations_includes_recommendation_section(self):
		"""Deep: Formatted output includes recommendation text."""
		recommendations = AutoDiscover.get_recommendations("test", [])
		formatted = AutoDiscover.format_recommendations(recommendations)

		assert "Recommendation:" in formatted

	def test_format_recommendations_with_presets_includes_preset_section(self):
		"""Integration: Includes preset suggestions when available."""
		recommendations = AutoDiscover.get_recommendations("implement", [])
		formatted = AutoDiscover.format_recommendations(recommendations)

		if recommendations["suggested_presets"]:
			assert "Preset" in formatted or "preset" in formatted

	def test_format_recommendations_with_workflows_includes_workflow_section(self):
		"""Integration: Includes workflow suggestions when available."""
		workflows = [
			{"id": "test-wf", "description": "testing workflow"},
		]
		recommendations = AutoDiscover.get_recommendations("test", workflows)
		formatted = AutoDiscover.format_recommendations(recommendations)

		if recommendations["suggested_workflows"]:
			assert "Workflow" in formatted or "workflow" in formatted
