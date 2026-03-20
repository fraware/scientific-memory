import Mathlib
import ScientificMemory.Chemistry.Adsorption.Definitions

namespace ScientificMemory.Chemistry.Adsorption.Freundlich1906

open ScientificMemory.Chemistry.Adsorption

noncomputable def freundlich_isotherm := FreundlichIsotherm

theorem freundlich_nonneg (k c n : ℝ) (hk : 0 ≤ k) (hc : 0 ≤ c) (_hn : n ≠ 0) :
    0 ≤ FreundlichIsotherm k c n := by
  unfold FreundlichIsotherm
  exact mul_nonneg hk (Real.rpow_nonneg hc _)

theorem freundlich_pos (k c n : ℝ) (hk : 0 < k) (hc : 0 < c) (_hn : n ≠ 0) :
    0 < FreundlichIsotherm k c n := by
  unfold FreundlichIsotherm
  exact mul_pos hk (Real.rpow_pos_of_pos hc _)

theorem freundlich_zero_k (c n : ℝ) (_hc : 0 ≤ c) (_hn : n ≠ 0) :
    FreundlichIsotherm 0 c n = 0 := by
  unfold FreundlichIsotherm
  ring

theorem freundlich_zero_c (k n : ℝ) (hn : 0 < n) :
    FreundlichIsotherm k 0 n = 0 := by
  unfold FreundlichIsotherm
  have H : Real.rpow 0 (1 / n) = 0 := Real.zero_rpow (one_div_ne_zero (ne_of_gt hn))
  rw [H, mul_zero]

theorem freundlich_mono_in_c (k c₁ c₂ n : ℝ) (hk : 0 ≤ k) (hn : 0 < n)
    (hc₁ : 0 < c₁) (hle : c₁ ≤ c₂) :
    FreundlichIsotherm k c₁ n ≤ FreundlichIsotherm k c₂ n := by
  unfold FreundlichIsotherm
  have h_exp : 0 ≤ 1 / n := by positivity
  have h₂ : 0 ≤ c₂ := le_trans (le_of_lt hc₁) hle
  exact mul_le_mul_of_nonneg_left (Real.rpow_le_rpow (le_of_lt hc₁) hle h_exp) hk

theorem freundlich_mono_in_k (k₁ k₂ c n : ℝ) (_hk₁ : 0 ≤ k₁) (hk : k₁ ≤ k₂)
    (hc : 0 ≤ c) (_hn : n ≠ 0) :
    FreundlichIsotherm k₁ c n ≤ FreundlichIsotherm k₂ c n := by
  unfold FreundlichIsotherm
  exact mul_le_mul_of_nonneg_right hk (Real.rpow_nonneg hc _)

theorem freundlich_at_one (k n : ℝ) (_hn : n ≠ 0) :
    FreundlichIsotherm k 1 n = k := by
  unfold FreundlichIsotherm
  simp [Real.one_rpow]

theorem freundlich_smul_k (a k c n : ℝ) (_ha : 0 ≤ a) (_hc : 0 ≤ c) (_hn : n ≠ 0) :
    FreundlichIsotherm (a * k) c n = a * FreundlichIsotherm k c n := by
  unfold FreundlichIsotherm
  ring

theorem freundlich_rpow_pos (c n : ℝ) (hc : 0 < c) (_hn : n ≠ 0) :
    0 < Real.rpow c (1 / n) :=
  Real.rpow_pos_of_pos hc _

theorem freundlich_strict_mono_in_c (k c₁ c₂ n : ℝ) (hk : 0 < k) (hn : 0 < n)
    (hc₁ : 0 < c₁) (hlt : c₁ < c₂) :
    FreundlichIsotherm k c₁ n < FreundlichIsotherm k c₂ n := by
  unfold FreundlichIsotherm
  have h_exp : 0 < 1 / n := one_div_pos.mpr hn
  exact mul_lt_mul_of_pos_left (Real.rpow_lt_rpow (le_of_lt hc₁) hlt h_exp) hk

theorem freundlich_double_k (k c n : ℝ) (_hc : 0 ≤ c) (_hn : n ≠ 0) :
    FreundlichIsotherm (2 * k) c n = 2 * FreundlichIsotherm k c n := by
  unfold FreundlichIsotherm
  ring

end ScientificMemory.Chemistry.Adsorption.Freundlich1906
