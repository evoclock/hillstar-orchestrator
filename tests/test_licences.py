#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for scripts/check_licences.py."""

import subprocess
import sys


def run_classify(lic: str) -> int:
    """Run --classify with the given licence string and return exit code."""
    result = subprocess.run(
        [sys.executable, "scripts/check_licences.py", "--classify", lic],
        capture_output=True,
        text=True,
    )
    return result.returncode


def test_classify_allowed_licences() -> None:
    """Verify all AGPL-compatible licences classify ALLOWED (exit 0).

    Source of truth: ~/project-planning/commercial/dependency-license-audit.md
    Compatible: MIT, BSD-2/3-Clause, Apache-2.0, ISC, GPLv2-or-later, GPLv3, LGPL, MPL-2.0, AGPLv3, PSF
    """
    # These are the SPDX identifiers from the audit doc's Methodology section
    allowed = [
        "MIT",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "Apache-2.0",
        "ISC",
        "GPL-2.0-or-later",
        "GPL-3.0-or-later",
        "LGPL-2.1-or-later",
        "LGPL-3.0-or-later",
        "MPL-2.0",
        "AGPL-3.0-or-later",
        "PSF",
    ]
    for lic in allowed:
        code = run_classify(lic)
        assert code == 0, f"Expected ALLOWED (0) for '{lic}', got exit {code}"


def test_classify_blocked_licences() -> None:
    """Verify all AGPL-incompatible licences classify DENIED (non-zero).

    Source of truth: ~/project-planning/commercial/dependency-license-audit.md
    Incompatible: GPLv2-only, BSD-4-Clause, proprietary, SSPL, Commons Clause,
                  BSL/Elastic-2.0, OpenRAIL-*, Llama/Stability/Gemma
    """
    # These are the blocked identifiers from the audit doc's Methodology section
    blocked = [
        "GPL-2.0-only",
        "BSD-4-Clause",
        "proprietary",
        "SSPL",
        "Commons Clause",
        "BSL-1.0",
        "Elastic-2.0",
        "OpenRAIL-M",
        "OpenRAIL-LLC",
        "Llama-2-Community",
        "Llama-3-Community",
        "Stability-1.0",
        "Gemma-1.0",
    ]
    for lic in blocked:
        code = run_classify(lic)
        assert code != 0, f"Expected DENIED (non-zero) for '{lic}', got exit {code}"


if __name__ == "__main__":
    # Run as a script for quick manual verification
    print("Running allowed-licence tests...")
    test_classify_allowed_licences()
    print("  PASS")

    print("Running blocked-licence tests...")
    test_classify_blocked_licences()
    print("  PASS")

    print("All tests passed.")
