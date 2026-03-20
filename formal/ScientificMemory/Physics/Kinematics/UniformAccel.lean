import Mathlib

namespace ScientificMemory.Physics.Kinematics.UniformAccel

/-- Final velocity under constant acceleration: `u + a t`. -/
theorem velocity_at_time (u a t : ℚ) : u + a * t = u + t * a := by ring

/-- Displacement identity under constant acceleration (algebraic rearrangement). -/
theorem displacement_rearranged (u a t : ℚ) :
    u * t + (1 / 2 : ℚ) * a * t ^ 2 = t * (u + (1 / 2 : ℚ) * a * t) := by ring

/-- Velocity change over interval `dt`. -/
theorem delta_velocity (u a dt : ℚ) : (u + a * dt) - u = a * dt := by ring

/-- Relating displacement over `2T` to twice displacement over `T` plus `a T^2`. -/
theorem displacement_double_time (u a T : ℚ) :
    u * (2 * T) + (1 / 2 : ℚ) * a * (2 * T) ^ 2
      = 2 * (u * T + (1 / 2 : ℚ) * a * T ^ 2) + a * T ^ 2 := by ring

/-- Average of endpoints sums to total span (algebra). -/
theorem average_endpoints (u v : ℚ) : (u + v) / 2 + (u + v) / 2 = u + v := by ring

/-- Acceleration from velocity change over nonzero duration. -/
theorem accel_from_delta_v (dv dt : ℚ) (hdt : dt ≠ 0) : (dv / dt) * dt = dv := by
  field_simp [hdt]

/-- Expand squared final velocity `(u + a t)²`. -/
theorem velocity_squared_expand (u a t : ℚ) :
    (u + a * t) ^ 2 = u ^ 2 + 2 * u * a * t + (a * t) ^ 2 := by ring

/-- Torricelli-style identity: `v² = u² + 2 a s` with `v = u + a t` and `s = u t + ½ a t²`. -/
theorem torricelli_squared (u a t : ℚ) :
    (u + a * t) ^ 2 = u ^ 2 + 2 * a * (u * t + (1 / 2 : ℚ) * a * t ^ 2) := by ring

/-- With zero acceleration, velocity stays at `u`. -/
theorem zero_accel_velocity_constant (u t : ℚ) : u + (0 : ℚ) * t = u := by ring

/-- Zero elapsed time gives zero displacement from the standard formula. -/
theorem zero_time_zero_displacement (u a : ℚ) :
    u * (0 : ℚ) + (1 / 2 : ℚ) * a * (0 : ℚ) ^ 2 = 0 := by ring

/-- Average of initial and final speeds times `t` equals `u t + ½ a t²` when `v = u + a t`. -/
theorem average_velocity_displacement (u a t : ℚ) :
    ((u + (u + a * t)) / (2 : ℚ)) * t = u * t + (1 / 2 : ℚ) * a * t ^ 2 := by ring

/-- Velocity composition across adjacent time intervals (same `a`). -/
theorem velocity_time_additivity (u a t s : ℚ) : u + a * (t + s) = (u + a * t) + a * s := by ring

/-- Displacement formula is linear in initial velocity (for fixed `a`, `t`). -/
theorem displacement_linearity_in_u (u1 u2 a t : ℚ) :
    (u1 + u2) * t + (1 / 2 : ℚ) * a * t ^ 2 =
      u1 * t + u2 * t + (1 / 2 : ℚ) * a * t ^ 2 := by ring

/-- The `½ a t²` term doubles to `a t²`. -/
theorem double_half_quadratic_term (a t : ℚ) :
    2 * ((1 / 2 : ℚ) * a * t ^ 2) = a * t ^ 2 := by ring

/-- Mean acceleration `(v - u) / Δt` equals `a` when `v = u + a Δt` and `Δt ≠ 0`. -/
theorem mean_acceleration_over_interval (u a dt : ℚ) (hdt : dt ≠ 0) :
    ((u + a * dt) - u) / dt = a := by
  have hs : (u + a * dt) - u = a * dt := by ring
  rw [hs]
  field_simp [hdt]

end ScientificMemory.Physics.Kinematics.UniformAccel
