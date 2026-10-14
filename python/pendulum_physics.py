"""Kater's pendulum physics: g calculation, amplitude correction, decay fit."""

import numpy as np
from typing import Tuple


def katers_g_ideal(L: float, T: float) -> float:
    """g = 4*pi^2*L / T^2 — equal-period case."""
    return 4.0 * np.pi**2 * L / T**2


def katers_g_bessel(T1: float, T2: float, L: float,
                    h1_minus_h2: float) -> float:
    """Bessel's formula for unequal periods.
    
    g = 8*pi^2 / [ (T1^2 + T2^2)/L + (T1^2 - T2^2)/(h1 - h2) ]
    """
    num = 8.0 * np.pi**2
    den = (T1**2 + T2**2) / L + (T1**2 - T2**2) / h1_minus_h2
    return num / den


def compute_g(T1: float, T2: float, L: float,
              h1_minus_h2: float = None,
              threshold: float = 0.001) -> Tuple[float, str]:
    """Smart g calculation: uses ideal if T1 ~= T2, Bessel's otherwise.
    
    Returns (g_value, formula_used_string).
    """
    rel_diff = abs(T1 - T2) / ((T1 + T2) / 2.0)

    if rel_diff < threshold or h1_minus_h2 is None or h1_minus_h2 == 0:
        T_avg = (T1 + T2) / 2.0
        g = katers_g_ideal(L, T_avg)
        return g, f"Ideal (T1 ~= T2, rel diff = {rel_diff:.4%})"
    else:
        g = katers_g_bessel(T1, T2, L, h1_minus_h2)
        return g, f"Bessel's (rel diff = {rel_diff:.4%})"


def amplitude_correction(T_measured: float, theta0_rad: float) -> float:
    """T0 ~= T_measured * (1 - theta0^2 / 16)."""
    return T_measured * (1.0 - theta0_rad**2 / 16.0)


def fit_decay(swing_numbers: np.ndarray,
              amplitudes: np.ndarray) -> Tuple[float, float, float]:
    """Fit theta(n) = theta0 * exp(-gamma * n). Returns (theta0, gamma, Q)."""
    mask = amplitudes > 0
    n, a = swing_numbers[mask], amplitudes[mask]
    if len(n) < 2:
        return 0.0, 0.0, float('inf')
    log_a = np.log(a)
    slope, intercept = np.polyfit(n, log_a, 1)
    gamma = -slope
    theta0 = np.exp(intercept)
    Q = np.pi / gamma if gamma > 0 else float('inf')
    return float(theta0), float(gamma), float(Q)


def logarithmic_decrement(theta_start: float, theta_end: float,
                          N: int) -> float:
    """delta = (1/N) * ln(theta_start / theta_end)."""
    if theta_end <= 0 or N <= 0:
        return 0.0
    return (1.0 / N) * np.log(theta_start / theta_end)
