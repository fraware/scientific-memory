# Scientific Memory PCS releases

| Document | Scope |
|----------|--------|
| [pcs-sm-v0.1.0-rc1.md](./pcs-sm-v0.1.0-rc1.md) | RC strict bundle import, portal render, drift gate |
| [pcs-sm-phase2.md](./pcs-sm-phase2.md) | Phase 2 protocol consumer: ReleaseManifest, chain validation, registry, lineage |

## Verify locally

```bash
just refresh-pcs-release   # sync pcs-core chain + Phase 2 fixtures
just pcs-rc-gate           # full test suite + import-release + portal contracts
```
