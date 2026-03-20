# Blueprint: Langmuir 1918 (Adsorption)

Blueprint-style outline for the first domain slice. Links claim IDs to target Lean declarations and gives a one-sentence description. This file is hand-maintained; the formal mapping is canonical in `corpus/papers/langmuir_1918_adsorption/mapping.json`.

## Paper

- **ID:** langmuir_1918_adsorption  
- **Title:** The Adsorption of Gases on Plane Surfaces of Glass, Mica and Platinum  
- **Domain:** chemistry / adsorption  

## Claims and target declarations

| Claim ID | Target declaration | Description |
|----------|--------------------|-------------|
| langmuir_1918_claim_001 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_isotherm` | At equilibrium, surface coverage is given by the Langmuir isotherm (ratio in pressure and adsorption parameter). |
| langmuir_1918_claim_002 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_isotherm_nonnegative` | Nonnegativity of Langmuir coverage under nonnegative K, P. |
| langmuir_1918_claim_003 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_isotherm_bounded` | Langmuir coverage bounded above by 1. |
| langmuir_1918_claim_004 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_isotherm_zero_pressure` | Coverage is zero at zero pressure. |
| langmuir_1918_claim_005 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_isotherm_zero_K` | Coverage is zero when K = 0. |
| langmuir_1918_claim_006 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_denom_pos` | Denominator 1 + K*P is positive or K*P = 0 under nonnegative K, P. |
| langmuir_1918_claim_007 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_isotherm_pos_of_pos` | Strict positivity of coverage for positive K, P. |
| langmuir_1918_claim_008 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_mono_in_P` | Monotonicity of coverage in pressure P. |
| langmuir_1918_claim_009 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_mono_in_K` | Monotonicity of coverage in adsorption constant K. |
| langmuir_1918_claim_010 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_add_one_denom` | Identity: coverage + 1/(1+K*P) = 1 when denominator nonzero. |
| langmuir_1918_claim_011 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_sym_recip` | Relation 1 - coverage = 1/(1+K*P) when K*P ≠ -1. |
| langmuir_1918_claim_012 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_isotherm_one` | Coverage equals 1/2 when P = 1/K (K ≠ 0). |
| langmuir_1918_claim_013 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_mul_denom` | Coverage * (1+K*P) = K*P when denominator nonzero. |
| langmuir_1918_claim_014 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_scale_K` | Scaling: coverage(c*K,P) = coverage(K,c*P). |
| langmuir_1918_claim_015 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_neg_P` | Relation for coverage at -P when K*P = 0. |
| langmuir_1918_claim_016 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_sub_one` | Identity (1 : ℝ) - coverage = 1/(1+K*P) when denominator nonzero. |
| langmuir_1918_claim_017 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_numer_nonneg` | Numerator K*P nonnegative under nonnegative K, P. |
| langmuir_1918_claim_018 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_recip_denom` | Reciprocal identity 1/(1+K*P) = 1 - coverage when denominator nonzero. |
| langmuir_1918_claim_019 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_half` | Coverage equals 1/2 at P = 1/K (uses langmuir_isotherm_one). |
| langmuir_1918_claim_020 | `ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_zero_at_zero` | Coverage at (0,0) is zero. |

## Dependencies

- Definitions: `ScientificMemory.Chemistry.Adsorption.Definitions` (e.g. `LangmuirCoverage`).
- Provenance and verification boundary: `ScientificMemory.Foundations.Provenance`, `ScientificMemory.Foundations.VerificationBoundary`.
- In-file dependencies: e.g. `langmuir_recip_denom` uses `langmuir_sub_one`; `langmuir_half` uses `langmuir_isotherm_one` (see manifest dependency_graph).

## Kernel linkage

- Executable kernel: `langmuir_adsorption_kernel_v1` (see `corpus/kernels.json`). Links to theorem card `langmuir_1918_adsorption_card_001`.
