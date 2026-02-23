"""
Script
------
__init__.py

Path
----
python/hillstar/governance/__init__.py

Purpose
-------
Governance module: Enforce workflow-driven development by gating git commits
behind verified Hillstar workflow executions.

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-08

Last Edited
-----------
2026-02-08
"""

from .enforcer import GovernanceEnforcer
from .hooks import HookManager
from .policy import GovernancePolicy
from .compliance import verify_hillstar_compliance

__all__ = [
    "GovernanceEnforcer",
    "HookManager",
    "GovernancePolicy",
    "verify_hillstar_compliance",
]
