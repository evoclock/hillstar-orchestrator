"""
Workflow Report Generator

Path
----
python/hillstar/utils/report.py

Purpose
-------
Generate pre-execution and post-execution markdown reports for workflows.

Reports include:
- Workflow metadata
- DAG visualization (Mermaid)
- Node specifications and costs
- Model selection strategy
- Governance/audit status
- Loon compression metrics

Inputs
------
workflow_path: Path to workflow JSON file
trace_path: Optional path to trace file for post-execution metrics

Outputs
-------
Markdown string with formatted report

Assumptions
-----------
- Workflow follows python/hillstar/schemas/workflow-schema.json
- Trace file is JSONL format with execution metrics
- Model costs available from ModelPresets

Failure Modes
-------------
- Missing workflow file → ValueError with clear message
- Missing trace file → Skip post-execution metrics gracefully
- Invalid workflow structure → Raise with helpful error

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-18

Last Edited
-----------
2026-02-18
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .loon import estimate_savings


class ReportGenerator:
    """Generate professional workflow execution reports."""

    def __init__(self, workflow_path: str):
        """Initialize with workflow file path."""
        self.workflow_path = Path(workflow_path)
        if not self.workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

        with open(self.workflow_path, 'r') as f:
            self.workflow = json.load(f)

        self.workflow_id = self.workflow.get("id", "unknown")
        self.description = self.workflow.get("description", "")

    def generate_pre_execution_report(self) -> str:
        """
        Generate pre-execution report with estimated costs and metadata.

        Returns:
            Markdown string ready for display or file output
        """
        sections = []

        # Metadata
        sections.append(self._metadata_section(status="Pre-execution"))

        # DAG Visualization
        sections.append(self._dag_section())

        # Node Table
        sections.append(self._node_table_section())

        # Model Selection
        sections.append(self._model_selection_section())

        # Cost Summary
        sections.append(self._cost_summary_section(actual_cost=None))

        # Loon Metrics
        loon_section = self._loon_metrics_section()
        if loon_section:
            sections.append(loon_section)

        # Governance
        sections.append(self._governance_section())

        return "\n\n".join(sections)

    def generate_post_execution_report(self, trace_path: str) -> str:
        """
        Generate post-execution report with actual execution metrics.

        Args:
            trace_path: Path to trace JSONL file from execution

        Returns:
            Markdown string with execution results
        """
        sections = []

        # Metadata
        sections.append(self._metadata_section(status="Completed"))

        # DAG Visualization
        sections.append(self._dag_section())

        # Node Table
        sections.append(self._node_table_section())

        # Model Selection
        sections.append(self._model_selection_section())

        # Parse trace for metrics
        trace_metrics = self._parse_trace_file(trace_path) if os.path.exists(trace_path) else None

        # Cost Summary with actual values
        actual_cost = trace_metrics.get("total_cost", 0) if trace_metrics else None
        sections.append(self._cost_summary_section(actual_cost=actual_cost))

        # Execution Results
        if trace_metrics:
            sections.append(self._execution_results_section(trace_metrics))

        # Loon Metrics
        loon_section = self._loon_metrics_section()
        if loon_section:
            sections.append(loon_section)

        # Governance
        sections.append(self._governance_section())

        return "\n\n".join(sections)

    def _metadata_section(self, status: str) -> str:
        """Generate metadata header section."""
        timestamp = datetime.now().isoformat()
        lines = [
            f"# Workflow Report: {self.workflow_id}",
            f"**Generated:** {timestamp}",
            f"**Status:** {status}",
        ]
        if self.description:
            lines.append(f"**Description:** {self.description}")

        return "\n".join(lines)

    def _dag_section(self) -> str:
        """Generate Mermaid DAG visualization."""
        mermaid = self._generate_mermaid_diagram()
        return f"## Workflow Structure\n\n```mermaid\n{mermaid}\n```"

    def _generate_mermaid_diagram(self) -> str:
        """Generate Mermaid diagram from workflow graph."""
        graph = self.workflow.get("graph", {})
        nodes = graph.get("nodes", {})
        edges = graph.get("edges", [])

        lines = ["graph TD"]

        # Add nodes with labels and colors (color by provider for better distinction)
        provider_colors = {
            "anthropic": "#6366f1",           # Indigo
            "openai": "#ec4899",              # Pink
            "mistral_mcp": "#f59e0b",         # Amber
            "devstral_local": "#10b981",      # Emerald
            "anthropic_ollama": "#8b5cf6",    # Violet
            "mistral": "#f59e0b",             # Amber
            "ollama": "#06b6d4",              # Cyan
        }

        for node_id, node_data in nodes.items():
            provider = node_data.get("provider", "unknown")

            # Get color based on provider
            color = provider_colors.get(provider, "#6b7280")  # Gray fallback

            # Clean, legible label - just the node ID
            lines.append(f'    {node_id}["{node_id}"]')
            lines.append(f"    style {node_id} fill:{color},stroke:#1f2937,stroke-width:2px,color:#fff")

        # Add edges
        for edge in edges:
            from_node = edge.get("from", "")
            to_node = edge.get("to", "")
            if from_node and to_node:
                lines.append(f"    {from_node} --> {to_node}")

        return "\n".join(lines)

    def _node_table_section(self) -> str:
        """Generate node specifications table."""
        graph = self.workflow.get("graph", {})
        nodes = graph.get("nodes", {})

        if not nodes:
            return "## Nodes\nNo nodes defined."

        lines = [f"## Nodes ({len(nodes)} nodes)"]
        lines.append("| ID | Tool | Provider | Model | Persona | Est. Cost |")
        lines.append("|---|---|---|---|---|---|")

        for node_id, node_data in nodes.items():
            tool = node_data.get("tool", "-")
            provider = node_data.get("provider", "-")
            model = node_data.get("model", "-")
            persona = node_data.get("persona", "-")
            cost = self._estimate_node_cost(node_data)

            lines.append(f"| {node_id} | {tool} | {provider} | {model} | {persona} | ${cost:.4f} |")

        return "\n".join(lines)

    def _model_selection_section(self) -> str:
        """Generate model selection strategy section."""
        model_config = self.workflow.get("model_config", {})
        mode = model_config.get("mode", "unknown")
        preset = model_config.get("preset", "unknown")
        complexity = model_config.get("complexity", "moderate")

        preset_descriptions = {
            "minimize_cost": "Select cheap models (Devstral, GPT-5-nano)",
            "balanced": "Select mid-range models for balanced cost/quality",
            "maximize_quality": "Use best models (Opus 4.6)",
            "local_only": "Local models only (air-gapped)",
        }
        strategy_desc = preset_descriptions.get(preset, "Custom strategy")

        lines = [
            "## Model Selection Strategy",
            f"- **Mode:** {mode}",
            f"- **Preset:** {preset}",
            f"- **Strategy:** {strategy_desc}",
            f"- **Complexity:** {complexity}",
        ]

        return "\n".join(lines)

    def _cost_summary_section(self, actual_cost: Optional[float] = None) -> str:
        """Generate cost summary section."""
        estimated_cost = self._total_estimated_cost()
        provider_breakdown = self._provider_cost_breakdown()

        lines = ["## Cost Summary"]

        if actual_cost is not None:
            lines.append(f"- **Estimated Total:** ${estimated_cost:.4f}")
            lines.append(f"- **Actual Total:** ${actual_cost:.4f}")
            if estimated_cost > 0:
                variance = ((actual_cost - estimated_cost) / estimated_cost * 100)
                lines.append(f"- **Variance:** {variance:+.1f}%")
        else:
            lines.append(f"- **Estimated Total:** ${estimated_cost:.4f}")

        if provider_breakdown:
            lines.append("- **Provider Breakdown:**")
            for provider, cost in provider_breakdown.items():
                pct = (cost / estimated_cost * 100) if estimated_cost > 0 else 0
                lines.append(f"  - {provider}: ${cost:.4f} ({pct:.0f}%)")

        return "\n".join(lines)

    def _execution_results_section(self, trace_metrics: Dict[str, Any]) -> str:
        """Generate execution results section (post-execution only)."""
        lines = ["## Execution Results"]
        lines.append(f"- **Status:** [OK] {trace_metrics.get('status', 'Unknown')}")
        if "duration" in trace_metrics:
            lines.append(f"- **Duration:** {trace_metrics['duration']}")
        if "tokens_used" in trace_metrics:
            lines.append(f"- **Total Tokens Used:** {trace_metrics['tokens_used']:,}")
        if "api_calls" in trace_metrics:
            calls = trace_metrics["api_calls"]
            lines.append(f"- **API Calls:** {calls}")
        if "trace_file" in trace_metrics:
            lines.append(f"- **Trace File:** `{trace_metrics['trace_file']}`")

        return "\n".join(lines)

    def _loon_metrics_section(self) -> Optional[str]:
        """Generate Loon compression metrics section."""
        try:
            metrics = estimate_savings(self.workflow)
            if metrics["savings_percent"] > 5:  # Only show if significant
                lines = [
                    "## Compression Metrics (Loon)",
                    f"- **Original JSON:** {metrics['original_chars']:,} bytes",
                    f"- **Compressed:** {metrics['compressed_chars']:,} bytes",
                    f"- **Savings:** {metrics['savings_percent']:.1f}%",
                    f"- **Estimated token savings:** {metrics['tokens_saved']} tokens",
                ]
                return "\n".join(lines)
        except Exception:
            pass
        return None

    def _governance_section(self) -> str:
        """Generate governance and audit section."""
        provider_config = self.workflow.get("provider_config", {})
        lines = ["## Governance & Audit"]

        # Check compliance flags
        all_compliant = True
        for provider, config in provider_config.items():
            if isinstance(config, dict):
                tos = config.get("tos_accepted", False)
                audit = config.get("audit_enabled", False)
                if not (tos and audit):
                    all_compliant = False

        if all_compliant and provider_config:
            lines.append("- **Compliance:** [OK] Accepted")
            lines.append("- **Audit Enabled:** [OK] Yes")
        else:
            lines.append("- **Compliance:** [WARN] Check provider_config")
            lines.append("- **Audit Enabled:** [WARN] Check settings")

        lines.append(f"- **Trace File Location:** `.hillstar/traces/{self.workflow_id}-*.jsonl`")

        return "\n".join(lines)

    def _parse_trace_file(self, trace_path: str) -> Dict[str, Any]:
        """
        Parse trace JSONL file to extract metrics.

        Args:
            trace_path: Path to trace file

        Returns:
            Dictionary with extracted metrics
        """
        metrics = {
            "status": "Unknown",
            "total_cost": 0,
            "tokens_used": 0,
            "api_calls": "0",
            "trace_file": trace_path,
        }

        try:
            if not os.path.exists(trace_path):
                return metrics

            lines = []
            with open(trace_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            lines.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

            if lines:
                # Check for completion marker
                for entry in lines:
                    if entry.get("event") == "execution_complete":
                        metrics["status"] = "Completed"
                        if "result" in entry:
                            result = entry["result"]
                            metrics["total_cost"] = result.get("total_cost", 0)
                            metrics["tokens_used"] = result.get("tokens_used", 0)

                # Count provider calls
                provider_calls = {}
                for entry in lines:
                    if entry.get("event") == "model_call":
                        provider = entry.get("provider", "unknown")
                        provider_calls[provider] = provider_calls.get(provider, 0) + 1

                if provider_calls:
                    total = sum(provider_calls.values())
                    call_str = f"{total} ("
                    call_str += ", ".join(f"{p}: {c}" for p, c in provider_calls.items())
                    call_str += ")"
                    metrics["api_calls"] = call_str

                # Extract duration if available
                start_time = None
                end_time = None
                for entry in lines:
                    if entry.get("event") == "execution_start" and not start_time:
                        start_time = entry.get("timestamp")
                    if entry.get("event") == "execution_complete" and not end_time:
                        end_time = entry.get("timestamp")

                if start_time and end_time:
                    try:
                        from datetime import datetime
                        start = datetime.fromisoformat(start_time)
                        end = datetime.fromisoformat(end_time)
                        duration = end - start
                        metrics["duration"] = str(duration).split('.')[0]
                    except Exception:
                        pass

        except Exception:
            pass

        return metrics

    def _estimate_node_cost(self, node_data: Dict[str, Any]) -> float:
        """
        Estimate cost for a single node.

        Args:
            node_data: Node configuration from workflow

        Returns:
            Estimated cost in USD
        """
        provider = node_data.get("provider")
        model = node_data.get("model")

        if not provider or not model:
            return 0.0

        # Simplified cost estimation - would use ModelPresets in production
        model_costs = {
            "claude-opus": 0.015,
            "claude-sonnet": 0.003,
            "claude-haiku": 0.00025,
            "gpt-4o": 0.003,
            "gpt-4-turbo": 0.01,
            "gpt-5": 0.0001,
            "mistral-large": 0.0024,
            "devstral": 0.0,
        }

        # Find matching model
        for key, cost in model_costs.items():
            if key in model.lower():
                return cost

        # Default small cost for unknown models
        return 0.0005

    def _total_estimated_cost(self) -> float:
        """Calculate total estimated cost across all nodes."""
        graph = self.workflow.get("graph", {})
        nodes = graph.get("nodes", {})

        total = 0.0
        for node_data in nodes.values():
            total += self._estimate_node_cost(node_data)

        return total

    def _provider_cost_breakdown(self) -> Dict[str, float]:
        """Get cost breakdown by provider."""
        graph = self.workflow.get("graph", {})
        nodes = graph.get("nodes", {})

        breakdown = {}
        for node_data in nodes.values():
            provider = node_data.get("provider")
            if provider:
                cost = self._estimate_node_cost(node_data)
                breakdown[provider] = breakdown.get(provider, 0) + cost

        return breakdown


def generate_pre_execution_report(workflow_path: str) -> str:
    """
    Generate pre-execution report for a workflow.

    Args:
        workflow_path: Path to workflow JSON file

    Returns:
        Markdown string with report
    """
    generator = ReportGenerator(workflow_path)
    return generator.generate_pre_execution_report()


def generate_post_execution_report(workflow_path: str, trace_path: str) -> str:
    """
    Generate post-execution report for a workflow.

    Args:
        workflow_path: Path to workflow JSON file
        trace_path: Path to trace JSONL file

    Returns:
        Markdown string with report including execution metrics
    """
    generator = ReportGenerator(workflow_path)
    return generator.generate_post_execution_report(trace_path)
