# Blueprint: Freundlich 1906 (Adsorption)

Blueprint-style outline for the Freundlich isotherm domain slice. Links claim IDs to target Lean declarations. The formal mapping is canonical in `corpus/papers/freundlich_1906_adsorption/mapping.json`.

## Paper

- **ID:** freundlich_1906_adsorption  
- **Domain:** chemistry / adsorption  

## Claims and target declarations

| Claim ID | Target declaration | Description |
|----------|--------------------|-------------|
| freundlich_1906_adsorption_claim_001 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_isotherm` | Freundlich isotherm: amount = k * c^(1/n). |
| freundlich_1906_adsorption_claim_002 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_nonneg` | Nonnegativity of Freundlich isotherm under typical constraints. |
| freundlich_1906_adsorption_claim_003 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_pos` | Strict positivity under positive k, c, n. |
| freundlich_1906_adsorption_claim_004 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_zero_k` | Amount zero when k = 0. |
| freundlich_1906_adsorption_claim_005 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_zero_c` | Amount zero when c = 0. |
| freundlich_1906_adsorption_claim_006 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_mono_in_c` | Monotonicity in concentration c. |
| freundlich_1906_adsorption_claim_007 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_mono_in_k` | Monotonicity in constant k. |
| freundlich_1906_adsorption_claim_008 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_at_one` | Value at c = 1. |
| freundlich_1906_adsorption_claim_009 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_smul_k` | Scaling in k. |
| freundlich_1906_adsorption_claim_010 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_rpow_pos` | Positivity of c^(1/n). |
| freundlich_1906_adsorption_claim_011 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_strict_mono_in_c` | Strict monotonicity in c. |
| freundlich_1906_adsorption_claim_012 | `ScientificMemory.Chemistry.Adsorption.Freundlich1906.freundlich_double_k` | Effect of doubling k. |

## Dependencies

- Definitions: `ScientificMemory.Chemistry.Adsorption.Definitions` (e.g. `FreundlichIsotherm`).

## Kernel linkage

- Executable kernel: `freundlich_adsorption_kernel_v1` (see `corpus/kernels.json`). Links to theorem card `freundlich_1906_adsorption_card_001`.
