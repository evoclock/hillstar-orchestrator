# SPDX-FileCopyrightText: 2026 evoclock
# SPDX-License-Identifier: AGPL-3.0-only
"""Stamp Markdown documentation footers from the release metadata."""

import argparse
import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOOTER = re.compile(r"\*Version: [^\n]* · Last updated: \d{4}-\d{2}-\d{2}\*")


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--check", action="store_true")
	args = parser.parse_args()
	version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
	date = re.search(r"^date-released: (\S+)$", (ROOT / "CITATION.cff").read_text(), re.M)
	if date is None:
		raise ValueError("CITATION.cff has no release date")
	stamp = f"*Version: {version} · Last updated: {date.group(1)}*"
	outdated = []
	for path in (ROOT / "docs").rglob("*.md"):
		original = path.read_text()
		updated = FOOTER.sub(stamp, original)
		if updated != original:
			outdated.append(str(path.relative_to(ROOT)))
			if not args.check:
				path.write_text(updated)
	if args.check and outdated:
			parser.exit(1, "Outdated documentation footers: " + ", ".join(outdated) + "\n")
	print("Documentation footers current" if args.check else f"Stamped {len(outdated)} files")


if __name__ == "__main__":
	main()
