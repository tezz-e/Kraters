# Precision Gravimetry via Digital-Telemetry Reversible Compound Pendulum

An experimental physics and inertial telemetry system for high-precision determination of gravitational acceleration ($g$) using a digital reversible compound pendulum (Kater's pendulum) and Friedrich Bessel's asymmetric formulation.

---

## 📄 Formal Research Paper & Documentation

The full academic research paper, complete mathematical derivations, experimental uncertainty budgets, and software post-mortem analyses are available in the [`docs/`](docs/) directory:

* **Research Paper (Markdown):** [docs/RESEARCH_REPORT.md](docs/RESEARCH_REPORT.md)
* **Formatted Document (Word):** [docs/Katers_Pendulum_Research_Report.docx](docs/Katers_Pendulum_Research_Report.docx) *(483 native Word `OMath` equations, 0 LaTeX leaks, publication styling)*
* **Print-Ready PDF:** [docs/Katers_Pendulum_Research_Report.pdf](docs/Katers_Pendulum_Research_Report.pdf) *(A4 academic layout, vector equations)*
* **System Specification & Theory:** [SYSTEM_EXPLANATION.md](SYSTEM_EXPLANATION.md) *(Firmware ISR, complementary filter, and signal acquisition architecture)*
* **Interactive Physics Guide:** Open `index.html` (or run `open_guide.bat`) in any modern browser for interactive apparatus deconstruction and live kinematic simulations.

---

## 🔬 Experimental Results Summary

Evaluating physical telemetry gathered across independent multi-trial laboratory sessions:

| Metric | Dataset 1 (Nominal Balanced Run) | Dataset 2 (Extended Decay Run) |
| :--- | :--- | :--- |
| **Pivot 1 Period ($T_{1,0}$)** | $1.69042 \pm 0.00090\text{ s}$ ($\text{SEM} = 0.128\text{ ms}$, $N_1 = 49$) | $1.68440 \pm 0.00160\text{ s}$ ($\text{SEM} = 0.257\text{ ms}$, $N_1 = 39$) |
| **Pivot 2 Period ($T_{2,0}$)** | $1.77322 \pm 0.00144\text{ s}$ ($\text{SEM} = 0.200\text{ ms}$, $N_2 = 52$) | $1.77187 \pm 0.00706\text{ s}$ ($\text{SEM} = 0.689\text{ ms}$, $N_2 = 105$) |
| **Knife-Edge Separation ($L$)** | $1.0000 \pm 0.0005\text{ m}$ | $1.0000 \pm 0.0005\text{ m}$ |
| **Center-of-Mass Asymmetry ($h_1 - h_2$)** | $-0.1400 \pm 0.0014\text{ m}$ | $-0.1400 \pm 0.0014\text{ m}$ |
| **Calculated Gravity ($g$)** | **$9.8079 \pm 0.0264\text{ m/s}^2$** | **$9.7045 \pm 0.0358\text{ m/s}^2$** |
| **Discrepancy vs Standard $g_0$ ($9.80665\text{ m/s}^2$)** | **$+0.013\%$** (well within $\pm 0.27\%$ budget) | **$-1.04\%$** (demonstrating balance localization sensitivity) |
| **Quality Factor ($Q$)** | Pivot 1: $681.1$, Pivot 2: $601.2$ | Pivot 1: $235.0$, Pivot 2: $569.0$ |

---

## 🛠️ System Overview & Innovations

Traditional Kater's pendulum experiments rely on visual optical coincidence methods or hand-triggered stopwatches, requiring hours of tedious physical weight adjustments to equalize periods ($T_1 = T_2$). This system modernizes the methodology:

1. **Embedded MEMS Inertial Telemetry:** An onboard TDK InvenSense MPU-6050 6-DoF sensor samples angular velocity ($\omega_z$) and tri-axial acceleration at a nominal $100\text{ Hz}$ ($98.5\text{ Hz}$ effective rate).
2. **Sub-Sample Zero-Crossing Interpolation:** Linear interpolation at velocity reversals eliminates human reaction latency and recovers cycle periods to sub-millisecond precision.
3. **Bessel's Asymmetric Formulation:** Evaluates unequal periods ($T_1 \neq T_2$) directly via Bessel's exact equation, attenuating center-of-mass balance uncertainty by a factor of approximately $4\times$.
4. **Half-Swing Gyro Velocity Integration:** Amplitude is evaluated via $\theta_0 = \frac{1}{2} \int |\omega_z| dt$, providing absolute invariance against accelerometer mounting tilt and inverted orientation gravity offsets.
5. **Per-Cycle Analytic Borda Correction:** Automatically applies $T_0 \approx T_{\text{meas}}(1 - \theta_0^2/16)$ to eliminate finite-amplitude period elongation.

---

## 📐 Hardware Architecture

```
        Pivot 1 (K1)                                    Pivot 2 (K2)
         ▼                                               ▼
         |===|=======================●===================|===|
             [Heavy Bob]            CoM                 [Light Bob]
             |------- h1 = 0.430m ---|------ h2 = 0.570m ----|
             |------------------- L = 1.000m ----------------|
```

| Sensor / Module | Connection Pin | Microcontroller (NodeMCU ESP8266) | Function |
| :--- | :--- | :--- | :--- |
| **MPU-6050 IMU** | VCC / GND | 3V3 / GND | 3.3V Power & Ground |
| **MPU-6050 IMU** | SDA | **D2** (GPIO 4) | I2C Data ($400\text{ kHz}$ Fast Mode) |
| **MPU-6050 IMU** | SCL | **D1** (GPIO 5) | I2C Clock |
| **IR Photogate** | DO / OUT | **D5** (GPIO 14) | Hardware Interrupt Edge Timestamp (`micros()`) |

---

## 💻 Repository Structure

```
physicsproject/
├── docs/
│   ├── RESEARCH_REPORT.md             # Complete academic research paper
│   ├── Katers_Pendulum_Research_Report.docx  # Formatted Word paper (483 OMath equations)
│   ├── Katers_Pendulum_Research_Report.pdf   # Academic PDF paper
│   └── figures/                       # Publication-grade 300 DPI figures
│       ├── fig1_waveforms.png
│       ├── fig2_post_mortem_diagnostics.png
│       ├── fig3_decay_fits.png
│       └── fig4_phase_space_and_bessel_sensitivity.png
├── firmware/
│   ├── platformio.ini                 # ESP8266 PlatformIO config (115200 baud)
│   ├── include/config.h               # Pin assignments & ISR sampling definitions
│   └── src/main.cpp                   # Sensor acquisition & microsecond event stream
├── python/
│   ├── requirements.txt               # PyQt5, pyqtgraph, pyserial, numpy
│   ├── main.py                        # Desktop application controller
│   ├── data_processor.py              # Real-time zero-crossing & DSP engine
│   ├── pendulum_physics.py            # Bessel formula, Borda correction, decay fit
│   ├── serial_reader.py               # Background threaded serial reader
│   ├── data_logger.py                 # Telemetry CSV & JSON session exporter
│   ├── data/                          # Empirical laboratory CSV telemetry logs
│   └── widgets/                       # Qt user interface widgets
├── scripts/
│   ├── generate_figures.py            # Generates 300 DPI publication plots from CSVs
│   ├── generate_docx.py               # Compiles RESEARCH_REPORT.md into native Word docx
│   └── generate_pdf.py                # Compiles publication-grade PDF via headless Edge
├── SYSTEM_EXPLANATION.md              # In-depth system specification & DSP derivations
├── index.html                         # Interactive physics & apparatus guide
└── run.bat                            # One-click launch script
```

---

## 🚀 Running the Application

### Prerequisites
* Windows 10 / 11
* Python 3.10+ (with `PyQt5`, `pyqtgraph`, `numpy`, `pyserial`)

### Quick Start
1. Connect the ESP8266 microcontroller via USB.
2. Double-click **`run.bat`** (or execute `py python/main.py`).
3. Follow the 4-step wizard:
   - **Step 1 — Setup:** Confirm knife-edge geometry ($L = 1.000\text{ m}$, $h_1 = 0.430\text{ m}$, $h_2 = 0.570\text{ m}$) and click **Connect**.
   - **Step 2 — Pivot 1 Trial:** Suspend on Knife Edge 1, let hang motionless for auto-calibration, deflect $5^\circ\text{--}8^\circ$, and record 40–50 oscillations.
   - **Step 3 — Pivot 2 Trial:** Invert pendulum to Knife Edge 2 and repeat.
   - **Step 4 — Results:** View real-time Bessel-calculated $g$, finite-amplitude corrections, quality factor ($Q$), and export telemetry.
