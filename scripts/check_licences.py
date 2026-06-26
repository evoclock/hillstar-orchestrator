#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

""" licence-checker: AGPLv3-compatible dependency gate.

Two modes:
  --classify "<licence>":  exit 0 if AGPL-compatible, non-zero if not.
  --check:  introspect the built env and exit non-zero on any disallowed dep.

Allow-list source of truth: ~/project-planning/commercial/dependency-license-audit.md
Compatible: MIT, BSD-2/3-Clause, Apache-2.0, ISC, GPLv2-or-later, GPLv3, LGPL, MPL-2.0, AGPLv3, PSF
Incompatible: GPLv2-only, BSD-4-Clause, proprietary, SSPL, Commons Clause, BSL/Elastic-2.0, OpenRAIL-*, Llama/Stability/Gemma
"""

from __future__ import annotations

import argparse
import sys
from typing import List


def _normalise_licence(lic: str) -> str:
    """Normalise a licence string for comparison."""
    # Strip common prefixes/suffixes
    lic = lic.strip()
    # Normalize spacing
    lic = " ".join(lic.split())
    # Remove trailing "-or-later" to match against base identifiers
    if lic.endswith("-or-later"):
        lic = lic[:-7]
    return lic


# Allowed licence identifiers (base identifiers without "-or-later" suffix)
ALLOWED_LICENCES = frozenset({
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "Apache-2.0",
    "ISC",
    "GPL-2.0",
    "GPL-3.0",
    "LGPL-2.1",
    "LGPL-3.0",
    "MPL-2.0",
    "AGPL-3.0",
    "PSF",
})

# Blocked licence patterns (exact or prefix for families)
BLOCKED_LICENCES = frozenset({
    "GPL-2.0-only",
    "BSD-4-Clause",
    "proprietary",
    "SSPL",
    "Commons Clause",
    "BSL-1.0",
    "Elastic-2.0",
    "OpenRAIL",
    "Llama-2-Community",
    "Llama-3-Community",
    "Stability-1.0",
    "Gemma-1.0",
})


def classify_licence(lic: str) -> bool:
    """Return True if AGPL-compatible, False otherwise."""
    norm = _normalise_licence(lic)

    # Check blocked first (explicit denies)
    for blocked in BLOCKED_LICENCES:
        if norm == blocked or norm.startswith(blocked):
            return False

    # Check allowed
    for allowed in ALLOWED_LICENCES:
        if norm == allowed or norm.startswith(allowed):
            return True

    # Unknown: block by default
    return False


def get_dependencies() -> List[tuple[str, str]]:
    """Return (name, licence) of installed dependencies.

    Tries importlib.metadata first (PEP 566), falls back to pip-licenses.
    """
    try:
        import importlib.metadata as metadata
    except ImportError:
        import importlib_metadata as metadata  # type: ignore

    deps: List[tuple[str, str]] = []
    for dist in metadata.distributions():
        name = dist.metadata.get("Name", dist.metadata["Name"])
        lic = dist.metadata.get("License", "") or ""
        # Some packages store licence as a classifer
        if not lic:
            classifiers = dist.metadata.get_all("Classifier") or []
            for c in classifiers:
                if c.startswith("License :: "):
                    # Extract the identifier portion
                    # e.g., "License :: OSI Approved :: MIT License" -> "MIT License"
                    lic = c.replace("License :: ", "").replace(" :: ", " ")
                    break
        deps.append((str(name), str(lic).strip()))
    return deps


def check_env() -> int:
    """Check all installed dependencies for AGPL compatibility.

    Returns 0 if all compatible, 1 otherwise.
    """
    deps = get_dependencies()
    bad: List[tuple[str, str]] = []

    for name, lic in deps:
        if not classify_licence(lic):
            bad.append((name, lic))

    if bad:
        print("Disallowed dependencies:", file=sys.stderr)
        for name, lic in bad:
            print(f"  {name}: {lic}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AGPL-compatible dependency gate"
    )
    parser.add_argument(
        "--classify",
        metavar="LICENCE",
        help="Classify a licence string (exit 0 if allowed, 1 if blocked)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Introspect the built environment and check all dependencies",
    )
    args = parser.parse_args()

    if args.classify is not None:
        allowed = classify_licence(args.classify)
        sys.exit(0 if allowed else 1)

    if args.check:
        return check_env()

    parser.error("One of --classify or --check is required")
    return 1


if __name__ == "__main__":
    sys.exit(main())
