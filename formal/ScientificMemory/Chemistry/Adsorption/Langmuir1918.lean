import Mathlib
import ScientificMemory.Chemistry.Adsorption.Definitions
import ScientificMemory.Foundations.Provenance
import ScientificMemory.Foundations.VerificationBoundary

namespace ScientificMemory.Chemistry.Adsorption.Langmuir1918

open ScientificMemory.Chemistry.Adsorption

def langmuir_isotherm_provenance : ScientificMemory.Provenance :=
  {
    paperId := "langmuir_1918_adsorption"
    claimId := "langmuir_1918_claim_001"
    sourceSpan := {
      sourceFile := "source/source.pdf"
      startPos := { page := 2, offset := 140 }
      endPos := { page := 2, offset := 290 }
    }
  }

theorem langmuir_isotherm_nonnegative
    (K P : ℝ)
    (hK : 0 ≤ K)
    (hP : 0 ≤ P) :
    0 ≤ LangmuirCoverage K P := by
  unfold LangmuirCoverage
  apply div_nonneg (mul_nonneg hK hP) (by positivity)

theorem langmuir_isotherm_bounded
    (K P : ℝ)
    (hK : 0 ≤ K)
    (hP : 0 ≤ P) :
    LangmuirCoverage K P ≤ 1 := by
  unfold LangmuirCoverage
  have pos : 0 < 1 + K * P := by nlinarith [mul_nonneg hK hP]
  calc (K * P) / (1 + K * P) ≤ (1 + K * P) / (1 + K * P) := (div_le_div_iff_of_pos_right pos).2 (by nlinarith)
    _ = 1 := div_self (ne_of_gt pos)

theorem langmuir_isotherm_zero_pressure (K : ℝ) :
    LangmuirCoverage K 0 = 0 := by
  unfold LangmuirCoverage
  norm_num

theorem langmuir_isotherm_zero_K (P : ℝ) :
    LangmuirCoverage 0 P = 0 := by
  unfold LangmuirCoverage
  norm_num

theorem langmuir_isotherm_pos_of_pos (K P : ℝ) (hK : 0 < K) (hP : 0 < P) :
    0 < LangmuirCoverage K P := by
  unfold LangmuirCoverage
  apply div_pos <;> nlinarith [mul_pos hK hP]

theorem langmuir_mono_in_P (K P Q : ℝ) (hK : 0 ≤ K) (hP : 0 ≤ P) (hPQ : P ≤ Q) :
    LangmuirCoverage K P ≤ LangmuirCoverage K Q := by
  unfold LangmuirCoverage
  have hp : 0 < 1 + K * P := by nlinarith [mul_nonneg hK hP]
  have hq : 0 < 1 + K * Q := by nlinarith [mul_nonneg hK (le_trans hP hPQ)]
  exact (div_le_div_iff₀ hp hq).2 (by nlinarith [mul_le_mul_of_nonneg_left hPQ hK])

theorem langmuir_mono_in_K (K L P : ℝ) (hK : 0 ≤ K) (hP : 0 ≤ P) (hKL : K ≤ L) :
    LangmuirCoverage K P ≤ LangmuirCoverage L P := by
  unfold LangmuirCoverage
  have hp : 0 < 1 + K * P := by nlinarith [mul_nonneg hK hP]
  have hq : 0 < 1 + L * P := by nlinarith [mul_nonneg (le_trans hK hKL) hP]
  exact (div_le_div_iff₀ hp hq).2 (by nlinarith [mul_le_mul_of_nonneg_right hKL hP])

theorem langmuir_denom_pos (K P : ℝ) (hK : 0 ≤ K) (hP : 0 ≤ P) :
    0 < 1 + K * P ∨ K * P = 0 := by
  left
  nlinarith [mul_nonneg hK hP]

theorem langmuir_add_one_denom (K P : ℝ) (h : 1 + K * P ≠ 0) :
    LangmuirCoverage K P + 1 / (1 + K * P) = 1 := by
  unfold LangmuirCoverage
  field_simp [h]
  ring

theorem langmuir_sym_recip (K P : ℝ) (h : K * P ≠ -1) :
    1 - LangmuirCoverage K P = 1 / (1 + K * P) := by
  unfold LangmuirCoverage
  have den : 1 + K * P ≠ 0 := by contrapose! h; linarith
  rw [eq_div_iff den, sub_mul]
  rw [mul_comm (K * P / (1 + K * P)) (1 + K * P), mul_div_cancel₀ (K * P) den]
  ring

theorem langmuir_isotherm_one (K : ℝ) (hK : K ≠ 0) :
    LangmuirCoverage K (1 / K) = 1 / 2 := by
  unfold LangmuirCoverage
  field_simp [hK]
  ring

theorem langmuir_mul_denom (K P : ℝ) (hd : 1 + K * P ≠ 0) :
    LangmuirCoverage K P * (1 + K * P) = K * P := by
  unfold LangmuirCoverage
  field_simp [hd]

theorem langmuir_scale_K (K P c : ℝ) :
    LangmuirCoverage (c * K) P = LangmuirCoverage K (c * P) := by
  unfold LangmuirCoverage
  have H : c * K * P = K * (c * P) := by rw [← mul_assoc, mul_comm c K, mul_assoc]
  rw [H]

theorem langmuir_neg_P (K P : ℝ) (h : K * P = 0) :
    LangmuirCoverage K (-P) = -LangmuirCoverage (-K) P := by
  unfold LangmuirCoverage
  have h1 : K * (-P) = 0 := by rw [mul_neg K P, h, neg_zero]
  have h2 : (-K) * P = 0 := by rw [neg_mul K P, h, neg_zero]
  rw [h1, h2]
  norm_num

theorem langmuir_sub_one (K P : ℝ) (h : 1 + K * P ≠ 0) :
    (1 : ℝ) - LangmuirCoverage K P = 1 / (1 + K * P) := by
  unfold LangmuirCoverage
  field_simp [h]
  ring

theorem langmuir_numer_nonneg (K P : ℝ) (hK : 0 ≤ K) (hP : 0 ≤ P) :
    0 ≤ K * P := mul_nonneg hK hP

theorem langmuir_recip_denom (K P : ℝ) (h : 1 + K * P ≠ 0) :
    1 / (1 + K * P) = 1 - LangmuirCoverage K P := (langmuir_sub_one K P h).symm

theorem langmuir_half (K : ℝ) (hK : K ≠ 0) :
    LangmuirCoverage K (1 / K) = 1 / 2 := langmuir_isotherm_one K hK

theorem langmuir_zero_at_zero : LangmuirCoverage 0 0 = 0 := by norm_num [LangmuirCoverage]

-- formal target for claim bundle langmuir_1918_claim_001
noncomputable def langmuir_isotherm := LangmuirCoverage

end ScientificMemory.Chemistry.Adsorption.Langmuir1918
