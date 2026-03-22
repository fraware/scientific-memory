# Hard-wedge stress papers

Two intentionally narrow intake scaffolds exercise failure modes that the main
chemistry wedge does not stress on its own:

- **stress_units_dimensional_2024** — dimensional analysis, unit consistency,
  and scaling before full claim extraction.
- **stress_approx_asymptotic_2024** — regime limits, asymptotic statements, and
  error-bound style reasoning.

Each paper's `metadata.json` declares a `hardness.primary` tag and an
`admission_rationale` string. Keep `claims.json` empty until real source
hashing and extraction are wired. Gate 3 provenance now allows a temporary
`manifest.json` with all-zero `metadata.source.sha256` only for this narrow
scaffold state (`hardness.primary:*` + empty claims). After `hash-source` and
real artifacts, run `just publish-artifacts <paper_id>` as usual.

See [playbooks/domain-expander.md](../playbooks/domain-expander.md) for how new
domains are admitted.
