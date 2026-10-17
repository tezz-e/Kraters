"""Real-time pendulum swing analysis: sensor fusion + gyro zero-crossing + IR edge detection.

Produces SwingEvents (reversals), PeriodMeasurements, and smooth real-time
2D angle/phase tracking from streaming IMU + IR data.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Callable
from enum import Enum


class Method(Enum):
    GYRO = "gyro"       # Zero-crossing at extremes
    IR = "ir"           # Break-beam at center


@dataclass
class SwingEvent:
    """A detected swing reversal (from gyro zero-crossing)."""
    timestamp: float
    amplitude_rad: float
    amplitude_deg: float
    direction: str            # 'left' or 'right'
    raw_accel_rod: float


@dataclass
class IRCrossing:
    """An IR beam crossing event (pendulum passing center)."""
    timestamp: float
    direction: str            # 'entering' or 'leaving' based on IR transition


@dataclass
class PeriodMeasurement:
    """A measured full period from either method."""
    T_measured: float
    T_corrected: float        # amplitude-corrected
    method: Method
    amplitude_avg: float      # average amplitude during this cycle (rad)
    swing_number: int


class DataProcessor:
    """Dual-method period detection and real-time 2D state estimation."""

    def __init__(self, a_rest: float = 1.0,
                 gyro_axis: str = 'gy',
                 accel_rod_axis: str = 'az',
                 accel_perp_axis: str = 'ax',
                 gyro_in_deg: bool = True,
                 comp_alpha: float = 0.98,
                 lpf_alpha: float = 0.25,
                 min_peak_omega_deg: float = 3.0,
                 min_half_period: float = 0.35,
                 on_swing: Optional[Callable] = None,
                 on_period: Optional[Callable] = None,
                 on_ir_crossing: Optional[Callable] = None):
        self.a_rest = a_rest if (a_rest and abs(a_rest) > 0.1) else 1.0
        self.gyro_axis = gyro_axis
        self.accel_rod_axis = accel_rod_axis
        self.accel_perp_axis = accel_perp_axis
        self.gyro_in_deg = gyro_in_deg

        # Filter & threshold parameters
        self.comp_alpha = comp_alpha
        self.lpf_alpha = lpf_alpha
        self.min_peak_omega = np.radians(min_peak_omega_deg) if gyro_in_deg else min_peak_omega_deg
        self.min_half_period = min_half_period

        # Callbacks
        self.on_swing = on_swing
        self.on_period = on_period
        self.on_ir_crossing = on_ir_crossing

        # ── Real-time 2D visualization state (updated every sample) ──
        self.current_angle_rad: float = 0.0
        self.current_angle_deg: float = 0.0
        self.current_omega_rad: float = 0.0
        self.current_phase_rad: float = 0.0   # [-pi, pi] phase in time period
        self._last_t: Optional[float] = None
        self._filt_omega: float = 0.0
        self._filt_a_rod: float = self.a_rest
        self._filt_a_perp: float = 0.0
        self._perp_offset: float = 0.0

        self._half_swing_omega_integral: float = 0.0
        self._theta_acc_dc: Optional[float] = None

        # ── Gyro zero-crossing state with hysteresis ─────────────────
        self._prev_sample = None
        self._prev_filt_omega: Optional[float] = None
        self._peak_omega_since_crossing: float = 0.0
        self._last_reversal_dir: Optional[str] = None
        self._last_reversal_time: Optional[float] = None

        self.swings: List[SwingEvent] = []
        self._last_pos_crossing: Optional[SwingEvent] = None
        self._last_neg_crossing: Optional[SwingEvent] = None

        # ── IR edge detection state ──────────────────────────────────
        self._prev_ir = None
        self._ir_idle_state: Optional[int] = None
        self._seen_isr_ir = False
        self.ir_crossings: List[IRCrossing] = []
        self._ir_enter_time: Optional[float] = None
        self._ir_center_times: List[float] = []  # Midpoints of each center pass

        # ── Period results (both methods) ────────────────────────────
        self.periods_gyro: List[PeriodMeasurement] = []
        self.periods_ir: List[PeriodMeasurement] = []

        # ── Recording control ────────────────────────────────────────
        self.recording = False
        self._swing_counter_gyro = 0
        self._swing_counter_ir = 0

    def set_rest_calibration(self, a_rest: float, a_perp_rest: float = 0.0):
        """Update rest calibration values so tilt angle is zeroed at vertical."""
        if a_rest and abs(a_rest) > 0.1:
            self.a_rest = a_rest
            self._filt_a_rod = a_rest
        self._perp_offset = a_perp_rest
        self._theta_acc_dc = 0.0

    def start_recording(self):
        """Begin a new recording trial. Resets all trial state."""
        self.swings.clear()
        self.ir_crossings.clear()
        self.periods_gyro.clear()
        self.periods_ir.clear()
        self._prev_sample = None
        self._prev_filt_omega = None
        self._half_swing_omega_integral = 0.0
        self._peak_omega_since_crossing = 0.0
        self._last_reversal_dir = None
        self._last_reversal_time = None
        self._last_pos_crossing = None
        self._prev_ir = None
        self._seen_isr_ir = False
        self._ir_enter_time = None
        self._ir_center_times.clear()
        self._swing_counter_gyro = 0
        self._swing_counter_ir = 0
        self.recording = True

    def stop_recording(self):
        """Stop recording. Data remains accessible for results."""
        self.recording = False

    def process_sample(self, sample: dict):
        """Process one IMU+IR sample. Always updates 2D angle; records events if recording."""
        self._update_kinematics(sample)

        if not self.recording:
            self._prev_sample = sample
            self._prev_filt_omega = self._filt_omega
            self._prev_ir = sample.get('ir', 1)
            if self._ir_idle_state is None:
                self._ir_idle_state = sample.get('ir', 1)
            return

        self._detect_gyro_crossing(sample)
        self._detect_ir_edge(sample)

        self._prev_sample = sample
        self._prev_filt_omega = self._filt_omega

    # ── Sensor Fusion: Smooth 2D Angle & Phase Tracking ──────────────

    def _update_kinematics(self, sample: dict):
        t = sample['t']
        raw_g = sample[self.gyro_axis]
        omega = np.radians(raw_g) if self.gyro_in_deg else raw_g

        a_rod = sample[self.accel_rod_axis]
        a_perp = sample.get(self.accel_perp_axis, 0.0) - self._perp_offset

        if self._last_t is None or (t - self._last_t) <= 0 or (t - self._last_t) > 0.5:
            dt = 0.01  # fallback 100 Hz
            self._filt_omega = omega
            self._filt_a_rod = a_rod
            self._filt_a_perp = a_perp
        else:
            dt = t - self._last_t
            a = self.lpf_alpha
            self._filt_omega = a * omega + (1.0 - a) * self._filt_omega
            self._filt_a_rod = a * a_rod + (1.0 - a) * self._filt_a_rod
            self._filt_a_perp = a * a_perp + (1.0 - a) * self._filt_a_perp

        self._last_t = t

        # Accumulate angular distance for the current half-swing
        if self.recording and 0 < dt < 0.2:
            self._half_swing_omega_integral += abs(self._filt_omega) * dt

        # Robust rod sign: auto-detect from filtered rod acceleration
        # Normalizes gravity vector so theta_acc is always centered near 0 deg,
        # whether mounted upright or inverted (Pivot 1 vs Pivot 2)
        if abs(self._filt_a_rod) > 0.2:
            rod_sign = 1.0 if self._filt_a_rod >= 0 else -1.0
        else:
            rod_sign = 1.0 if self.a_rest >= 0 else -1.0

        raw_theta_acc = np.arctan2(self._filt_a_perp * rod_sign, abs(self._filt_a_rod))

        # Dynamic equilibrium tracker: cancel any static mounting tilt DC bias
        if self._theta_acc_dc is None:
            self._theta_acc_dc = raw_theta_acc
        else:
            # Slow adaptation to track physical vertical equilibrium
            self._theta_acc_dc = 0.998 * self._theta_acc_dc + 0.002 * raw_theta_acc

        centered_theta_acc = raw_theta_acc - self._theta_acc_dc

        # Complementary filter: high-pass gyro integration + low-pass accel tilt
        # During recording, keep alpha at comp_alpha (0.98) to prevent turning-point tangential
        # acceleration contamination (r*theta_ddot) from attenuating the measured peak amplitude.
        # Only use the fast-settling 0.88 blend when not recording (e.g. idle/setup tilt tracking).
        if self.recording:
            alpha = self.comp_alpha
        else:
            omega_deg_abs = abs(float(np.degrees(self._filt_omega)))
            blend = float(np.clip(omega_deg_abs / 25.0, 0.0, 1.0))
            alpha = (1.0 - blend) * 0.88 + blend * self.comp_alpha

        self.current_angle_rad = (
            alpha * (self.current_angle_rad + self._filt_omega * dt)
            + (1.0 - alpha) * centered_theta_acc
        )
        self.current_angle_deg = float(np.degrees(self.current_angle_rad))
        self.current_omega_rad = float(self._filt_omega)

        # Phase in the oscillation cycle [-pi, pi]: atan2(-omega / omega0, theta)
        mean_T, _ = self.get_mean_period(Method.GYRO, last_n=5)
        omega0 = (2.0 * np.pi / mean_T) if (mean_T and mean_T > 0.2) else np.sqrt(9.81 / 1.0)
        self.current_phase_rad = float(
            np.arctan2(-self.current_omega_rad / omega0, self.current_angle_rad)
        )

    # ── Gyro Zero-Crossing (with Hysteresis & Peak Validation) ───────

    def _detect_gyro_crossing(self, sample: dict):
        if self._prev_sample is None or self._prev_filt_omega is None:
            return

        g_prev = self._prev_filt_omega
        g_curr = self._filt_omega

        # Track maximum angular speed reached during the current half-swing
        if abs(g_curr) > self._peak_omega_since_crossing:
            self._peak_omega_since_crossing = abs(g_curr)

        # Check for zero-crossing
        if g_prev * g_curr > 0 or (g_prev == 0 and g_curr == 0):
            return

        # Gate 1: Reject noise wiggles that never reached minimum swing speed
        if self._peak_omega_since_crossing < self.min_peak_omega:
            return

        direction = 'right' if g_prev > 0 else 'left'

        # Gate 2: Must strictly alternate left <-> right
        if self._last_reversal_dir == direction:
            return

        # Sub-sample linear interpolation for exact zero-crossing timestamp
        t_prev = self._prev_sample['t']
        t_curr = sample['t']
        denom = g_curr - g_prev
        if abs(denom) > 1e-9:
            t_zero = t_prev - g_prev * (t_curr - t_prev) / denom
        else:
            t_zero = 0.5 * (t_prev + t_curr)

        # Gate 3: Minimum half-period elapsed since previous opposite reversal
        if self._last_reversal_time is not None:
            if (t_zero - self._last_reversal_time) < self.min_half_period:
                return

        # Reset peak tracker and update reversal state
        self._peak_omega_since_crossing = 0.0
        self._last_reversal_dir = direction
        self._last_reversal_time = t_zero

        # Interpolate rod accel for logging
        a_prev = self._prev_sample[self.accel_rod_axis]
        a_curr = sample[self.accel_rod_axis]
        frac = np.clip((t_zero - t_prev) / max(t_curr - t_prev, 1e-6), 0.0, 1.0)
        a_cross = a_prev + frac * (a_curr - a_prev)

        # Physical half-swing gyro integration (0.5 * integral(|omega| dt))
        # Strictly immune to accelerometer DC offset, inverted gravity, and tilt
        if self._half_swing_omega_integral > 0.01 and len(self.swings) > 0:
            theta_amp = 0.5 * self._half_swing_omega_integral
        else:
            theta_amp = abs(self.current_angle_rad)

        self._half_swing_omega_integral = 0.0

        swing = SwingEvent(
            timestamp=float(t_zero),
            amplitude_rad=float(theta_amp),
            amplitude_deg=float(np.degrees(theta_amp)),
            direction=direction,
            raw_accel_rod=float(a_cross),
        )
        self.swings.append(swing)

        # Backfill initial swing with first full half-swing amplitude
        if len(self.swings) == 2:
            self.swings[0].amplitude_rad = self.swings[1].amplitude_rad
            self.swings[0].amplitude_deg = self.swings[1].amplitude_deg

        if self.on_swing:
            self.on_swing(swing)

        # Compute full period once per complete oscillation (on 'right' reversals)
        if direction == 'right':
            if self._last_pos_crossing is not None:
                T = t_zero - self._last_pos_crossing.timestamp
                if T > 2.0 * self.min_half_period:
                    self._record_gyro_period(T, self._last_pos_crossing, swing)
            self._last_pos_crossing = swing
        else:
            self._last_neg_crossing = swing

    def _record_gyro_period(self, T_meas: float, s1: SwingEvent, s2: SwingEvent):
        theta_avg = 0.5 * (s1.amplitude_rad + s2.amplitude_rad)
        T_corr = T_meas * (1.0 - theta_avg**2 / 16.0)

        p = PeriodMeasurement(
            T_measured=float(T_meas),
            T_corrected=float(T_corr),
            method=Method.GYRO,
            amplitude_avg=float(theta_avg),
            swing_number=self._swing_counter_gyro,
        )
        self.periods_gyro.append(p)
        self._swing_counter_gyro += 1

        if self.on_period:
            self.on_period(p)

    def process_ir_midpoint(self, t_center: float):
        """Called when high-precision # IR_MID:<sec> event is received from firmware ISR."""
        self._seen_isr_ir = True
        if not self.recording:
            return

        crossing = IRCrossing(timestamp=t_center, direction='center')
        self.ir_crossings.append(crossing)
        if self.on_ir_crossing:
            self.on_ir_crossing(crossing)

        if self._ir_center_times and (t_center - self._ir_center_times[-1]) < self.min_half_period:
            return

        self._ir_center_times.append(t_center)

        n_passes = len(self._ir_center_times)
        if n_passes >= 3 and (n_passes % 2 == 1):
            T = self._ir_center_times[-1] - self._ir_center_times[-3]
            if T > 2.0 * self.min_half_period:
                amp = self._get_nearest_amplitude(t_center)
                T_corr = T * (1.0 - amp**2 / 16.0) if amp > 0 else T

                p = PeriodMeasurement(
                    T_measured=float(T),
                    T_corrected=float(T_corr),
                    method=Method.IR,
                    amplitude_avg=float(amp),
                    swing_number=self._swing_counter_ir,
                )
                self.periods_ir.append(p)
                self._swing_counter_ir += 1

                if self.on_period:
                    self.on_period(p)

    # ── IR Break-Beam Center Crossing Detection (Polling Fallback) ───

    def _detect_ir_edge(self, sample: dict):
        if getattr(self, '_seen_isr_ir', False):
            return  # hardware ISR takes precedence

        ir_curr = sample['ir']
        if self._prev_ir is None:
            self._prev_ir = ir_curr
            self._ir_idle_state = ir_curr
            return

        if ir_curr == self._prev_ir:
            return

        t = sample['t']
        if self._ir_idle_state is None:
            self._ir_idle_state = self._prev_ir

        is_entering = (ir_curr != self._ir_idle_state)
        direction = 'entering' if is_entering else 'leaving'
        crossing = IRCrossing(timestamp=t, direction=direction)
        self.ir_crossings.append(crossing)

        if self.on_ir_crossing:
            self.on_ir_crossing(crossing)

        if is_entering:
            # Beam broken (entering beam)
            self._ir_enter_time = t
        elif self._ir_enter_time is not None:
            # Beam restored (leaving beam) -> compute center midpoint
            t_center = 0.5 * (self._ir_enter_time + t)
            self._ir_enter_time = None

            # Debounce: ignore spurious glitches closer than min_half_period
            if self._ir_center_times and (t_center - self._ir_center_times[-1]) < self.min_half_period:
                self._prev_ir = ir_curr
                return

            self._ir_center_times.append(t_center)

            # One full period = 2 center passes (same movement direction: k and k-2)
            n_passes = len(self._ir_center_times)
            if n_passes >= 3 and (n_passes % 2 == 1):
                T = self._ir_center_times[-1] - self._ir_center_times[-3]
                if T > 2.0 * self.min_half_period:
                    amp = self._get_nearest_amplitude(t_center)
                    T_corr = T * (1.0 - amp**2 / 16.0) if amp > 0 else T

                    p = PeriodMeasurement(
                        T_measured=float(T),
                        T_corrected=float(T_corr),
                        method=Method.IR,
                        amplitude_avg=float(amp),
                        swing_number=self._swing_counter_ir,
                    )
                    self.periods_ir.append(p)
                    self._swing_counter_ir += 1

                    if self.on_period:
                        self.on_period(p)

        self._prev_ir = ir_curr

    def _get_nearest_amplitude(self, t: float) -> float:
        """Get amplitude from the nearest gyro swing event."""
        if not self.swings:
            return 0.0
        best = min(self.swings[-10:], key=lambda s: abs(s.timestamp - t))
        return best.amplitude_rad

    # ── Aggregate Getters ────────────────────────────────────────────

    def get_mean_period(self, method: Method, last_n: int = 10, corrected: bool = True):
        """Return (mean, std) of the last N periods for a method (raw or corrected)."""
        periods = self.periods_gyro if method == Method.GYRO else self.periods_ir
        if not periods:
            return None, None
        recent = periods[-last_n:]
        T_vals = np.array([p.T_corrected if corrected else p.T_measured for p in recent])
        return float(np.mean(T_vals)), float(np.std(T_vals))

    def get_all_periods(self, method: Method):
        """Return array of all corrected periods for a method."""
        periods = self.periods_gyro if method == Method.GYRO else self.periods_ir
        if not periods:
            return np.array([])
        return np.array([p.T_corrected for p in periods])

    def get_decay_data(self):
        """Return (cycle_numbers, amplitudes_deg) where cycle_numbers is in FULL cycles."""
        if not self.swings:
            return np.array([]), np.array([])
        # Each reversal is 0.5 cycles apart (0.0, 0.5, 1.0, 1.5, ...)
        cycle_numbers = np.arange(len(self.swings), dtype=float) * 0.5
        amplitudes_deg = np.array([s.amplitude_deg for s in self.swings])
        return cycle_numbers, amplitudes_deg

    def get_oscillation_count(self):
        """Number of complete oscillations detected (gyro method)."""
        return len(self.periods_gyro)
