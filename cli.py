"""
Script
------
cli.py

Path
----
python/hillstar/cli.py

Purpose
-------
Command-line interface for workflow orchestration.

Usage
-----
    hillstar discover [PATH]              Find workflows in current or specified directory
    hillstar validate WORKFLOW_PATH       Validate a workflow
    hillstar execute WORKFLOW_PATH [DIR]  Execute a workflow
    hillstar presets                      List available presets
    hillstar wizard                       Run interactive setup wizard
    hillstar mode dev|normal              Set development mode for commits
    hillstar enforce check|status|...     Governance enforcement
    hillstar loon reduce WORKFLOW          Reduce workflow to Loon format
    hillstar loon expand LOON              Expand Loon back to standard format
    hillstar loon estimate WORKFLOW        Estimate token savings
    hillstar execute-node WORKFLOW NODE   Execute a single node
    hillstar --version                    Show version
    hillstar --help                       Show this help message

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-17
"""

import sys
import os
import json
import argparse

from .workflows import WorkflowDiscovery, WorkflowValidator, ModelPresets
from .execution import WorkflowRunner
from .config import SetupWizard
from .utils import HillstarException
from .governance import GovernanceEnforcer, HookManager


def cmd_discover(args):
    """Find workflows in a directory."""
    start_path = args.path or '.'

    print(f"[SEARCH] Discovering workflows in: {os.path.abspath(start_path)}\n")

    workflows = WorkflowDiscovery.get_all_workflow_info(start_path, max_depth=4)

    if not workflows:
        print(" No workflows found")
        return 1

    print(f" Found {len(workflows)} workflow(s):\n")

    for workflow in workflows:
        print(f"  {workflow['id']}")
        print(f"    Path:     {workflow['path']}")
        print(f"    Nodes:    {workflow['node_count']} nodes, {workflow['edge_count']} edges")
        print(f"    Mode:     {workflow['mode']}")
        if workflow['preset']:
            print(f"    Preset:   {workflow['preset']}")
        if workflow['has_budget']:
            print("    Budget:   [x] configured")
        if workflow['uses_custom_provider']:
            print("    Custom:   [x] uses custom providers")
        print()

    return 0


def cmd_validate(args):
    """Validate a workflow."""
    workflow_path = args.workflow_path

    if not os.path.exists(workflow_path):
        print(f" Workflow file not found: {workflow_path}")
        return 1

    print(f"[SEARCH] Validating: {os.path.abspath(workflow_path)}\n")

    valid, errors = WorkflowValidator.validate_file(workflow_path)

    if valid:
        print(" Workflow is valid\n")

        # Show metadata
        with open(workflow_path) as f:
            workflow = json.load(f)

        print(f"  ID:          {workflow.get('id', 'unknown')}")
        print(f"  Description: {workflow.get('description', '(none)')}")
        print(f"  Nodes:       {len(workflow.get('graph', {}).get('nodes', {}))}")
        print(f"  Edges:       {len(workflow.get('graph', {}).get('edges', []))}")

        model_config = workflow.get('model_config', {})
        if model_config:
            print(f"  Mode:        {model_config.get('mode', 'explicit')}")
            if model_config.get('preset'):
                print(f"  Preset:      {model_config.get('preset')}")
            if model_config.get('budget'):
                budget = model_config['budget']
                if budget.get('max_workflow_usd'):
                    print(f"  Budget:      ${budget.get('max_workflow_usd'):.2f} total")


        return 0
    else:
        print(" Workflow has errors:\n")
        for error in errors:
            print(f"   {error}")
        print()
        return 1


def cmd_execute(args):
    """Execute a workflow."""
    workflow_path = args.workflow_path
    output_dir = args.output_dir or '.hillstar'

    if not os.path.exists(workflow_path):
        print(f" Workflow file not found: {workflow_path}")
        return 1

    # Validate first
    valid, errors = WorkflowValidator.validate_file(workflow_path)
    if not valid:
        print("[!] Workflow validation failed:\n")
        for error in errors:
            print(f"  [-] {error}")
        print()
        return 1

    print(f"[RUN]  Executing: {os.path.abspath(workflow_path)}")
    print(f"[DIR] Output:    {os.path.abspath(output_dir)}")
    print("ℹ️  COMPLIANCE NOTICE: All cloud providers use API authentication. Users are responsible for provider ToS compliance.")
    print()

    try:
        runner = WorkflowRunner(workflow_path, output_dir)
        result = runner.execute(resume_from=args.resume_from)

        print("[x] Workflow executed successfully\n")
        print(f"  Workflow ID: {result.get('workflow_id')}")
        print(f"  Trace file:  {result.get('trace_file')}")

        cost = result.get('cumulative_cost_usd', 0)
        if cost:
            print(f"  Cost:        ${cost:.4f}")

        return 0

    except Exception as e:
        print(f" Execution failed: {str(e)}\n")
        return 1


# ===== Phase 2 Features (deferred, not in v1.0.0) =====
#
# def cmd_diagram(args):
#     """Display DAG diagram of a workflow."""
#     workflow_path = args.workflow_path
#
#     if not os.path.exists(workflow_path):
#         print(f" Workflow file not found: {workflow_path}")
#         return 1
#
#     try:
#         with open(workflow_path) as f:
#             workflow = json.load(f)
#     except json.JSONDecodeError:
#         print(f" Invalid JSON in {workflow_path}")
#         return 1
#
#     print(DAGVisualizer.generate_mermaid_markdown(workflow, include_title=True))
#     print()
#     print("ℹ️  This diagram can be copied into Markdown, GitHub, or Claude Code.")
#     print()
#
#     if args.summary:
#         print(DAGVisualizer.print_summary(workflow))
#
#     if args.save:
#         md_path = os.path.splitext(os.path.abspath(workflow_path))[0] + ".md"
#         doc = DAGVisualizer.generate_companion_doc(workflow, workflow_path)
#         with open(md_path, "w", encoding="utf-8") as f:
#             f.write(doc)
#         print(f"📄 Companion doc saved: {md_path}")
#
#     return 0


# PHASE 2: Report generation
# def cmd_report(args):
#     """Generate workflow execution report."""
#     ...deferred to Phase 2...


def cmd_presets(args):
    """List available presets."""
    print(" Available Presets:\n")

    presets = ModelPresets.get_available_presets()

    for preset_name in presets:
        desc = ModelPresets.describe_preset(preset_name)
        print(f"  {preset_name}")
        print(f"    {desc.get('description')}")
        print(f"    Use case: {desc.get('use_case')}")
        print()

    return 0


def cmd_enforce(args):
    """Governance enforcement commands."""
    hillstar_dir = args.hillstar_dir or '.hillstar'
    enforcer = GovernanceEnforcer(hillstar_dir)
    hook_manager = HookManager(args.project_dir or '.')

    if args.enforce_command == 'check':
        dev_mode = getattr(args, 'dev', False)
        compliant, reason = enforcer.check(dev_mode=dev_mode)
        if compliant:
            print(f" {reason}")
            return 0
        else:
            print(f" {reason}")
            return 1

    elif args.enforce_command == 'status':
        status = enforcer.status()
        hook_status = hook_manager.status()
        print("Governance status:")
        print(f"  Compliant:    {' yes' if status['compliant'] else ' no'}")
        print(f"  Reason:       {status['reason']}")
        if status['marker']:
            m = status['marker']
            print(f"  Last workflow: {m.get('workflow_id', 'unknown')} ({m.get('workflow_file', '')})")
            print(f"  Executed at:   {m.get('executed_at', 'unknown')}")
        print(f"  Hook installed: {' yes' if hook_status['is_installed'] else ' no'}")
        print(f"  Max age:       {status['policy']['max_age_seconds']}s")
        return 0

    elif args.enforce_command == 'install':
        success, msg = hook_manager.install(force=args.force)
        print(f"{'' if success else ''} {msg}")
        return 0 if success else 1

    elif args.enforce_command == 'uninstall':
        success, msg = hook_manager.uninstall()
        print(f"{'' if success else ''} {msg}")
        return 0 if success else 1

    else:
        print("Usage: hillstar enforce {check|status|install|uninstall}")
        return 1


def cmd_wizard(args):
    """Run setup wizard."""
    print("🧙 Hillstar Setup Wizard\n")
    print("This will configure your local model provider.\n")

    try:
        wizard = SetupWizard()
        wizard.run()
        print("\n Configuration saved to ~/.hillstar/user_config.json")
        return 0
    except KeyboardInterrupt:
        print("\n⏸  Setup cancelled")
        return 1
    except Exception as e:
        print(f"\n Setup failed: {str(e)}")
        return 1


def cmd_mode(args):
    """Set development mode for development commits."""
    mode = args.mode
    hillstar_dir = args.hillstar_dir or '.hillstar'
    dev_mode_file = os.path.join(hillstar_dir, 'dev_mode_active')

    if mode == 'dev':
        os.makedirs(hillstar_dir, exist_ok=True)
        with open(dev_mode_file, 'w') as f:
            f.write('development mode active for git commits\n')
        print("Development mode enabled")
        print("Run: git commit -m \"message\"")
        return 0
    elif mode == 'normal':
        if os.path.exists(dev_mode_file):
            os.remove(dev_mode_file)
        print("Development mode disabled")
        return 0
    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: dev, normal")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='hillstar',
        description='Hillstar workflow orchestration CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hillstar discover                       # Find workflows in current directory
  hillstar validate workflow.json         # Validate a workflow
  hillstar validate workflow.json --diagram # Validate and show DAG diagram
  hillstar diagram workflow.json          # Display workflow DAG (Mermaid)
  hillstar diagram workflow.json --summary # Show diagram with execution order
  hillstar execute workflow.json          # Execute a workflow
  hillstar mode dev                       # Enable development mode
  git commit -m "message"                 # Commit (works with dev mode active)
  hillstar mode normal                    # Disable development mode (require workflow)
  hillstar presets                        # List available presets
  hillstar wizard                         # Setup local model provider
        """
    )

    parser.add_argument('--version', action='version', version='hillstar 1.0.0')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # discover command
    discover_parser = subparsers.add_parser('discover', help='Find workflows')
    discover_parser.add_argument('path', nargs='?', default=None, help='Directory to search (default: current)')
    discover_parser.set_defaults(func=cmd_discover)

    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a workflow')
    validate_parser.add_argument('workflow_path', help='Path to workflow.json')
    validate_parser.add_argument('--diagram', action='store_true', help='Show Mermaid DAG diagram')
    validate_parser.set_defaults(func=cmd_validate)

    # execute command
    execute_parser = subparsers.add_parser('execute', help='Execute a workflow')
    execute_parser.add_argument('workflow_path', help='Path to workflow.json')
    execute_parser.add_argument('output_dir', nargs='?', default=None, help='Output directory (default: .hillstar)')
    execute_parser.add_argument('--resume-from', type=str, default=None, help='Resume from checkpoint (path to checkpoint file or node_id)')
    execute_parser.set_defaults(func=cmd_execute)

    # PHASE 2: diagram and report commands deferred

    # enforce command
    enforce_parser = subparsers.add_parser('enforce', help='Governance enforcement')
    enforce_parser.add_argument('enforce_command', choices=['check', 'status', 'install', 'uninstall'],
                                help='check: verify compliance | status: show full status | install/uninstall: manage git hook')
    enforce_parser.add_argument('--hillstar-dir', default=None, help='Path to .hillstar dir (default: .hillstar)')
    enforce_parser.add_argument('--project-dir', default=None, help='Path to project root (default: .)')
    enforce_parser.add_argument('--force', action='store_true', help='Force overwrite existing hook')
    enforce_parser.add_argument('--dev', action='store_true', help='Development mode: skip governance check')
    enforce_parser.set_defaults(func=cmd_enforce)

    # presets command
    presets_parser = subparsers.add_parser('presets', help='List available presets')
    presets_parser.set_defaults(func=cmd_presets)

    # PHASE 2: loon command deferred

    # execute-node command
    execute_node_parser = subparsers.add_parser('execute-node', help='Execute a single workflow node')
    execute_node_parser.add_argument('workflow_path', help='Path to workflow JSON file')
    execute_node_parser.add_argument('node_id', help='Node ID to execute')
    execute_node_parser.add_argument('--inputs', type=str, default='{}', help='Node inputs as JSON')
    execute_node_parser.set_defaults(func=cmd_execute_node)


    # wizard command
    wizard_parser = subparsers.add_parser('wizard', help='Run setup wizard')
    wizard_parser.set_defaults(func=cmd_wizard)

    # mode command
    mode_parser = subparsers.add_parser('mode', help='Set development mode for commits')
    mode_parser.add_argument('mode', choices=['dev', 'normal'], help='dev: enable development mode | normal: disable development mode')
    mode_parser.add_argument('--hillstar-dir', default=None, help='Path to .hillstar dir (default: .hillstar)')
    mode_parser.set_defaults(func=cmd_mode)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except HillstarException as e:
        print(f" Error: {str(e)}")
        return 1
    except Exception as e:
        print(f" Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1



# PHASE 2 FEATURE: Loon commands deferred (cmd_loon_reduce, cmd_loon_expand, cmd_loon_estimate)


def cmd_execute_node(args):
    """Execute a single node from a workflow."""
    workflow_path = args.workflow_path
    node_id = args.node_id

    try:
        inputs = json.loads(args.inputs)
    except json.JSONDecodeError:
        print(f"\n[ERROR] Invalid JSON in --inputs: {args.inputs}\n")
        return 1

    if not os.path.exists(workflow_path):
        print(f" Workflow file not found: {workflow_path}")
        return 1

    try:
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)

        # Find the node
        node = None
        for n in workflow.get('graph', {}).get('nodes', []):
            if n.get('id') == node_id:
                node = n
                break

        if not node:
            print(f"\n[ERROR] Node '{node_id}' not found in workflow\n")
            return 1

        # Create runner and execute node
        output_dir = '.hillstar'
        runner = WorkflowRunner(workflow_path, output_dir)
        result = runner.execute_node(node_id, node, inputs)

        print("\n[OK] Node executed successfully:")
        print(f"  Node ID:     {node_id}")
        print(f"  Result type: {type(result).__name__}")
        if isinstance(result, dict):
            print(f"  Result:      {json.dumps(result, indent=2)}")
        else:
            print(f"  Result:      {result}")
        print()

        return 0

    except Exception as e:
        print(f"\n[ERROR] Node execution failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1
if __name__ == '__main__':
    sys.exit(main())
