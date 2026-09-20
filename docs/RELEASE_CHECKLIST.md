# Release Checklist

How to cut a Hillstar release. The version single source of truth is
`pyproject.toml`; everything else is stamped or derived from it.

## 1. Prepare

1. Make changes on a feature branch; open a PR into `main` (the branch is
   rule-protected; direct pushes are rejected).
2. Bump the version in `pyproject.toml` **in the release PR** if this is a
   release commit. Keep `CITATION.cff` (`version:` and `date-released:`)
   and `docs/sphinx/conf.py` (`release` / `version`) in step.
3. Add a `CHANGELOG.md` section for the new version.
4. Update the README title and Status section to the new version.
5. Run `python scripts/stamp_docs.py` (never edit doc footers by hand),
   then `python scripts/stamp_docs.py --check` to confirm.

## 2. Merge and tag

1. Merge the PR (required status checks: pytest 3.11/3.12/3.13,
   licence-check).
2. Tag the release tip and push the tag:

   ```sh
   git tag -a vX.Y.Z -m "Hillstar vX.Y.Z — summary"
   git push origin vX.Y.Z
   ```

3. Create the GitHub release for the tag (`gh release create vX.Y.Z` with
   notes from the changelog section). GitHub shows the most recently
   created release as "Latest"; do not leave a version untagged or the
   release page goes stale.

## 3. Publish to PyPI (Trusted Publishing)

The `.github/workflows/release.yml` workflow publishes automatically when
a `v*.*.*` tag is pushed. It uses PyPI Trusted Publishing (OIDC): no API
token is stored in the repository or on any machine.

One-time setup (repository owner, on pypi.org):

1. Go to the project on pypi.org → Publishing → add a **pending
   publisher** with:
   - Owner: `evoclock`
   - Repository: `hillstar-orchestrator`
   - Workflow name: `release.yml`
   - Environment: `pypi`
2. In GitHub, create the environment `pypi` under Settings → Environments
   (the workflow declares `environment: pypi`; the name must match).
3. The first tagged push after setup publishes; verify on pypi.org and
   with `pip index versions hillstar-orchestrator`.

If a manual publish is ever needed, build with `uv build` (or
`python -m build`) and use `twine upload` with credentials stored in the
macOS Keychain, never in a dotfile:

```sh
security add-generic-password -U -a julen -s pypi-upload -w
export TWINE_USERNAME=__token__
export TWINE_PASSWORD="$(/usr/bin/security find-generic-password -s 'pypi-upload' -a 'julen' -w 2>/dev/null)"
twine upload dist/*
unset TWINE_USERNAME TWINE_PASSWORD
```

The key value is typed at the prompt (never in shell history); the
environment variables live only for the upload command's duration.

## 4. Verify

1. `pip index versions hillstar-orchestrator` shows the new version.
2. `pip install hillstar-orchestrator==X.Y.Z` in a scratch venv and run
   `hillstar --version`.
3. GitHub release page shows the new release as "Latest".
