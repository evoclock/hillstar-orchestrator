# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Licence-header invariant test.

Every tracked Python source file must carry the AGPLv3 SPDX headers required by
the Section 7(b) author-attribution clause in the LICENSE file. This test is the
deterministic guard for that invariant: it walks the real tracked file set (via
git, so it cannot drift from what ships) and fails the moment a file is missing
either header.

Failure modes asserted (not just the happy path):
- a tracked .py with no SPDX-License-Identifier at all (the new-file-added case),
- a tracked .py whose identifier is not AGPL-3.0-or-later (e.g. a stray
  Apache/MIT header left over from before the relicence),
- a tracked .py missing the SPDX-FileCopyrightText author line (7(b) attribution).

Sufficiency rationale: the check reads only the first few lines of each file (the
header lives there by construction of the inserter), keying off git's tracked set
rather than a filesystem walk so untracked scratch files never trip it and a
newly committed file is always covered. It deliberately does not parse the full
SPDX grammar or licence text; the identifier string is the load-bearing token a
relicence regression would change, and matching it is enough to catch the
regression without reimplementing an SPDX parser.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_ID = "SPDX-License-Identifier: AGPL-3.0-or-later"
EXPECTED_COPYRIGHT = "SPDX-FileCopyrightText: 2026 Julen Gamboa"


def _tracked_py_files():
	out = subprocess.check_output(["git", "ls-files", "*.py"], cwd=REPO_ROOT, text=True)
	return [REPO_ROOT / line for line in out.split()]


def _header(path):
	return "".join(path.read_text().splitlines(keepends=True)[:6])


def test_every_python_file_has_agpl_spdx_identifier():
	"""Every tracked .py carries the AGPLv3 SPDX licence identifier."""
	missing = [
		str(p.relative_to(REPO_ROOT))
		for p in _tracked_py_files()
		if EXPECTED_ID not in _header(p)
	]
	assert not missing, f"tracked .py files missing {EXPECTED_ID!r}: {missing}"


def test_every_python_file_has_author_copyright_header():
	"""Every tracked .py carries the author SPDX-FileCopyrightText line (7(b))."""
	missing = [
		str(p.relative_to(REPO_ROOT))
		for p in _tracked_py_files()
		if EXPECTED_COPYRIGHT not in _header(p)
	]
	assert not missing, f"tracked .py files missing {EXPECTED_COPYRIGHT!r}: {missing}"
