import Mathlib

namespace ScientificMemory.Chemistry.Solutions.DilutionRef

/--
Dilution with fixed solute amount: `c₀ v₀ = (c₀ / k) (k v₀)` when volume scales by `k ≠ 0`.
-/
theorem solute_amount_preserved_under_dilution (c0 v0 k : ℚ) (hk : k ≠ 0) :
    c0 * v0 = (c0 / k) * (v0 * k) := by
  -- Only rewrite the factor `c0` on the LHS; `rw [c0 = …]` would also change `c0` inside `c0 / k` on the RHS.
  conv_lhs => rw [← div_mul_cancel₀ c0 hk]
  rw [mul_assoc, mul_comm k v0]

/--
Mass-balance rearrangement: from `c₀ v₀ = c₁ v₁` and `v₁ ≠ 0`, solve for `c₁`.
-/
theorem conc_from_fixed_amount (c0 c1 v0 v1 : ℚ) (hv1 : v1 ≠ 0) (h : c0 * v0 = c1 * v1) :
    c1 = (c0 * v0) / v1 := by
  -- `mul_div_cancel₀.symm` can defeq to `v1 * (c1 / v1)` instead of `(c1 * v1) / v1` on ℚ.
  rw [eq_div_iff hv1]
  exact h.symm

end ScientificMemory.Chemistry.Solutions.DilutionRef
