# Playbook: Release manager

For contributors who cut and publish a release. Ensures the release workflow runs, artifacts are signed, and the GitHub Release is created with the correct assets.

## Prerequisites

- Push access to the repository (to push tags). Release workflow runs on GitHub Actions on tag push `v*`.

## Gate checklist (before tagging)

1. **Main is green**  
   All CI gates pass on the branch you will tag (typically `main`): validate, test, build, benchmark, portal build.

2. **Changelog and version**  
   Ensure notable changes are documented. The workflow generates `dist/CHANGELOG.md` from git log (previous tag to HEAD). When packaging runs with `uv`, `scripts/release_corpus_delta.py` can append a structured corpus delta for release context. Optionally prepare release notes in advance.

3. **No uncommitted changes**  
   Tag only from a committed state. The workflow will run on the tag ref.

## End-to-end path (create a release)

1. **Confirm CI**  
   On `main` (or release branch): run locally `just check` and `just benchmark`. Confirm GitHub Actions for the branch is green.

2. **Tag**  
   Choose a version (e.g. `v0.2.0`). Run:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

3. **Workflow**  
   The [release workflow](../../.github/workflows/release.yml) will:
   - Run full check (lake build, validate-all, portal build)
   - Package artifacts (`scripts/release_artifacts.sh`) → `dist/` (corpus, CHANGELOG.md, checksums.txt)
   - Verify checksums (`scripts/verify_release_checksums.sh`)
   - Sign `dist/checksums.txt` with Sigstore (cosign) → `dist/checksums.txt.sig`, `dist/checksums.txt.pem`
   - Create a GitHub Release and upload: CHANGELOG.md, checksums.txt, .sig, .pem, release-bundle.zip

4. **Verify**  
   Open the new GitHub Release. Confirm assets are present. Optionally download `release-bundle.zip`, unpack, and run `scripts/verify_release_checksums.sh` (and cosign verify if you have the .sig and .pem).

## Failure troubleshooting

| Failure | What to do |
|--------|------------|
| Workflow fails on “Full check” | Fix the failing step (Lean build, validate, or portal build) on the branch, then re-push the tag (delete and re-create: `git tag -d v0.2.0`, `git push origin :refs/tags/v0.2.0`, then re-tag and push). |
| Checksum verification fails | Fix `scripts/release_artifacts.sh` or `scripts/verify_release_checksums.sh` so that recomputed hashes match; ensure no non-determinism in dist content. |
| Cosign signing fails | Check workflow permissions (`id-token: write`, `contents: write`). Ensure `sigstore/cosign-installer` and cosign version are correct. |
| Release not created | Check `contents: write` permission and that `softprops/action-gh-release` has `GITHUB_TOKEN`. Ensure the tag matches `v*`. |
| Release bundle missing or incomplete | Ensure `dist/` after packaging contains corpus, CHANGELOG.md, checksums.txt, and (after signing) .sig and .pem; zip step creates `dist/release-bundle.zip` from dist contents. |

## Quick reference

| Goal | Command / action |
|------|-------------------|
| Tag and push | `git tag vX.Y.Z` then `git push origin vX.Y.Z` |
| Verify locally before tag | `just check` and `just benchmark` |
| Release policy | [infra/release-policy.md](../../infra/release-policy.md) |
| Release integrity (Gate 7) | [Contributor playbook – Gate 7](../contributor-playbook.md#release-integrity-gate-7) |
| Verify a release | Clone at tag, run `just bootstrap`, `just build`, then `scripts/verify_release_checksums.sh`; optionally cosign verify with .sig and .pem. |
