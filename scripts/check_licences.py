#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""licence-checker: AGPLv3-compatible dependency gate.

Two modes:
  --classify "<licence>":  exit 0 if AGPL-compatible, non-zero if not.
  --check:  classify the project's DECLARED runtime dependencies and exit
            non-zero on any that is disallowed or has no auditable licence.

Scope (--check): only the runtime dependencies the project itself declares
(``[project.dependencies]``, read here from the installed distribution's
``Requires-Dist`` so no TOML parser is needed). The whole installed environment
is deliberately NOT scanned: dev/test/build tools (pytest, ruff, sphinx, ...) do
not ship in the distributed artifact, and transitive deps are covered by their
parents' audits. This keeps the gate self-contained (it does not reach into the
private planning repo) so it runs unchanged in public CI.

Allow-list / audit reference: ~/project-planning/commercial/dependency-license-audit.md
Compatible: MIT, BSD-2/3-Clause, Apache-2.0, ISC, GPLv2-or-later, GPLv3, LGPL, MPL-2.0, AGPLv3, PSF
Incompatible: GPLv2-only, BSD-4-Clause, proprietary, SSPL, Commons Clause, BSL/Elastic-2.0, OpenRAIL-*, Llama/Stability/Gemma
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import re
import sys
from email.message import Message
from typing import List, Optional, Tuple, cast

# The distribution whose declared runtime deps are gated. Matches the project
# name in pyproject.toml; resolved from installed metadata at runtime.
DISTRIBUTION_NAME = "hillstar-orchestrator"

# Allowed licence identifiers (base SPDX ids, without an "-or-later" suffix).
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

# Blocked licence identifiers (exact id, or prefix for a family).
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

# Free-text / classifier substrings that mark a blocked licence even when the
# string is not a clean SPDX id (case-insensitive). Keeps the gate fail-closed
# against messy metadata forms. Deliberately excludes "all rights reserved",
# which appears verbatim in the permissive BSD licence texts.
BLOCKED_KEYWORDS = frozenset({
    "sspl",
    "server side public license",
    "commons clause",
    "elastic license 2.0",
    "elastic-2.0",
    "business source license",
    "bsl-1.0",
    "openrail",
    "llama",
    "stability ai",
    "gemma",
    "bsd-4-clause",
    "proprietary",
})

# Declared deps whose published wheel metadata carries NO parseable licence
# (no License field, no classifier, no PEP 639 License-Expression), only a
# License-File. Licence verified out-of-band in dependency-license-audit.md
# (2026-05-29) and pinned here so the gate stays self-contained and deterministic.
# A new metadata-less dep NOT in this map fails the gate, forcing a fresh audit.
AUDITED_DEP_LICENCES = {
    "mistralai": "Apache-2.0",  # ships LICENSE file only; Apache-2.0 per audit
}


def _normalise_licence(lic: str) -> str:
    """Collapse whitespace and drop an "-or-later" suffix for base matching."""
    lic = " ".join(lic.strip().split())
    if lic.endswith("-or-later"):
        lic = lic[: -len("-or-later")]
    return lic


def _has_token(low: str, token: str) -> bool:
    """True if token appears as a whole word in the lower-cased string."""
    return re.search(rf"\b{re.escape(token)}\b", low) is not None


def _allowed_family(low: str) -> bool:
    """Recognise an allowed licence family from a messy / free-text string.

    Applied only after explicit block and exact-allow checks, so it cannot
    override a blocked licence. Affero and Lesser are tested before plain GPL
    so the more specific family wins.
    """
    if "affero" in low or _has_token(low, "agpl"):
        return True
    if "lesser general public" in low or _has_token(low, "lgpl"):
        return True
    if "mozilla" in low or _has_token(low, "mpl"):
        return True
    if "apache" in low:
        return True
    if _has_token(low, "mit"):
        return True
    if _has_token(low, "isc"):
        return True
    if _has_token(low, "bsd"):
        return True
    if "python software foundation" in low or _has_token(low, "psf"):
        return True
    # Generic GPL: GPLv2-only is caught by the block checks above; any remaining
    # GPL form (v2-or-later, v3) is allowed.
    if "general public license" in low or _has_token(low, "gpl"):
        return True
    return False


def classify_licence(lic: Optional[str]) -> bool:
    """Return True if the licence string is AGPL-compatible, False otherwise.

    Handles clean SPDX ids, SPDX compound expressions ("A OR B", "A AND B"),
    classifier strings ("License :: OSI Approved :: MIT License" reduced to
    "MIT License"), free-text names, and full licence texts. Unknown or empty
    strings are blocked (fail-closed).
    """
    if lic is None:
        return False
    raw = lic.strip()
    if not raw:
        return False

    # SPDX compound expressions use UPPERCASE operators; prose ("v3 or later")
    # does not, so matching only uppercase avoids splitting on prose.
    if " OR " in f" {raw} ":
        return any(classify_licence(p) for p in re.split(r"\s+OR\s+", raw))
    if " AND " in f" {raw} ":
        return all(classify_licence(p) for p in re.split(r"\s+AND\s+", raw))

    norm = _normalise_licence(raw)
    low = norm.lower()

    # Explicit blocks first, so a blocked family cannot be rescued by the
    # allow/family checks below.
    for blocked in BLOCKED_LICENCES:
        if norm == blocked or norm.startswith(blocked):
            return False
    for kw in BLOCKED_KEYWORDS:
        if kw in low:
            return False

    # Exact / family-prefix allow on clean SPDX ids.
    for allowed in ALLOWED_LICENCES:
        if norm == allowed or norm.startswith(allowed):
            return True

    # Messy classifier / free-text / full-text forms.
    return _allowed_family(low)


def declared_runtime_deps() -> List[str]:
    """Return the project's declared runtime dependency names.

    Reads ``Requires-Dist`` from the installed distribution and drops any entry
    gated behind an ``extra ==`` marker (optional / dev / build extras) and the
    project itself. Raises PackageNotFoundError if the project is not installed.
    """
    reqs = metadata.requires(DISTRIBUTION_NAME) or []
    names: List[str] = []
    for req in reqs:
        if "extra ==" in req:
            continue
        match = re.match(r"[A-Za-z0-9._-]+", req.strip())
        if match:
            names.append(match.group(0))
    return names


def _canon_name(name: str) -> str:
    """Normalise a distribution name for case/separator-insensitive lookup."""
    return name.lower().replace("_", "-")


def resolve_licence(name: str) -> Optional[str]:
    """Resolve the best available licence string for an installed dependency.

    Order: PEP 639 ``License-Expression``; then the ``License`` field only when
    it looks like an identifier (short, single line, not an embedded full text);
    then a ``License ::`` classifier. Returns None when nothing usable is found.
    """
    # metadata() returns an email.message.Message at runtime; cast so .get is
    # both typed and non-deprecated (subscripting a missing key is deprecated).
    md = cast(Message, metadata.metadata(name))

    expr = (md.get("License-Expression") or "").strip()
    if expr:
        return expr

    lic = (md.get("License") or "").strip()
    if lic and "\n" not in lic and len(lic) <= 60:
        return lic

    for classifier in md.get_all("Classifier") or []:
        if classifier.startswith("License :: "):
            parts = [p.strip() for p in classifier.split(" :: ")]
            # Skip a bare "License :: OSI Approved" with no concrete identifier.
            if len(parts) >= 3:
                return parts[-1]

    return None


def check_env() -> int:
    """Classify the declared runtime deps; return 0 if all pass, 1 otherwise.

    A dep fails when its resolved licence is disallowed, or when no licence can
    be resolved and it is not in the audited-exception map.
    """
    bad: List[Tuple[str, str]] = []

    for name in declared_runtime_deps():
        lic = resolve_licence(name)
        if lic is None:
            lic = AUDITED_DEP_LICENCES.get(_canon_name(name))
        if lic is None:
            bad.append((name, "<no auditable licence metadata; needs audit>"))
            continue
        if not classify_licence(lic):
            bad.append((name, lic))

    if bad:
        print("Disallowed or unauditable dependencies:", file=sys.stderr)
        for name, lic in bad:
            print(f"  {name}: {lic}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AGPL-compatible dependency gate")
    parser.add_argument(
        "--classify",
        metavar="LICENCE",
        help="Classify a licence string (exit 0 if allowed, 1 if blocked)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Classify the project's declared runtime dependencies",
    )
    args = parser.parse_args()

    if args.classify is not None:
        sys.exit(0 if classify_licence(args.classify) else 1)

    if args.check:
        return check_env()

    parser.error("One of --classify or --check is required")


if __name__ == "__main__":
    sys.exit(main())
