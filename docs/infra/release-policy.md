# Release policy

Releases are created by pushing a version tag (`v*`) and are built and
verified by the
[release workflow](../../.github/workflows/release.yml).

## What the release workflow does

1. **Build**: Lean build (`lake build`), pipeline validation, portal build.
2. **Artifacts**:
   [scripts/release_artifacts.sh](../../scripts/release_artifacts.sh) produces
   `dist/` with CHANGELOG, checksums, and release bundle.
3. **Verification**:
   [scripts/verify_release_checksums.sh](../../scripts/verify_release_checksums.sh)
   recomputes manifest checksum and release artifact hash; job fails if they do
   not match.
4. **Signing**: Release workflow signs `dist/checksums.txt` with
   **Sigstore (cosign) keyless**; output in `dist/checksums.txt.sig` and
   `dist/checksums.txt.pem`.
5. **Publication**: A GitHub Release is created for the tag; assets uploaded
   include CHANGELOG.md, checksums.txt, .sig, .pem, and `release-bundle.zip`
   (full dist contents). See
   [Contributor playbook – Release integrity (Gate 7)](../contributor-playbook.md#release-integrity-gate-7).

## Gate 7 (release integrity)

- **Changelog**: Generated from git log (previous tag to HEAD).
- **Checksums**: `dist/checksums.txt` includes `manifest_checksum` and per-file
  hashes; used for tamper detection.
- **Signing**: Sigstore keyless signing of `dist/checksums.txt`; see
  [Contributor playbook – Release integrity (Gate 7)](../contributor-playbook.md#release-integrity-gate-7).

## Releasing

1. Ensure `main` is green (all CI gates pass).
2. Tag: `git tag v0.1.0` (or desired version).
3. Push tag: `git push origin v0.1.0`.
4. The workflow runs and creates a GitHub Release with signed artifacts;
   download from the Releases page.

## Snapshot baselines

When creating a release, run (repeat `--highlight` for each bullet; at least one is required):

`uv run --project pipeline python -m sm_pipeline.cli export-diff-baseline --baseline-id v{semver}-corpus --title "..." --narrative "..." --highlight "..."`

The `just export-diff-baseline` recipe runs the same CLI with defaults; pass extra flags via `uv run ...` as above. Update `last-release.json` to point
to the current release snapshot (or regenerate it).
**Naming convention:** Use `v{semver}-corpus.json` or `release-{tag}.json` for
tagged releases; `last-release.json` serves as the canonical current alias.

**Quality requirements:** Each release baseline must have:
- Non-empty `title` (descriptive)
- `narrative` (minimum 10 characters, describes what changed)
- Non-empty `highlights` array (at least one entry summarizing key additions)

Validation (`just validate`) emits warnings if release baselines lack these
fields. See [docs/generated-artifacts.md](../generated-artifacts.md).

## Verifying a release locally

Clone at the release tag, run `just bootstrap` and `just build`, then
optionally run `scripts/verify_release_checksums.sh` and compare with published
`dist/checksums.txt`.
