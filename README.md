# Kater's Reversible Pendulum — Physics Lab Experiment System

An automated data collection and analysis suite for first-year physics lab experiments with Kater's Reversible Pendulum.

## Overview

This project replaces traditional stopwatch timing with high-speed sensor automation:
- **MPU6050 (6-axis IMU)**: Mounted flat on the pendulum rod, detects swing reversals via gyroscope zero-crossings and measures instantaneous tilt angles for amplitude correction.
- **IR Break-Beam Sensor**: Detects center-line equilibrium crossings.
- **Interactive Physics & Apparatus Guide**: Open `index.html` (or run `open_guide.bat`) in any browser for tabbed notes covering the complete apparatus deconstruction, governing formulae, derivations, and live physics simulations.
- **Manual Stopwatch Input**: Allows side-by-side comparison between manual human timing and automated sensor timing in the final report.

---

## Hardware Configuration (NodeMCU ESP8266)

| Sensor | Sensor Pin | NodeMCU Pin | GPIO | Function |
|---|---|---|---|---|
| **MPU6050** | VCC | 3V3 / VIN | — | Power |
| **MPU6050** | GND | GND | — | Ground |
| **MPU6050** | SDA | **D2** | GPIO 4 | I2C Data |
| **MPU6050** | SCL | **D1** | GPIO 5 | I2C Clock |
| **IR Sensor** | OUT / DO | **D5** | GPIO 14 | Digital Input (`INPUT_PULLUP`) |
| **IR Sensor** | VCC / GND | 3V3 / GND | — | Power & Ground |

---

## Software Architecture

```
physicsproject/
├── firmware/
│   ├── platformio.ini         # ESP8266 PlatformIO config (115200 baud, CH340)
│   ├── include/config.h       # Pin assignments & 100 Hz sampling rate
│   └── src/main.cpp           # MPU6050 + IR reader + serial command protocol
└── python/
    ├── requirements.txt       # PyQt5, pyqtgraph, pyserial, numpy
    ├── main.py                # Qt Wizard GUI application
    ├── serial_reader.py       # Background threaded serial reader
    ├── data_processor.py      # Real-time zero-crossing & IR edge detector
    ├── pendulum_physics.py    # Kater's formula, Bessel's formula & decay fit
    ├── data_logger.py         # CSV & JSON report exporter
    └── widgets/
        ├── pendulum_widget.py # 2D animated pendulum arm with velocity arrow
        ├── setup_page.py      # Step 1: Connection & parameter entry
        ├── trial_page.py      # Steps 2 & 3: Live trial recording & stopwatch entry
        └── results_page.py    # Step 4: Comparison dashboard & accuracy report
```

---

## Quick Start (For Lab Sessions)

> **Complete Lab Guide:** See [TEAMMATE_HANDOFF_GUIDE.md](TEAMMATE_HANDOFF_GUIDE.md) for full physical setup diagrams, center-of-mass balancing guide, and Bessel's formula derivation.

### How to Run:
1. Download this repo as a ZIP (click the green **`<> Code`** button -> **`Download ZIP`**) and extract it.
2. Plug the ESP8266 NodeMCU into the PC via USB.
3. Double-click **`run.bat`**. It will automatically check Python, auto-install any missing dependencies (`PyQt5`, `pyqtgraph`, `numpy`, `pyserial`), and launch the application window.

### 4-Step Wizard Workflow:
1. **Step 1 — Setup**: Select COM port, enter Knife-Edge distance $L = 1.000\text{ m}$ and distances to Center of Mass ($h_1 \approx 0.43\text{ m}$, $h_2 \approx 0.57\text{ m}$), and click **Connect**.
2. **Step 2 — Pivot 1 Trial**: Hang pendulum on knife-edge 1 (heavy weight near top). Click **Calibrate Zero** while still, deflect gently ($4^\circ\text{--}5^\circ$), click **Start Trial**, record 40–50 oscillations, and proceed to Pivot 2.
3. **Step 3 — Pivot 2 Trial**: Invert the pendulum to knife-edge 2 (heavy weight near bottom) and repeat.
4. **Step 4 — Results & Comparison**: View the side-by-side comparison table showing $T_1$, $T_2$, Borda amplitude-corrected $T_0$, calculated $g$ ($\approx 9.81\text{ m/s}^2$), and error %. Live parameters can be recalculated directly on screen. Export raw CSV waveforms and JSON summaries with a single click.
