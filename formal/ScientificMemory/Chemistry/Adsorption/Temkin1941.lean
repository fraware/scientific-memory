import Mathlib
import ScientificMemory.Chemistry.Adsorption.Definitions

namespace ScientificMemory.Chemistry.Adsorption.Temkin1941

open ScientificMemory.Chemistry.Adsorption

/-- Temkin-style logarithmic coverage: proportional to ln(K·p) with coefficient (R·T)/a.
    Classical form used in Temkin–Pyzhev kinetics and adsorption literature. -/
noncomputable def temkin_theta (R T a K p : ℝ) : ℝ :=
  (R * T / a) * Real.log (K * p)

theorem temkin_theta_eq (R T a K p : ℝ) : temkin_theta R T a K p = (R * T / a) * Real.log (K * p) :=
  rfl

theorem temkin_zero_at_inv_pressure (R T a K : ℝ) (_ha : a ≠ 0) (hK : K ≠ 0) :
    temkin_theta R T a K K⁻¹ = 0 := by
  unfold temkin_theta
  rw [mul_inv_cancel₀ hK, Real.log_one, mul_zero]

theorem temkin_zero_when_Kp_eq_one (R T a K p : ℝ) (_ha : a ≠ 0) (h : K * p = 1) :
    temkin_theta R T a K p = 0 := by
  unfold temkin_theta
  rw [h, Real.log_one, mul_zero]

theorem temkin_strict_mono_in_p (R T a K p₁ p₂ : ℝ) (_ha : a ≠ 0) (hcoef : 0 < R * T / a)
    (hK : 0 < K) (hp₁ : 0 < p₁) (hp₂ : 0 < p₂) (hlt : p₁ < p₂) :
    temkin_theta R T a K p₁ < temkin_theta R T a K p₂ := by
  unfold temkin_theta
  have hkp₁ : 0 < K * p₁ := mul_pos hK hp₁
  have hkp₂ : 0 < K * p₂ := mul_pos hK hp₂
  have hmul : K * p₁ < K * p₂ := mul_lt_mul_of_pos_left hlt hK
  exact mul_lt_mul_of_pos_left (Real.log_lt_log hkp₁ hmul) hcoef

theorem temkin_mono_in_p (R T a K p₁ p₂ : ℝ) (ha : a ≠ 0) (hcoef : 0 < R * T / a)
    (hK : 0 < K) (hp₁ : 0 < p₁) (hp₂ : 0 < p₂) (hle : p₁ ≤ p₂) :
    temkin_theta R T a K p₁ ≤ temkin_theta R T a K p₂ := by
  rcases eq_or_lt_of_le hle with heq | hlt
  · rw [heq]
  · exact le_of_lt (temkin_strict_mono_in_p R T a K p₁ p₂ ha hcoef hK hp₁ hp₂ hlt)

theorem temkin_strict_mono_in_K (R T a K₁ K₂ p : ℝ) (_ha : a ≠ 0) (hcoef : 0 < R * T / a)
    (hp : 0 < p) (hK₁ : 0 < K₁) (hK₂ : 0 < K₂) (hlt : K₁ < K₂) :
    temkin_theta R T a K₁ p < temkin_theta R T a K₂ p := by
  unfold temkin_theta
  have hk₁ : 0 < K₁ * p := mul_pos hK₁ hp
  have hk₂ : 0 < K₂ * p := mul_pos hK₂ hp
  have hmul : K₁ * p < K₂ * p := mul_lt_mul_of_pos_right hlt hp
  exact mul_lt_mul_of_pos_left (Real.log_lt_log hk₁ hmul) hcoef

theorem temkin_smul_R (r R T a K p : ℝ) (_ha : a ≠ 0) :
    temkin_theta (r * R) T a K p = r * temkin_theta R T a K p := by
  unfold temkin_theta
  ring

theorem temkin_smul_T (R t T a K p : ℝ) (_ha : a ≠ 0) :
    temkin_theta R (t * T) a K p = t * temkin_theta R T a K p := by
  unfold temkin_theta
  ring

theorem temkin_flip_sign_a (R T a K p : ℝ) (ha : a ≠ 0) (_ha' : -a ≠ 0) :
    temkin_theta R T (-a) K p = -temkin_theta R T a K p := by
  unfold temkin_theta
  field_simp [ha]

theorem temkin_log_split (K p : ℝ) (hK : 0 < K) (hp : 0 < p) :
    Real.log (K * p) = Real.log K + Real.log p :=
  Real.log_mul (ne_of_gt hK) (ne_of_gt hp)

theorem temkin_linear_in_log_p (R T a K p : ℝ) (_ha : a ≠ 0) (hK : 0 < K) (hp : 0 < p) :
    temkin_theta R T a K p = (R * T / a) * Real.log K + (R * T / a) * Real.log p := by
  unfold temkin_theta
  rw [temkin_log_split K p hK hp]
  ring

theorem temkin_nonneg_when_Kp_ge_one (R T a K p : ℝ) (_ha : a ≠ 0) (hcoef : 0 ≤ R * T / a)
    (hkp : 1 ≤ K * p) (_hkp_pos : 0 < K * p) : 0 ≤ temkin_theta R T a K p := by
  unfold temkin_theta
  exact mul_nonneg hcoef (Real.log_nonneg (by exact hkp))

end ScientificMemory.Chemistry.Adsorption.Temkin1941
