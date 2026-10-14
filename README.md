# Kater's Reversible Pendulum — Physics Lab Experiment System

An automated data collection and analysis suite for first-year physics lab experiments with Kater's Reversible Pendulum.

## Overview

This project replaces traditional stopwatch timing with high-speed sensor automation:
- **MPU6050 (6-axis IMU)**: Mounted flat on the pendulum rod, detects swing reversals via gyroscope zero-crossings and measures instantaneous tilt angles for amplitude correction.
- **IR Break-Beam Sensor**: Detects center-line equilibrium crossings.
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

## Quick Start

### 1. Launch the Desktop App

From the `physicsproject/python` directory:

```powershell
python main.py
```

### 2. Follow the 4-Step Wizard:
1. **Step 1 — Setup**: Select `COM13` (or your detected CH340 port), enter knife-edge distance $L$, and click **Connect**.
2. **Step 2 — Pivot 1 Trial**: Hang pendulum on knife-edge 1. Click **Calibrate** while still, push the pendulum gently, click **Start Recording**, record 20–30 oscillations, click **Stop Recording**, and enter your manual stopwatch time for comparison.
3. **Step 3 — Pivot 2 Trial**: Flip the pendulum to knife-edge 2 and repeat.
4. **Step 4 — Results & Comparison**: View the side-by-side comparison table showing $T_1$, $T_2$, amplitude-corrected $T_0$, calculated $g$, percentage error, and exponential decay curve. Click **Export Session Summary JSON** to save your report data.
