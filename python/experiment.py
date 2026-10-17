"""Experiment session state machine.

Tracks the overall experiment state: which trial we're on,
what data we've collected, and computes final results.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import numpy as np

from data_processor import DataProcessor, Method
from pendulum_physics import compute_g, fit_decay, logarithmic_decrement


class ExperimentState(Enum):
    SETUP = "setup"
    PIVOT1_READY = "pivot1_ready"
    PIVOT1_CALIBRATING = "pivot1_calibrating"
    PIVOT1_RECORDING = "pivot1_recording"
    PIVOT1_DONE = "pivot1_done"
    PIVOT2_READY = "pivot2_ready"
    PIVOT2_CALIBRATING = "pivot2_calibrating"
    PIVOT2_RECORDING = "pivot2_recording"
    PIVOT2_DONE = "pivot2_done"
    RESULTS = "results"


@dataclass
class TrialResult:
    """Results from one pivot trial."""
    pivot_name: str             # "Pivot 1" or "Pivot 2"
    
    # Gyro method
    T_gyro_mean: float = 0.0
    T_gyro_std: float = 0.0
    T_gyro_corrected: float = 0.0
    n_oscillations_gyro: int = 0
    
    # IR method
    T_ir_mean: float = 0.0
    T_ir_std: float = 0.0
    T_ir_corrected: float = 0.0
    n_oscillations_ir: int = 0
    
    # Manual stopwatch
    T_manual: Optional[float] = None
    n_oscillations_manual: Optional[int] = None
    
    # Amplitude data
    amplitude_start_deg: float = 0.0
    amplitude_end_deg: float = 0.0
    amplitude_mean_deg: float = 0.0
    
    # Decay fit
    decay_theta0: float = 0.0
    decay_gamma: float = 0.0
    quality_factor: float = 0.0
    log_decrement: float = 0.0
    
    # Raw arrays for plotting
    decay_swing_numbers: List = field(default_factory=list)
    decay_amplitudes: List = field(default_factory=list)
    periods_gyro_all: List = field(default_factory=list)
    periods_ir_all: List = field(default_factory=list)


class Experiment:
    """Manages the full Kater's pendulum experiment session."""

    def __init__(self):
        self.state = ExperimentState.SETUP
        self.L: float = 1.0                    # knife-edge distance (m)
        self.h1_minus_h2: Optional[float] = None  # asymmetry (m)
        self.g_accepted: float = 9.80665       # reference g
        
        self.trial1: Optional[TrialResult] = None
        self.trial2: Optional[TrialResult] = None

    def finalize_trial(self, processor: DataProcessor,
                       pivot_name: str,
                       manual_T: float = None,
                       manual_N: int = None) -> TrialResult:
        """Extract results from a completed trial's DataProcessor."""
        result = TrialResult(pivot_name=pivot_name)

        # Gyro periods
        T_gyro_raw, T_gyro_raw_std = processor.get_mean_period(Method.GYRO, last_n=999, corrected=False)
        T_gyro_corr, _ = processor.get_mean_period(Method.GYRO, last_n=999, corrected=True)
        if T_gyro_raw is not None:
            result.T_gyro_mean = T_gyro_raw
            result.T_gyro_std = T_gyro_raw_std
            result.T_gyro_corrected = T_gyro_corr if T_gyro_corr is not None else T_gyro_raw
            valid_periods = processor.get_all_periods(Method.GYRO)
            result.n_oscillations_gyro = len(valid_periods)
            result.periods_gyro_all = [float(x) for x in valid_periods]

        # IR periods
        T_ir_raw, T_ir_raw_std = processor.get_mean_period(Method.IR, last_n=999, corrected=False)
        T_ir_corr, _ = processor.get_mean_period(Method.IR, last_n=999, corrected=True)
        if T_ir_raw is not None:
            result.T_ir_mean = T_ir_raw
            result.T_ir_std = T_ir_raw_std
            result.T_ir_corrected = T_ir_corr if T_ir_corr is not None else T_ir_raw
            result.n_oscillations_ir = len(processor.periods_ir)
            result.periods_ir_all = [p.T_corrected for p in processor.periods_ir]

        # Manual
        if manual_T and manual_N and manual_N > 0:
            result.T_manual = manual_T / manual_N
            result.n_oscillations_manual = manual_N

        # Amplitude / decay
        swing_n, swing_amp = processor.get_decay_data()
        if len(swing_n) > 0:
            result.amplitude_start_deg = float(swing_amp[0])
            result.amplitude_end_deg = float(swing_amp[-1])
            result.amplitude_mean_deg = float(np.mean(swing_amp))
            result.decay_swing_numbers = swing_n.tolist()
            result.decay_amplitudes = swing_amp.tolist()

            if len(swing_n) > 3:
                theta0, gamma, Q = fit_decay(swing_n, swing_amp)
                result.decay_theta0 = theta0
                result.decay_gamma = gamma
                result.quality_factor = Q
                result.log_decrement = gamma  # delta = gamma per cycle

        return result

    def compute_results(self) -> Dict[str, Any]:
        """Compute final g values from both trials using all methods."""
        if not self.trial1 or not self.trial2:
            return {}

        results = {
            'L': self.L,
            'h1_minus_h2': self.h1_minus_h2,
            'g_accepted': self.g_accepted,
            'trial1': self.trial1.__dict__,
            'trial2': self.trial2.__dict__,
        }

        # ── g from Gyro method ─────────────────────
        T1_g = self.trial1.T_gyro_corrected
        T2_g = self.trial2.T_gyro_corrected
        if T1_g > 0 and T2_g > 0:
            g_gyro, formula = compute_g(T1_g, T2_g, self.L, self.h1_minus_h2)
            results['g_gyro'] = g_gyro
            results['g_gyro_formula'] = formula
            results['g_gyro_error_pct'] = abs(g_gyro - self.g_accepted) / self.g_accepted * 100

        # ── g from IR method ──────────────────────
        T1_ir = self.trial1.T_ir_corrected
        T2_ir = self.trial2.T_ir_corrected
        if T1_ir > 0 and T2_ir > 0:
            g_ir, formula = compute_g(T1_ir, T2_ir, self.L, self.h1_minus_h2)
            results['g_ir'] = g_ir
            results['g_ir_formula'] = formula
            results['g_ir_error_pct'] = abs(g_ir - self.g_accepted) / self.g_accepted * 100

        # ── g from Manual method ──────────────────
        T1_m = self.trial1.T_manual
        T2_m = self.trial2.T_manual
        if T1_m and T2_m:
            g_manual, formula = compute_g(T1_m, T2_m, self.L, self.h1_minus_h2)
            results['g_manual'] = g_manual
            results['g_manual_formula'] = formula
            results['g_manual_error_pct'] = abs(g_manual - self.g_accepted) / self.g_accepted * 100

        return results
