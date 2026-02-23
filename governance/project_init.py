"""
Script
------
project_init.py

Path
----
python/hillstar/governance/project_init.py

Purpose
-------
Initialize Hillstar project structure with recommended directory layout.

Inputs
------
- project_path (str): Root directory of project to initialize

Outputs
-------
- Created .hillstar/ and workflows/ directories with subdirectories

Assumptions
-----------
- Project directory exists and is writable

Parameters
----------
- project_path: Project root (defaults to current directory)

Failure Modes
-------------
- No write permissions → PermissionError
- Invalid path → FileNotFoundError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-09

Last Edited
-----------
2026-02-17
"""

from pathlib import Path
from typing import Optional


def initialize_project_structure(project_path: Optional[str] = None) -> dict:
    """
    Initialize recommended directory structure for Hillstar projects.

    Creates:
    - .hillstar/ with subdirectories (traces, logs, audit, checkpoints, data_stores)
    - workflows/ with subdirectories (core, infrastructure)

    Args:
        project_path: Project root directory (defaults to current directory)

    Returns:
        Dictionary with created directories and initialization status
    """
    if project_path is None:
        project_path = "."

    project_root = Path(project_path).resolve()

    # Verify project root exists
    if not project_root.exists():
        raise FileNotFoundError(f"Project directory not found: {project_root}")

    if not project_root.is_dir():
        raise NotADirectoryError(f"Not a directory: {project_root}")

    created_dirs = []

    # Create .hillstar structure
    hillstar_subdirs = [
        project_root / ".hillstar" / "traces",
        project_root / ".hillstar" / "logs",
        project_root / ".hillstar" / "audit",
        project_root / ".hillstar" / "checkpoints",
        project_root / ".hillstar" / "data_stores",
    ]

    for directory in hillstar_subdirs:
        directory.mkdir(parents=True, exist_ok=True)
        if not any(d in created_dirs for d in [str(directory), str(directory.parent)]):
            created_dirs.append(str(directory))

    # Create workflows structure
    workflows_subdirs = [
        project_root / "workflows" / "core",
        project_root / "workflows" / "infrastructure",
    ]

    for directory in workflows_subdirs:
        directory.mkdir(parents=True, exist_ok=True)
        if not any(d in created_dirs for d in [str(directory), str(directory.parent)]):
            created_dirs.append(str(directory))

    # Create .gitignore entries if needed
    gitignore_path = project_root / ".gitignore"
    entries_to_add = [
        ".hillstar/traces/",
        ".hillstar/logs/",
        ".hillstar/checkpoints/",
        ".hillstar/data_stores/",
        ".hillstar/__pycache__/",
    ]

    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            existing = f.read()
        entries_to_add = [e for e in entries_to_add if e not in existing]

    if entries_to_add:
        with open(gitignore_path, "a") as f:
            f.write("\n# Hillstar execution artifacts (auto-generated)\n")
            for entry in entries_to_add:
                f.write(f"{entry}\n")
        created_dirs.append(str(gitignore_path))

    return {
        "project_root": str(project_root),
        "created_directories": created_dirs,
        "status": "success",
        "message": f"Initialized Hillstar project structure in {project_root}",
    }


if __name__ == "__main__":
    import sys
    import json

    project_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        result = initialize_project_structure(project_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=2))
        sys.exit(1)
