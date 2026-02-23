"""
Script
------
auto_discover.py

Path
----
python/hillstar/auto_discover.py

Purpose
-------
Auto-discovery mechanism to detect Hillstar projects and suggest workflows.

Detects if current directory is a Hillstar project and finds available workflows.
Used by Claude Code to automatically offer Hillstar integration.

Inputs
------
current_dir (str): Directory to check (default: current working directory)
task_description (str): Natural language task description
workflows (List[Dict]): Workflow metadata to search

Outputs
-------
is_hillstar_project (bool): True if directory is Hillstar project
suggested_workflows (List[Dict]): Matching workflows ranked by relevance
workflow_suggestions (Dict): Workflow recommendations with confidence scores

Assumptions
-----------
- Workflow files exist and are valid JSON
- Workflow descriptions are informative
- Task descriptions follow natural language patterns

Parameters
----------
None (per-operation)

Failure Modes
-------------
- No workflows found → Empty list
- Invalid task description → Return all workflows
- Directory not found → False

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
"""

import os
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple


class AutoDiscover:
    """Auto-detect Hillstar projects and suggest workflows."""

    # Keywords for task type detection
    PLANNING_KEYWORDS = ['plan', 'design', 'analyze', 'review', 'investigate', 'explore', 'study']
    IMPLEMENTATION_KEYWORDS = ['implement', 'build', 'create', 'develop', 'code', 'write', 'script']
    TESTING_KEYWORDS = ['test', 'validate', 'verify', 'check', 'quality', 'qa', 'audit']
    QUALITY_KEYWORDS = ['quality', 'accuracy', 'precision', 'reproducibility', 'thorough', 'careful']
    BUDGET_KEYWORDS = ['budget', 'cost', 'cheap', 'free', 'minimize', 'save']
    LOCAL_KEYWORDS = ['local', 'offline', 'airgap', 'air-gapped', 'sensitive', 'private']
    SPEED_KEYWORDS = ['fast', 'quick', 'speed', 'performance', 'efficiency', 'rapid']

    @staticmethod
    def is_hillstar_project(start_dir: str = '.') -> bool:
        """
        Detect if a directory is a Hillstar project.

        Args:
            start_dir: Directory to check (default: current)

        Returns:
            True if Hillstar project indicators found

        Indicators:
            - python/hillstar/ directory (source or pip installation)
            - .hillstar/ directory (runtime artifacts)
            - workflow.json in current or subdirectories (workflow definition)
        """
        current_dir = os.path.abspath(start_dir)

        # Never treat /tmp as a project directory
        if current_dir.startswith('/tmp'):
            return False

        indicators = [
            os.path.join(current_dir, 'python/hillstar'),  # Source installation
            os.path.join(current_dir, '.hillstar'),        # Runtime artifacts
            os.path.join(current_dir, 'workflow.json'),    # Workflow definition
        ]

        for indicator in indicators:
            if os.path.exists(indicator):
                return True

        # Check subdirectories for workflow.json
        for root, dirs, files in os.walk(current_dir):
            if 'workflow.json' in files:
                return True

            # Don't go too deep
            if root.count(os.sep) - current_dir.count(os.sep) > 3:
                break

        return False

    @staticmethod
    def get_project_info(start_dir: str = '.') -> Dict[str, Any]:
        """
        Get Hillstar project information.

        Args:
            start_dir: Directory to analyze

        Returns:
            Dictionary with:
            - is_hillstar: bool
            - has_schema: bool
            - has_artifacts: bool
            - has_workflows: bool
            - workflow_count: int
            - schema_path: str or None
        """
        current_dir = os.path.abspath(start_dir)

        schema_path = os.path.join(current_dir, 'python/hillstar/schemas/workflow-schema.json')
        artifacts_path = os.path.join(current_dir, '.hillstar')

        has_schema = os.path.exists(schema_path)
        # Also check for pip-installed version
        if not has_schema:
            try:
                from importlib.resources import files
                has_schema = True  # If importlib succeeds, schema is available
                schema_path = "hillstar.schemas.workflow-schema.json (installed package)"
            except Exception:
                pass
        has_artifacts = os.path.exists(artifacts_path)

        # Count workflows
        workflow_count = 0
        for root, dirs, files in os.walk(current_dir):
            if 'workflow.json' in files:
                workflow_count += 1
            if root.count(os.sep) - current_dir.count(os.sep) > 3:
                break

        has_workflows = workflow_count > 0

        return {
            'is_hillstar': has_schema or has_artifacts or has_workflows,
            'has_schema': has_schema,
            'has_artifacts': has_artifacts,
            'has_workflows': has_workflows,
            'workflow_count': workflow_count,
            'schema_path': schema_path if has_schema else None,
        }

    @staticmethod
    def classify_task(task_description: str) -> Dict[str, float]:
        """
        Classify task by keywords to infer requirements.

        Args:
            task_description: Natural language task description

        Returns:
            Dictionary with task type scores:
            - planning: float (0.0-1.0)
            - implementation: float
            - testing: float
            - quality: float
            - budget_conscious: float
            - local_only: float
            - speed_critical: float
        """
        text = task_description.lower()

        def count_keywords(keywords: List[str]) -> int:
            count = 0
            for keyword in keywords:
                count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            return count

        planning_score = count_keywords(AutoDiscover.PLANNING_KEYWORDS)
        impl_score = count_keywords(AutoDiscover.IMPLEMENTATION_KEYWORDS)
        testing_score = count_keywords(AutoDiscover.TESTING_KEYWORDS)
        quality_score = count_keywords(AutoDiscover.QUALITY_KEYWORDS)
        budget_score = count_keywords(AutoDiscover.BUDGET_KEYWORDS)
        local_score = count_keywords(AutoDiscover.LOCAL_KEYWORDS)
        speed_score = count_keywords(AutoDiscover.SPEED_KEYWORDS)

        # Normalize scores
        total = max(
            planning_score + impl_score + testing_score + quality_score +
            budget_score + local_score + speed_score,
            1
        )

        return {
            'planning': planning_score / total,
            'implementation': impl_score / total,
            'testing': testing_score / total,
            'quality': quality_score / total,
            'budget_conscious': budget_score / total,
            'local_only': local_score / total,
            'speed_critical': speed_score / total,
        }

    @staticmethod
    def get_preset_suggestions(task_scores: Dict[str, float]) -> List[Tuple[str, float]]:
        """
        Suggest presets based on task classification.

        Args:
            task_scores: Task classification scores

        Returns:
            List of (preset_name, confidence) tuples, sorted by confidence
        """
        suggestions = []

        # Logic for suggesting presets based on task characteristics
        if task_scores['local_only'] > 0.3:
            suggestions.append(('local_only', task_scores['local_only']))

        if task_scores['budget_conscious'] > 0.3:
            suggestions.append(('minimize_cost', task_scores['budget_conscious']))

        if task_scores['quality'] > 0.4:
            suggestions.append(('maximize_quality', task_scores['quality']))

        # Balanced is default
        if not suggestions:
            suggestions.append(('balanced', 0.5))

        # Sort by confidence
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions

    @staticmethod
    def _similarity_score(text1: str, text2: str) -> float:
        """Calculate string similarity score (0.0-1.0)."""
        text1 = text1.lower()
        text2 = text2.lower()
        return SequenceMatcher(None, text1, text2).ratio()

    @staticmethod
    def suggest_workflows(
        task_description: str,
        workflows: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Suggest workflows based on task description.

        Args:
            task_description: Natural language task
            workflows: Available workflow metadata
            top_k: Return top K matches

        Returns:
            List of suggested workflows with relevance scores, sorted best-first
        """
        if not workflows:
            return []

        suggestions = []

        for workflow in workflows:
            score = 0.0

            # Match against workflow ID
            id_match = AutoDiscover._similarity_score(
                task_description,
                workflow.get('id', '')
            )
            score += id_match * 0.3

            # Match against workflow description
            desc = workflow.get('description', '')
            desc_match = AutoDiscover._similarity_score(
                task_description,
                desc
            )
            score += desc_match * 0.5

            # Bonus for preset match
            preset = workflow.get('preset')
            if preset:
                task_scores = AutoDiscover.classify_task(task_description)
                preset_suggestions = AutoDiscover.get_preset_suggestions(task_scores)
                preset_names = [p[0] for p in preset_suggestions]
                if preset in preset_names:
                    score += 0.2

            # Bonus for mode match
            mode = workflow.get('mode', 'explicit')
            if mode in ['auto', 'preset']:
                score += 0.1

            if score > 0:
                suggestions.append({
                    'workflow': workflow,
                    'relevance_score': score,
                })

        # Sort by relevance score
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Return top K
        return [s['workflow'] for s in suggestions[:top_k]]

    @staticmethod
    def get_recommendations(
        task_description: str,
        workflows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Get comprehensive recommendations for a task.

        Args:
            task_description: Natural language task
            workflows: Available workflows

        Returns:
            Dictionary with:
            - task_classification: Task type scores
            - suggested_presets: List of (preset, confidence) tuples
            - suggested_workflows: List of matching workflows
            - recommendation_text: Human-readable summary
        """
        task_scores = AutoDiscover.classify_task(task_description)
        preset_suggestions = AutoDiscover.get_preset_suggestions(task_scores)
        workflow_suggestions = AutoDiscover.suggest_workflows(
            task_description,
            workflows,
            top_k=3
        )

        # Generate recommendation text
        recommendation_parts = []

        if task_scores['local_only'] > 0.3:
            recommendation_parts.append("Local-only execution recommended (sensitive data)")

        if task_scores['budget_conscious'] > 0.3:
            recommendation_parts.append("Cost optimization recommended")

        if task_scores['quality'] > 0.4:
            recommendation_parts.append("Quality-focused approach recommended")

        if workflow_suggestions:
            best_workflow = workflow_suggestions[0]
            recommendation_parts.append(
                f"Best match: '{best_workflow.get('id')}' workflow"
            )

        if preset_suggestions:
            best_preset = preset_suggestions[0]
            recommendation_parts.append(
                f"Suggested preset: {best_preset[0]}"
            )

        recommendation_text = '. '.join(recommendation_parts)
        if not recommendation_text:
            recommendation_text = "No specific recommendations. You may use any available preset."

        return {
            'task_classification': task_scores,
            'suggested_presets': preset_suggestions,
            'suggested_workflows': workflow_suggestions,
            'recommendation_text': recommendation_text,
        }

    @staticmethod
    def format_recommendations(recommendations: Dict[str, Any]) -> str:
        """
        Format recommendations as human-readable text.

        Args:
            recommendations: Output from get_recommendations()

        Returns:
            Formatted text suitable for display to user
        """
        lines = []

        lines.append(" Task Analysis & Recommendations")
        lines.append("")

        # Task classification
        task_class = recommendations['task_classification']
        if max(task_class.values()) > 0.2:
            lines.append(" Task Characteristics:")
            for key, value in task_class.items():
                if value > 0.15:
                    pct = int(value * 100)
                    lines.append(f"  • {key.replace('_', ' ').title()}: {pct}%")
            lines.append("")

        # Suggested presets
        presets = recommendations['suggested_presets']
        if presets:
            lines.append("🎮 Model Selection Presets:")
            for preset_name, confidence in presets[:2]:
                confidence_pct = int(confidence * 100)
                lines.append(f"  • {preset_name} ({confidence_pct}% fit)")
            lines.append("")

        # Suggested workflows
        workflows = recommendations['suggested_workflows']
        if workflows:
            lines.append("⚙️  Suggested Workflows:")
            for i, workflow in enumerate(workflows[:3], 1):
                workflow_id = workflow.get('id', 'unknown')
                description = workflow.get('description', 'No description')
                lines.append(f"  {i}. {workflow_id}")
                lines.append(f"     {description}")
            lines.append("")

        # Overall recommendation
        lines.append("💡 Recommendation:")
        lines.append(f"  {recommendations['recommendation_text']}")

        return '\n'.join(lines)
