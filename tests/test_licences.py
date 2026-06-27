#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for scripts/check_licences.py.

Covers the happy path (clean SPDX ids classify correctly) and the failure
modes the gate exists to catch: messy classifier / free-text licence strings,
SPDX compound expressions, blocked families in non-SPDX form, empty / full-text
strings, declared-dep scoping, and the end-to-end --check over the real env.

Sufficiency rationale: the gate's job is to be fail-closed. The blocked-form and
empty/unknown tests assert that disallowed or unresolvable licences stay blocked
(the dangerous direction); the classifier/expression tests assert that genuinely
compatible deps are not wrongly blocked (the false-positive that broke CI). The
--check test exercises the real installed-metadata path end to end, including the
audited-exception fallback for a metadata-less dep (mistralai).
"""

import subprocess
import sys

from scripts import check_licences as cl


def run_classify(lic: str) -> int:
    """Run --classify with the given licence string and return exit code."""
    result = subprocess.run(
        [sys.executable, "scripts/check_licences.py", "--classify", lic],
        capture_output=True,
        text=True,
    )
    return result.returncode


def test_classify_allowed_licences() -> None:
    """All AGPL-compatible clean SPDX ids classify ALLOWED (CLI exit 0)."""
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
        assert run_classify(lic) == 0, f"Expected ALLOWED for {lic!r}"


def test_classify_blocked_licences() -> None:
    """All AGPL-incompatible clean SPDX ids classify DENIED (CLI non-zero)."""
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
        assert run_classify(lic) != 0, f"Expected DENIED for {lic!r}"


def test_classify_classifier_and_freetext_allowed() -> None:
    """Messy classifier / free-text forms of allowed families classify allowed.

    These are the real metadata shapes that broke the old gate (it matched only
    clean SPDX ids, so "Apache Software License" etc. failed-closed wrongly).
    """
    allowed_messy = [
        "MIT License",
        "Apache Software License",
        "Apache 2.0",
        "ISC License (ISCL)",
        "BSD License",
        "Python Software Foundation License",
        "GNU Lesser General Public License v3 (LGPLv3)",
        "Mozilla Public License 2.0 (MPL 2.0)",
        "GNU Affero General Public License v3 or later (AGPLv3+)",
    ]
    for lic in allowed_messy:
        assert cl.classify_licence(lic), f"Expected ALLOWED for {lic!r}"


def test_classify_spdx_expressions() -> None:
    """SPDX compound expressions: OR needs any operand allowed, AND needs all."""
    assert cl.classify_licence("Apache-2.0 OR BSD-3-Clause")
    assert cl.classify_licence("MIT OR Apache-2.0")
    assert cl.classify_licence("MIT AND Apache-2.0")
    # AND with a blocked operand must fail (all operands must be allowed).
    assert not cl.classify_licence("MIT AND SSPL")
    # OR where one operand is allowed is still allowed (consumer may pick it).
    assert cl.classify_licence("SSPL OR MIT")


def test_classify_blocked_freetext() -> None:
    """Blocked families stay blocked in non-SPDX, free-text form (fail-closed)."""
    blocked_messy = [
        "SSPL",
        "Server Side Public License",
        "OpenRAIL-M",
        "Llama 2 Community License",
        "Business Source License 1.1",
        "Elastic License 2.0",
    ]
    for lic in blocked_messy:
        assert not cl.classify_licence(lic), f"Expected DENIED for {lic!r}"


def test_classify_empty_and_none_blocked() -> None:
    """Empty / whitespace / None licence strings are blocked (unknown == deny)."""
    assert not cl.classify_licence("")
    assert not cl.classify_licence("   ")
    assert not cl.classify_licence(None)


def test_classify_full_agpl_text_allowed() -> None:
    """A full AGPL licence text classifies allowed.

    Regression: the project's own pyproject uses license = { file = "LICENSE" },
    so setuptools embeds the entire AGPLv3 text in the License metadata field.
    The gate must recognise that as AGPL-compatible rather than choking on it.
    """
    full_text = (
        "Hillstar\nCopyright (C) 2026 Julen Gamboa\n\n"
        "This program is free software: you can redistribute it and/or modify "
        "it under the terms of the GNU Affero General Public License as "
        "published by the Free Software Foundation, version 3 of the License."
    )
    assert cl.classify_licence(full_text)


def test_declared_runtime_deps_scoped() -> None:
    """declared_runtime_deps returns the 9 declared runtime deps only.

    Asserts the scope fix: the project itself and extras (dev/docs) are excluded,
    so the gate does not scan the whole installed environment.
    """
    deps = {cl._canon_name(d) for d in cl.declared_runtime_deps()}
    expected = {
        "anthropic",
        "openai",
        "mistralai",
        "google-generativeai",
        "requests",
        "urllib3",
        "pydantic",
        "cryptography",
        "keyring",
    }
    assert deps == expected, f"Unexpected declared runtime deps: {deps}"
    assert "pytest" not in deps  # dev extra must not be in scope
    assert "hillstar-orchestrator" not in deps  # project itself excluded


def test_resolve_licence_metadataless_dep_is_audited() -> None:
    """mistralai exposes no parseable licence metadata; the audit map covers it."""
    assert cl.resolve_licence("mistralai") is None
    assert cl._canon_name("mistralai") in cl.AUDITED_DEP_LICENCES


def test_check_env_passes_on_real_deps() -> None:
    """End-to-end: --check returns 0 over the real declared deps.

    This is the symptom the bug produced (non-zero exit); it must now pass with
    all nine declared deps resolving to AGPL-compatible licences.
    """
    assert cl.check_env() == 0


if __name__ == "__main__":
    test_classify_allowed_licences()
    test_classify_blocked_licences()
    test_classify_classifier_and_freetext_allowed()
    test_classify_spdx_expressions()
    test_classify_blocked_freetext()
    test_classify_empty_and_none_blocked()
    test_classify_full_agpl_text_allowed()
    test_declared_runtime_deps_scoped()
    test_resolve_licence_metadataless_dep_is_audited()
    test_check_env_passes_on_real_deps()
    print("All tests passed.")
