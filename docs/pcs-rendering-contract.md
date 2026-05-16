# PCS rendering contract

Every LabTrust PCS claim page at `/pcs/claims/<claim_id>` must render the following sections in order.

| # | Section title | Component | Data source |
|---|---------------|-----------|-------------|
| 1 | Claim | `ClaimArtifactView` | `read_model.claim` |
| 2 | Assumptions | `AssumptionSetView` | `read_model.assumption_set` |
| 3 | Runtime Evidence | `RuntimeReceiptView` | `read_model.runtime_receipt` |
| 4 | Temporal Certificate | `TraceCertificateView` | `read_model.trace_certificate` |
| 5 | Verification Result | `VerificationResultView` | `read_model.verification_result` |
| 6 | Artifact Hashes | `ArtifactHashTable` | `read_model.artifact_hashes` |
| 7 | Source Repositories | `SourceRepositories` | `read_model.source_repositories` |
| 8 | Reproduce / Verify | `ReplayCommand` | `reproduce_commands`, `verify_commands` |
| 9 | Limitations | `LimitationNotice` | `limitation_notice` (+ optional `limitations`) |

## Guarantee-type separation

The claim section must show boolean flags for:

- `formally_checked`
- `certificate_checked`
- `runtime_observed`
- `empirically_measured`
- `human_reviewed`
- `unchecked_advisory`

Values come from `ClaimArtifact.guarantee_types` when present; otherwise they are inferred from nested artifact statuses and verification checks.

## Required limitation notice

Every page must display the following notice verbatim (or substantively identical wording):

> This artifact is a proof-carrying simulation result. It demonstrates protocol-level and runtime-evidence verification inside LabTrust-Gym. It is not a clinical validation, production medical certification, or guarantee about a real hospital laboratory.

The canonical string is defined in `sm_pipeline.pcs_import.artifact_normalizer.LIMITATION_NOTICE`.

## Status visibility

Status enums must be visible for:

- Claim artifact
- Assumption set and individual assumptions (when provided)
- Runtime receipt
- Trace certificate
- Verification result and each check outcome

Statuses use the pcs-core canonical enum (`Draft`, `RuntimeObserved`, `CertificateChecked`, etc.).

## Reproduce / verify commands

Commands are copied from the signed bundle (top-level or `science_claim_bundle` fields) without modification. They are shown as shell snippets for external verification, for example:

- `pf verify science-claim …`
- `just pcs-validate-bundle BUNDLE=…`

## Test IDs

Portal components expose `data-testid` attributes for contract tests:

- `pcs-claim-page`
- `pcs-section-claim`, `pcs-section-assumptions`, …
- `pcs-limitation-notice`
- `pcs-hash-table`, `pcs-source-repo`, `pcs-source-commit`

Python tests in `tests/pcs/` validate import behavior and read-model completeness.
