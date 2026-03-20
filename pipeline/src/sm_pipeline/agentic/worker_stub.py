"""
Optional agentic worker stub (SPEC v0.3): deferred HTTP/queue implementation.

This module documents the intended surface only. Do not expose unauthenticated
write paths. Reference integration remains MCP + human PR (ADR 0007).

Intended future endpoints (not bound here):
- POST /proposals -- accept proof-repair proposal JSON; store for human review only.
- GET /health -- liveness.

Run the real workflow via `sm-pipeline proof-repair-proposals` and MCP tools instead.
"""

WORKER_DEFERRED = True
