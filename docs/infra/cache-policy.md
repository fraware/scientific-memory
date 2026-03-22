# Cache policy

CI and local builds use caches to speed up Lake, uv, and frontend installs.

## Lake (Lean)

- **Location**: `.lake/` (gitignored); GitHub Actions cache key includes
  `lakefile.toml`, `lean-toolchain`, `lake-manifest.json`.
- **Workflow**:
  [.github/workflows/lean-ci.yml](../../.github/workflows/lean-ci.yml)
  restores and saves the Lake cache.
- **Policy**: Cache is invalidated when any of the key files change. No
  retention limit beyond GitHub's; clear manually if builds are inconsistent.

## uv (Python)

- **Location**: `.venv/` (gitignored); `uv.lock` pins dependencies.
- **Workflow**: Validation and benchmark jobs run in a venv; cache key
  typically includes `uv.lock` and `pyproject.toml` (or equivalent).
- **Policy**: Reproducible install from lockfile; cache key should include
  lockfile hash.

## Portal (pnpm)

- **Location**: `portal/node_modules/` (gitignored); `pnpm-lock.yaml` in repo
  root or portal.
- **Workflow**:
  [.github/workflows/portal-ci.yml](../../.github/workflows/portal-ci.yml)
  (or equivalent) may cache `pnpm store` or `node_modules`.
- **Policy**: Cache key should include `pnpm-lock.yaml` and
  `portal/package.json` so dependency changes invalidate the cache.

## Local development

Run from repo root; `just bootstrap` (or project-specific commands) populate
caches. Do not commit `.lake/`, `.venv/`, or `node_modules/`.
