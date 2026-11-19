# SPDX-FileCopyrightText: 2026 Julen Gamboa
# SPDX-License-Identifier: AGPL-3.0-only

"""Regression test for the installed CLI version."""

import subprocess
from importlib.metadata import version


def test_cli_version_matches_distribution():
	result = subprocess.run(['hillstar', '--version'], capture_output=True, text=True, check=True)
	assert result.stdout.strip() == f'hillstar {version("hillstar-orchestrator")}'
