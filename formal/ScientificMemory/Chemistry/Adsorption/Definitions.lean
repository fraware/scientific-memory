import Mathlib

namespace ScientificMemory.Chemistry.Adsorption

abbrev Pressure := ℝ
abbrev Coverage := ℝ
abbrev AdsorptionConstant := ℝ

noncomputable def LangmuirCoverage (K P : ℝ) : ℝ :=
  (K * P) / (1 + K * P)

/-- Freundlich isotherm: amount adsorbed per mass as k * c^(1/n) (empirical; c > 0, n ≠ 0 in typical use). -/
noncomputable def FreundlichIsotherm (k c n : ℝ) : ℝ :=
  k * Real.rpow c (1 / n)

end ScientificMemory.Chemistry.Adsorption
