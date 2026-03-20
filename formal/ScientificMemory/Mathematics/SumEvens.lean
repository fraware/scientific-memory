import Mathlib
import ScientificMemory.Foundations.Provenance
import ScientificMemory.Foundations.VerificationBoundary

namespace ScientificMemory.Mathematics.SumEvens

/-- The sum of two even natural numbers is even. -/
theorem sum_evens (a b : ℕ) (ha : Even a) (hb : Even b) : Even (a + b) := by
  obtain ⟨k, rfl⟩ := ha
  obtain ⟨m, rfl⟩ := hb
  use k + m
  ring_nf

end ScientificMemory.Mathematics.SumEvens
