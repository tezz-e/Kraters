"""Generate publication-grade 300 DPI figures for Kater's Pendulum Research Paper from raw CSV data."""

import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Set publication style
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9.5,
    'ytick.labelsize': 9.5,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    'mathtext.fontset': 'stix',
    'lines.linewidth': 1.2,
    'axes.linewidth': 0.8,
    'grid.alpha': 0.35,
    'grid.linestyle': '--'
})

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(PROJECT_DIR, "docs", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Helper to read CSV
def read_csv(fpath):
    with open(fpath, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    t = np.array([float(r['t']) for r in rows])
    gz = np.array([float(r['gz']) for r in rows])
    ay = np.array([float(r['ay']) for r in rows])
    ax = np.array([float(r['ax']) for r in rows])
    az = np.array([float(r['az']) for r in rows])
    return t, gz, ay, ax, az

p1_oct15 = os.path.join(PROJECT_DIR, "python", "data", "20261015_095301_pivot1.csv")
p2_oct15 = os.path.join(PROJECT_DIR, "python", "data", "20261015_095301_pivot2.csv")
p1_oct17 = os.path.join(PROJECT_DIR, "python", "data", "20261017_082917_pivot1.csv")
p2_oct17 = os.path.join(PROJECT_DIR, "python", "data", "20261017_082917_pivot2.csv")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 1: Raw Kinematic Waveforms & Zero-Crossing Detection
# ─────────────────────────────────────────────────────────────────────────────
print("[1/4] Generating Figure 1: Raw Kinematic Waveforms...")
t1, gz1, ay1, ax1, az1 = read_csv(p1_oct15)
t2, gz2, ay2, ax2, az2 = read_csv(p2_oct15)

fig, axes = plt.subplots(2, 2, figsize=(10, 5.5), dpi=300)

# Window of 10 seconds for clarity
w1 = (t1 >= t1[0] + 5.0) & (t1 <= t1[0] + 15.0)
w2 = (t2 >= t2[0] + 5.0) & (t2 <= t2[0] + 15.0)

# (a) Pivot 1 Angular Velocity
axes[0, 0].plot(t1[w1] - t1[w1][0], gz1[w1], color='#0066cc', label=r'$\omega_z(t)$ (Gyro)')
axes[0, 0].axhline(0, color='gray', linestyle='--', linewidth=0.7)
# Highlight zero crossings
zero_crossings_1 = np.where(np.diff(np.signbit(gz1[w1])))[0]
axes[0, 0].plot(t1[w1][zero_crossings_1] - t1[w1][0], gz1[w1][zero_crossings_1], 'ro', markersize=4, label='Zero-Crossings')
axes[0, 0].set_title(r'(a) Pivot 1: Angular Velocity $\omega_z(t)$ ($T_1 \approx 1.69\ \mathrm{s}$)')
axes[0, 0].set_ylabel(r'$\omega_z$ [deg/s]')
axes[0, 0].grid(True)
axes[0, 0].legend(loc='upper right')

# (b) Pivot 2 Angular Velocity
axes[0, 1].plot(t2[w2] - t2[w2][0], gz2[w2], color='#cc3300', label=r'$\omega_z(t)$ (Gyro)')
axes[0, 1].axhline(0, color='gray', linestyle='--', linewidth=0.7)
zero_crossings_2 = np.where(np.diff(np.signbit(gz2[w2])))[0]
axes[0, 1].plot(t2[w2][zero_crossings_2] - t2[w2][0], gz2[w2][zero_crossings_2], 'ro', markersize=4, label='Zero-Crossings')
axes[0, 1].set_title(r'(b) Pivot 2: Angular Velocity $\omega_z(t)$ ($T_2 \approx 1.77\ \mathrm{s}$)')
axes[0, 1].set_ylabel(r'$\omega_z$ [deg/s]')
axes[0, 1].grid(True)
axes[0, 1].legend(loc='upper right')

# (c) Pivot 1 Accelerations (Rod vs Perp)
axes[1, 0].plot(t1[w1] - t1[w1][0], ay1[w1], color='#2ca02c', label=r'$a_{\mathrm{rod}}$ ($a_y \approx -1.0g$)')
axes[1, 0].plot(t1[w1] - t1[w1][0], ax1[w1], color='#9467bd', label=r'$a_{\mathrm{perp}}$ ($a_x \approx 0.0g$)')
axes[1, 0].set_title(r'(c) Pivot 1: Tri-axial Accelerations ($a_{\mathrm{rod}}$ and $a_{\mathrm{perp}}$)')
axes[1, 0].set_xlabel('Relative Time [s]')
axes[1, 0].set_ylabel('Acceleration [g]')
axes[1, 0].grid(True)
axes[1, 0].legend(loc='lower right')

# (d) Pivot 2 Accelerations (Inverted Rod)
axes[1, 1].plot(t2[w2] - t2[w2][0], ay2[w2], color='#2ca02c', label=r'$a_{\mathrm{rod}}$ ($a_y \approx +0.95g$)')
axes[1, 1].plot(t2[w2] - t2[w2][0], ax2[w2], color='#9467bd', label=r'$a_{\mathrm{perp}}$ ($a_x \approx +0.20g$)')
axes[1, 1].set_title(r'(d) Pivot 2: Inverted Accelerations ($a_{\mathrm{rod}}$ inverted by 180°)')
axes[1, 1].set_xlabel('Relative Time [s]')
axes[1, 1].set_ylabel('Acceleration [g]')
axes[1, 1].grid(True)
axes[1, 1].legend(loc='lower right')

plt.tight_layout()
fig1_path = os.path.join(FIG_DIR, "fig1_waveforms.png")
plt.savefig(fig1_path, dpi=300)
plt.close()
print(f"Saved: {fig1_path}")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 2: Amplitude Decay Envelopes & Exponential Fits
# ─────────────────────────────────────────────────────────────────────────────
print("[2/4] Generating Figure 2: Amplitude Decay Envelopes & Quality Factor Q...")
import sys
sys.path.append(os.path.join(PROJECT_DIR, "python"))
from data_processor import DataProcessor, Method
from pendulum_physics import fit_decay

proc1 = DataProcessor(a_rest=-1.0, gyro_axis='gz', accel_rod_axis='ay', accel_perp_axis='ax', min_peak_omega_deg=0.8)
proc1.start_recording()
for r in csv.DictReader(open(p1_oct15)):
    s = {k: float(v) for k, v in r.items()}
    s['ir'] = int(s['ir'])
    proc1.process_sample(s)
proc1.stop_recording()
n1, a1 = proc1.get_decay_data()
th0_1, gam_1, Q_1 = fit_decay(n1, a1)

proc2 = DataProcessor(a_rest=1.0, gyro_axis='gz', accel_rod_axis='ay', accel_perp_axis='ax', min_peak_omega_deg=0.8)
proc2.start_recording()
for r in csv.DictReader(open(p2_oct15)):
    s = {k: float(v) for k, v in r.items()}
    s['ir'] = int(s['ir'])
    proc2.process_sample(s)
proc2.stop_recording()
n2, a2 = proc2.get_decay_data()
th0_2, gam_2, Q_2 = fit_decay(n2, a2)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=300)

# Pivot 1 Decay Fit
fit_x1 = np.linspace(n1[0], n1[-1], 200)
fit_y1 = th0_1 * np.exp(-gam_1 * fit_x1)
ax1.scatter(n1, a1, color='#0066cc', s=16, alpha=0.85, label='Measured Peak $\\theta_0(n)$')
ax1.plot(fit_x1, fit_y1, color='#009933', linewidth=1.8, linestyle='--',
         label=f'Exponential Fit: $\\theta_0 e^{{-\\gamma n}}$\n$\\theta_0 = {th0_1:.2f}^\\circ$, $\\gamma = {gam_1:.5f}$\n$Q = {Q_1:.1f}$')
ax1.set_title(r'(a) Pivot 1: Amplitude Decay & Quality Factor $Q = 681$')
ax1.set_xlabel('Oscillation Number ($n$)')
ax1.set_ylabel(r'Peak Amplitude $\theta_0$ [deg]')
ax1.grid(True)
ax1.legend(loc='upper right')

# Pivot 2 Decay Fit
fit_x2 = np.linspace(n2[0], n2[-1], 200)
fit_y2 = th0_2 * np.exp(-gam_2 * fit_x2)
ax2.scatter(n2, a2, color='#cc3300', s=16, alpha=0.85, label='Measured Peak $\\theta_0(n)$')
ax2.plot(fit_x2, fit_y2, color='#009933', linewidth=1.8, linestyle='--',
         label=f'Exponential Fit: $\\theta_0 e^{{-\\gamma n}}$\n$\\theta_0 = {th0_2:.2f}^\\circ$, $\\gamma = {gam_2:.5f}$\n$Q = {Q_2:.1f}$')
ax2.set_title(r'(b) Pivot 2: Amplitude Decay & Quality Factor $Q = 601$')
ax2.set_xlabel('Oscillation Number ($n$)')
ax2.set_ylabel(r'Peak Amplitude $\theta_0$ [deg]')
ax2.grid(True)
ax2.legend(loc='upper right')

plt.tight_layout()
fig2_path = os.path.join(FIG_DIR, "fig2_decay_fits.png")
plt.savefig(fig2_path, dpi=300)
plt.close()
print(f"Saved: {fig2_path}")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 3: Software Post-Mortem Diagnostics (Bifurcation & 4.81g Outliers)
# ─────────────────────────────────────────────────────────────────────────────
print("[3/4] Generating Figure 3: Software Post-Mortem Diagnostics...")
# Show the bifurcation artifact: naive abs(current_angle) vs half-swing integration
# And show the period sequence with the 2 tail outliers (3.55s and 5.32s)
import json
with open(os.path.join(PROJECT_DIR, "python", "data", "20261017_082917_results.json")) as f:
    res_bad = json.load(f)

periods_bad = res_bad['trial2']['periods_gyro_all']
amplitudes_bifurcated = res_bad['trial2']['decay_amplitudes']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=300)

# (a) Bifurcation vs Integrated Decay
n_bif = np.arange(len(amplitudes_bifurcated)) * 0.5
ax1.plot(n_bif[:40], amplitudes_bifurcated[:40], 'ro-', markersize=4, linewidth=0.8,
         label='Uncorrected: Accelerometer Tilt Offset\n(Bifurcated: $19.7^\\circ$ vs $3.7^\\circ$)')
# Contrast with true half-swing integrated amplitude
ax1.plot(n2[:40], a2[:40], 'bo-', markersize=4, linewidth=1.2,
         label=r'Corrected: Half-Swing Gyro $\frac{1}{2}\int|\omega|dt$' + '\n(Monotonic exponential decay)')
ax1.set_title('(a) Artifact 1: Tilt Bifurcation vs. True Decay')
ax1.set_xlabel('Oscillation Number ($n$)')
ax1.set_ylabel(r'Amplitude Reading $\theta$ [deg]')
ax1.grid(True)
ax1.legend(loc='center right')

# (b) Tail Outliers causing 4.81g collapse
cycles = np.arange(1, len(periods_bad) + 1)
ax2.plot(cycles[:-2], periods_bad[:-2], 'bs-', markersize=5, label=f'Clean Oscillations ($T_2 = 1.7718\\ \\mathrm{{s}}$)')
ax2.plot(cycles[-2:], periods_bad[-2:], 'r^--', markersize=7, linewidth=1.5,
         label=r'Missed Cycles ($\omega_{\mathrm{peak}} < 3^\circ/\mathrm{s}$)' + '\n$3.55\\ \\mathrm{s}$ (2×) & $5.32\\ \\mathrm{s}$ (3×)\n$\\rightarrow$ Raw mean $2.038\\ \\mathrm{s} \\rightarrow g = 4.81\\ \\mathrm{m/s}^2$')
ax2.axhline(1.7718, color='green', linestyle=':', label='True Median Period ($1.7718\\ \\mathrm{s}$)')
ax2.set_title('(b) Artifact 2: Low-Amplitude Tail Skips (4.81g Root Cause)')
ax2.set_xlabel('Recorded Cycle Number')
ax2.set_ylabel('Measured Period $T_2$ [s]')
ax2.set_ylim(1.5, 5.8)
ax2.grid(True)
ax2.legend(loc='upper left')

plt.tight_layout()
fig3_path = os.path.join(FIG_DIR, "fig3_post_mortem_diagnostics.png")
plt.savefig(fig3_path, dpi=300)
plt.close()
print(f"Saved: {fig3_path}")

# ─────────────────────────────────────────────────────────────────────────────
# Figure 4: Phase Space Trajectory & Bessel Error Attenuation
# ─────────────────────────────────────────────────────────────────────────────
print("[4/4] Generating Figure 4: Phase Space & Bessel Sensitivity Surface...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=300)

# (a) Phase portrait (omega vs theta)
# Compute theta via integration for a clean 30s slice
slice_idx = (t1 >= t1[0] + 5.0) & (t1 <= t1[0] + 35.0)
dt = np.diff(t1[slice_idx])
theta_int = np.cumsum(np.radians(gz1[slice_idx][:-1]) * dt)
theta_int_deg = np.degrees(theta_int - np.mean(theta_int))

ax1.plot(theta_int_deg, gz1[slice_idx][:-1], color='#1f77b4', linewidth=0.6, alpha=0.8)
ax1.set_title(r'(a) Phase Space Portrait: $\omega_z(\theta)$ (Spiral Decay)')
ax1.set_xlabel(r'Oscillation Angle $\theta$ [deg]')
ax1.set_ylabel(r'Angular Velocity $\omega_z$ [deg/s]')
ax1.grid(True)

# (b) Bessel Error Suppression vs Period Difference (T1 - T2)
# Show the partial derivative |dg/dd| as a function of (T2 - T1)
T1_nom = 1.6904
delta_T = np.linspace(-0.25, 0.25, 200)
T2_range = T1_nom + delta_T
d_nom = -0.140

# dg/dd multiplier: (T1^2 - T2^2) / d^2
den = (T1_nom**2 + T2_range**2)/1.0 + (T1_nom**2 - T2_range**2)/d_nom
sensitivity = np.abs((8.0 * np.pi**2 / den**2) * (T1_nom**2 - T2_range**2) / (d_nom**2))

ax2.plot(delta_T, sensitivity, color='#d62728', linewidth=1.8, label=r'$|\partial g / \partial (h_1 - h_2)|$ Sensitivity')
ax2.axvline(0, color='gray', linestyle='--', label=r'Equal Period ($T_1 = T_2 \to \partial g/\partial d = 0$)')
ax2.plot(1.7732 - 1.6904, 17.826, 'k*', markersize=10, label=r'Our Experiment: $\Delta T = 0.083\ \mathrm{s}$' + '\n' + r'(Attenuation factor $\approx 4\times$)')
ax2.set_title(r'(b) Bessel Error Mitigation: $\frac{\partial g}{\partial(h_1 - h_2)}$ vs $(T_2 - T_1)$')
ax2.set_xlabel(r'Period Difference $(T_2 - T_1)$ [s]')
ax2.set_ylabel(r'Center-of-Mass Error Multiplier $[\mathrm{s}^{-2}]$')
ax2.grid(True)
ax2.legend(loc='upper right')

plt.tight_layout()
fig4_path = os.path.join(FIG_DIR, "fig4_phase_space_and_bessel_sensitivity.png")
plt.savefig(fig4_path, dpi=300)
plt.close()
print(f"Saved: {fig4_path}")

print("\nALL 4 PUBLICATION FIGURES GENERATED SUCCESSFULLY AT 300 DPI!")
