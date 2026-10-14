# Automated Kater's Reversible Pendulum Experiment System
## Complete Physical Theory, Mathematical Formulations, Sensor Fusion, and System Architecture

---

## 1. Executive Summary & System Overview

This system provides automated, high-precision measurement of local gravitational acceleration ($g$) and damping characteristics using a **Kater's Reversible Pendulum**. The apparatus combines embedded sensor telemetry (NodeMCU ESP8266 + MPU-6050 6-DOF IMU + IR break-beam sensor) with a desktop application (Python 3 / PyQt5 / pyqtgraph) to compare three independent timing methods:

1. **Automated IMU Gyroscope Zero-Crossing:** Detects velocity turning points at the oscillation extremes ($\omega = 0$).
2. **Automated IR Break-Beam Sensor:** Interrupt-driven microsecond midpoint detection at the center of swing ($\theta = 0$).
3. **Manual Stopwatch Input:** Human-timed baseline representing traditional lab methodology.

```
 +-----------------------------------------------------------------------------------------+
 |                                    PHYSICAL APPARATUS                                    |
 |  [ Knife Edge 1 ]                                                       [ Knife Edge 2 ] |
 |          │                                                                      │        |
 |          └─────────────[ MPU-6050 IMU ]─────[ Rod / Bob ]─────[ IR Flag ]────────┘        |
 +----------------------------------│──────────────────────────────────│-------------------+
                                    │ I2C (400 kHz)                    │ GPIO ISR (D5)
                                    ▼                                  ▼
                     +-------------------------------------------------------+
                     |                 NodeMCU ESP8266 MCU                   |
                     |  - mpu.calcOffsets(true, false) (Gyro-only zeroing)   |
                     |  - attachInterrupt(irISR, CHANGE)                     |
                     |  - Microsecond midpoint calculation: (t1 + t2) / 2    |
                     |  - 100 Hz CSV Telemetry + High-speed Event Stream     |
                     +---------------------------│---------------------------+
                                                 │ USB-Serial (115200 baud)
                                                 ▼
                     +-------------------------------------------------------+
                     |           Python Host Application (PyQt5)             |
                     |                                                       |
                     |  [ SerialReader Thread ]                              |
                     |        │                                              |
                     |        ▼                                              |
                     |  [ DataProcessor Engine ]                             |
                     |    ├─ Dominant-Axis Rest Calibration                  |
                     |    ├─ Adaptive Complementary Filter (α = 0.88 - 0.98) |
                     |    ├─ Hysteresis Gyro Zero-Crossing Detection         |
                     |    └─ 2-Pass IR Full-Period Detection                 |
                     |        │                                              |
                     |        ▼                                              |
                     |  [ Experiment Engine ]                                |
                     |    ├─ Borda Finite-Amplitude Correction (T0)          |
                     |    ├─ Bessel's Exact Formula for g                    |
                     |    └─ Damping Exponential Fit (γ, Q, δ)               |
                     |        │                                              |
                     |        ▼                                              |
                     |  [ GUI Dashboard & DataLogger ]                       |
                     |    ├─ Live 2D Vector Animation & Phase Plot           |
                     |    ├─ Real-Time Tilt θ(t) & Angular Velocity ω(t)     |
                     |    ├─ Results Table (Gyro vs IR vs Manual)            |
                     |    └─ Raw CSV & Session JSON Persistence              |
                     +---------------------------│---------------------------+
```

---

## 2. Theoretical Physics of Kater's Pendulum

### 2.1 The Physical Pendulum Equation of Motion

A rigid body of mass $m$ pivoted at a distance $h$ from its center of mass (CM) oscillates under gravity. For small angular displacements ($\theta \ll 1\text{ rad}$), torque $\tau = -m g h \sin\theta \approx -m g h \theta$, giving:

$$I \frac{d^2\theta}{dt^2} + m g h \theta = 0$$

where $I$ is the mass moment of inertia about the suspension axis. By the parallel-axis theorem:

$$I = I_{\text{cm}} + m h^2 = m (k^2 + h^2)$$

where $k$ is the radius of gyration of the pendulum about its center of mass ($I_{\text{cm}} = m k^2$). Substituting into the equation of motion:

$$\frac{d^2\theta}{dt^2} + \frac{g h}{k^2 + h^2} \theta = 0$$

The natural angular frequency $\omega_0$ and period $T$ are:

$$\omega_0 = \sqrt{\frac{g h}{k^2 + h^2}}, \qquad T = 2\pi \sqrt{\frac{k^2 + h^2}{g h}}$$

### 2.2 The Principle of Reversibility (Kater's Theorem)

A physical pendulum has two conjugate suspension points (knife-edges) on opposite sides of the center of mass:
* **Pivot 1:** distance $h_1$ from CM $\implies T_1 = 2\pi \sqrt{\frac{k^2 + h_1^2}{g h_1}}$
* **Pivot 2:** distance $h_2$ from CM $\implies T_2 = 2\pi \sqrt{\frac{k^2 + h_2^2}{g h_2}}$

Squaring both equations:

$$\frac{g h_1 T_1^2}{4\pi^2} = k^2 + h_1^2, \qquad \frac{g h_2 T_2^2}{4\pi^2} = k^2 + h_2^2$$

Subtracting the two equations eliminates the unknown moment of inertia parameter $k^2$:

$$\frac{g}{4\pi^2} (h_1 T_1^2 - h_2 T_2^2) = h_1^2 - h_2^2 = (h_1 - h_2)(h_1 + h_2)$$

When the adjustable weights are positioned such that the two periods are identical ($T_1 = T_2 = T$):

$$\frac{g T^2}{4\pi^2} (h_1 - h_2) = (h_1 - h_2)(h_1 + h_2)$$

Dividing by $(h_1 - h_2)$ (since $h_1 \ne h_2$):

$$T = 2\pi \sqrt{\frac{h_1 + h_2}{g}} = 2\pi \sqrt{\frac{L}{g}}$$

where $L = h_1 + h_2$ is the **exact distance between the two knife edges**. 

> **Kater's Core Advantage:** The acceleration due to gravity $g$ depends **only** on the distance between the knife-edges $L$ and the period $T$. The complex mass distribution, moment of inertia, and exact location of the center of mass completely cancel out.

---

### 2.3 Bessel's Exact Formula for Unequal Periods ($T_1 \ne T_2$)

In practice, adjusting weights to reach $T_1 = T_2$ to within $0.0001\text{ s}$ is extremely tedious. Friedrich Bessel derived the exact algebraic relation between $g$, $T_1$, $T_2$, $L = h_1 + h_2$, and $(h_1 - h_2)$:

Adding and subtracting the squared period equations yields two simultaneous linear equations:

$$\frac{g}{4\pi^2} (h_1 T_1^2 + h_2 T_2^2) = 2k^2 + h_1^2 + h_2^2$$
$$\frac{g}{4\pi^2} (h_1 T_1^2 - h_2 T_2^2) = h_1^2 - h_2^2$$

Combining these relations eliminates $k^2$ without requiring $T_1 = T_2$:

$$\frac{8\pi^2}{g} = \frac{T_1^2 + T_2^2}{h_1 + h_2} + \frac{T_1^2 - T_2^2}{h_1 - h_2}$$

Solving explicitly for gravitational acceleration $g$:

$$g_{\text{Bessel}} = \frac{8\pi^2}{\displaystyle \frac{T_1^2 + T_2^2}{L} + \frac{T_1^2 - T_2^2}{h_1 - h_2}}$$

#### The Ideal Approximation ($|T_1 - T_2| \ll 1$)
When the relative period difference is small ($\frac{|T_1 - T_2|}{T_{\text{avg}}} < 0.05$), the second term $\frac{T_1^2 - T_2^2}{h_1 - h_2} \approx 0$, reducing to the simplified standard formula:

$$g_{\text{ideal}} = \frac{4\pi^2 L}{T_{\text{avg}}^2}, \qquad \text{where } T_{\text{avg}} = \frac{T_1 + T_2}{2}$$

The software implements both formulas:
```python
# python/pendulum_physics.py
def calculate_g_bessel(T1, T2, L, h1_minus_h2):
    denom = (T1**2 + T2**2) / L + (T1**2 - T2**2) / h1_minus_h2
    return (8.0 * np.pi**2) / denom

def calculate_g_ideal(T1, T2, L):
    T_avg = 0.5 * (T1 + T2)
    return (4.0 * np.pi**2 * L) / (T_avg**2)
```

---

### 2.4 Borda's Finite-Amplitude Correction

The simple harmonic formula assumes an infinitesimal swing angle ($\sin\theta \approx \theta$). For finite peak amplitude $\theta_0$, the exact elliptic integral expands as:

$$T(\theta_0) = T_0 \left[ 1 + \frac{1}{4}\sin^2\left(\frac{\theta_0}{2}\right) + \frac{9}{64}\sin^4\left(\frac{\theta_0}{2}\right) + \dots \right]$$

Using the small-angle Taylor expansion $\sin(\theta_0 / 2) \approx \theta_0 / 2$:

$$T(\theta_0) \approx T_0 \left( 1 + \frac{\theta_0^2}{16} \right)$$

Inverting to solve for the true infinitesimal period $T_0$:

$$T_0 = T_{\text{measured}} \left( 1 - \frac{\theta_0^2}{16} \right)$$

where $\theta_0$ is the angular amplitude in radians.

* **Example:** At $\theta_0 = 5^\circ = 0.08727\text{ rad}$:
  $$\frac{\theta_0^2}{16} = \frac{(0.08727)^2}{16} = 0.000476 \quad (0.048\% \text{ correction})$$
  For $T = 2.0000\text{ s}$, the correction reduces the measured period by $\approx 0.95\text{ ms}$, which shifts calculated $g$ by $\approx +0.01\text{ m/s}^2$. The system applies this correction dynamically to every cycle using the measured peak amplitude of that specific swing.

---

### 2.5 Damped Oscillations and Quality Factor ($Q$)

Under viscous air resistance and knife-edge friction, the equation of motion is:

$$\frac{d^2\theta}{dt^2} + 2\gamma \frac{d\theta}{dt} + \omega_0^2 \theta = 0$$

where $\gamma$ is the damping attenuation coefficient ($\text{s}^{-1}$). For weak damping ($\gamma \ll \omega_0$), the solution is:

$$\theta(t) = \theta_0 e^{-\gamma t} \cos(\omega_d t + \phi), \qquad \omega_d = \sqrt{\omega_0^2 - \gamma^2} \approx \omega_0$$

Expressed per oscillation cycle number $n$ ($t = n T$):

$$\theta(n) = \theta_0 e^{-\delta n}$$

where $\delta = \gamma T$ is the **logarithmic decrement**:

$$\delta = \ln\left(\frac{\theta_n}{\theta_{n+1}}\right)$$

The **Quality Factor ($Q$)** measures energy retention per cycle:

$$Q = \frac{\omega_0}{2\gamma} = \frac{2\pi f_0}{2 (\delta / T)} = \frac{\pi}{\delta}$$

In `pendulum_physics.py`, the parameters are fitted via log-linear regression:

$$\ln \theta_n = \ln \theta_0 - \delta \cdot n$$

```python
slope, intercept = np.polyfit(cycle_numbers, np.log(amplitudes_deg), 1)
delta = -slope
gamma = delta / T_period
Q = np.pi / delta
```

---

## 3. Hardware Architecture & Firmware Implementation

### 3.1 NodeMCU ESP8266 Pinout & Communication

| Hardware Pin | Function | Electrical Configuration |
| :--- | :--- | :--- |
| **`D2` (GPIO 4)** | I2C SDA | Pull-up via MPU-6050 module ($400\text{ kHz}$ Fast Mode) |
| **`D1` (GPIO 5)** | I2C SCL | Pull-up via MPU-6050 module ($400\text{ kHz}$ Fast Mode) |
| **`D5` (GPIO 14)** | IR Sensor Signal | `INPUT_PULLUP`, Hardware Interrupt on `CHANGE` |
| **`3V3` / `GND`** | Sensor Power | 3.3V DC rail (< 15 mA total current consumption) |
| **USB Micro** | Serial Telemetry | CH340 USB-UART, $115200\text{ baud}$, 8N1 |

---

### 3.2 Firmware Gyro-Only Calibration

The standard `MPU6050_light` library function `calcOffsets(true, true)` calibrates both the gyroscope and accelerometer offsets by assuming the chip is resting horizontally on a flat table with $+1g$ on the Z axis. On a Kater's pendulum:
1. The sensor hangs vertically along the rod ($a_y$ or $a_z \approx \pm 1g$).
2. For Pivot 2, the pendulum is inverted upside down ($a_{\text{rod}} \to -a_{\text{rod}}$).

Calling `calcOffsets(true, true)` would subtract Earth's gravity as an "offset error". The firmware explicitly sets:

```cpp
// firmware/src/main.cpp
mpu.calcOffsets(true, false); // gyro offsets ONLY
```

Python performs true 3-axis rest gravity calibration dynamically.

---

### 3.3 Hardware Interrupt IR Edge Detection

Polling an optical sensor at $100\text{ Hz}$ ($10\text{ ms}$ interval) introduces up to $\pm 10\text{ ms}$ of phase jitter. For a pendulum swinging at $v_{\text{max}} = 0.3\text{ m/s}$, a $3\text{ mm}$ flag blocks the beam for:

$$\Delta t_{\text{beam}} = \frac{0.003\text{ m}}{0.3\text{ m/s}} = 10\text{ ms}$$

A 10 ms polling loop can miss the flag entirely. The firmware attaches a hardware interrupt to pin `D5`:

```cpp
// firmware/src/main.cpp
volatile int ir_idle_val = HIGH;
volatile unsigned long t_enter_us = 0;
volatile unsigned long t_exit_us = 0;
volatile unsigned long last_ir_mid_us = 0;
volatile bool ir_mid_ready = false;
volatile bool ir_latched = false;
volatile unsigned long last_edge_time_us = 0;

IRAM_ATTR void irISR() {
    unsigned long now_us = micros();
    if (now_us - last_edge_time_us < 2000) return; // 2 ms debounce
    last_edge_time_us = now_us;

    int pinVal = digitalRead(IR_SENSOR_PIN);
    if (pinVal != ir_idle_val) {
        // Flag entered beam
        t_enter_us = now_us;
        ir_latched = true;
    } else if (t_enter_us != 0) {
        // Flag exited beam -> compute center midpoint
        t_exit_us = now_us;
        last_ir_mid_us = (t_enter_us + t_exit_us) / 2;
        ir_mid_ready = true;
        t_enter_us = 0;
    }
}
```

#### Why the Midpoint Formula Cancels Mechanical Delay
The flag has physical width $w$. As the pendulum damps, its velocity $v$ decreases:
* Time of entry: $t_{\text{enter}} = t_{\text{center}} - \frac{w}{2v}$
* Time of exit: $t_{\text{exit}} = t_{\text{center}} + \frac{w}{2v}$
* Midpoint average:
  $$t_{\text{mid}} = \frac{t_{\text{enter}} + t_{\text{exit}}}{2} = \frac{(t_{\text{center}} - \frac{w}{2v}) + (t_{\text{center}} + \frac{w}{2v})}{2} = t_{\text{center}}$$

The width $w$ and speed $v$ cancel out, giving sub-millisecond center passage timing across all swing amplitudes.

---

## 4. Signal Processing & Sensor Fusion Pipeline

```
  [ Raw Accelerometer: ax, ay, az ]            [ Raw Gyroscope: gx, gy, gz ]
                 │                                            │
                 ▼                                            ▼
   Low-Pass Filter (α = 0.25)                   Low-Pass Filter (α = 0.25)
                 │                                            │
                 ▼                                            ▼
    Signed Tilt Angle:                             Angular Velocity:
    θ_acc = atan2(a_perp, a_rod)                      ω = filt_omega
                 │                                            │
                 └──────────────────────┬─────────────────────┘
                                        ▼
                         [ Adaptive Complementary Filter ]
                           blend = clip(|ω| / 25°/s, 0, 1)
                           α = (1 - blend) * 0.88 + blend * 0.98
                           θ_k = α(θ_{k-1} + ω·dt) + (1 - α)θ_acc
                                        │
                                        ▼
                         Fused State: θ(t) & ω(t)
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
     [ 2D Vector Visualizer ]                     [ Period Detection Engines ]
     - Smooth arm rotation θ                      - Gyro Zero-Crossing (Reversals)
     - Tangential arrow ω                         - IR Midpoint (k - (k-2))
```

---

### 4.1 Dominant-Axis Rest Calibration

When the user clicks **Calibrate Zero**, the pendulum hangs stationary. The firmware sends `# CAL_DONE` after gyro bias zeroing. Python then collects 100 gravity samples across all three accelerometer axes:

$$\bar{a}_x = \frac{1}{N}\sum a_x, \qquad \bar{a}_y = \frac{1}{N}\sum a_y, \qquad \bar{a}_z = \frac{1}{N}\sum a_z$$

The system determines the mounting orientation by identifying which axis measures $|a| \approx 1.0g$:

```python
abs_axes = {'az': abs(mean_z), 'ay': abs(mean_y), 'ax': abs(mean_x)}
dominant = max(abs_axes, key=abs_axes.get)
```

| Dominant Axis | Physical Mounting | Accelerometer Rod Axis | Perpendicular Axis | Gyro Rotation Axis |
| :--- | :--- | :--- | :--- | :--- |
| **`ay`** | Vertical (pins up/down along rod) | `ay` | `ax` | `gz` (rotation in X-Y plane) |
| **`az`** | Flat on rod face | `az` | `ax` | `gy` (rotation in X-Z plane) |
| **`ax`** | Side mount | `ax` | `ay` | `gz` (rotation in Y-X plane) |

Once detected, the orientation is **locked** for the duration of the trial, preventing mid-swing axis flipping.

---

### 4.2 Linear Tilt Angle Formulation

The tilt angle is computed using the 2-axis arc-tangent:

$$\theta_{\text{acc}} = \text{atan2}(a_{\text{perp}} \cdot \text{rod\_sign},\, a_{\text{rod}} \cdot \text{rod\_sign})$$

where:
$$\text{rod\_sign} = \begin{cases} +1.0 & \text{if } a_{\text{rest}} \ge 0 \quad (\text{Pivot 1}) \\ -1.0 & \text{if } a_{\text{rest}} < 0 \quad (\text{Pivot 2 - inverted}) \end{cases}$$

Multiplying both components by `rod_sign` preserves the coordinate frame orientation when the physical pendulum is inverted for Pivot 2, preventing the accelerometer from fighting the gyroscope.

---

### 4.3 Adaptive Complementary Filter

The complementary filter blends high-pass filtered gyro integration with low-pass filtered accelerometer tilt:

$$\theta_k = \alpha (\theta_{k-1} + \omega_k \Delta t) + (1 - \alpha) \theta_{\text{acc}, k}$$

#### The Problem with Static $\alpha = 0.98$
At $\Delta t = 0.01\text{ s}$ ($100\text{ Hz}$), the filter time constant is:

$$\tau = \frac{\alpha \Delta t}{1 - \alpha} = \frac{0.98 \times 0.01}{0.02} = 0.49\text{ s}$$

It takes $3\tau \approx 1.5\text{ seconds}$ to reflect a change in tilt. When held stationary or tilted slowly by hand ($\omega \approx 0$), the visualizer appears frozen.

#### The Adaptive Solution
The system computes an angular velocity blend factor:

$$\text{blend} = \text{clip}\left(\frac{|\omega|}{25.0^\circ/\text{s}},\, 0.0,\, 1.0\right)$$
$$\alpha = (1.0 - \text{blend}) \times 0.88 + \text{blend} \times 0.98$$

* **Static / Slow Hand Tilt ($|\omega| < 2.5^\circ/\text{s}$):**
  $\alpha \approx 0.88 \implies \tau = \frac{0.88 \times 0.01}{0.12} = 0.073\text{ s} \ (73\text{ ms})$. The 2D pendulum tracks hand motion instantaneously.
* **Dynamic Pendulum Swing ($|\omega| > 25^\circ/\text{s}$):**
  $\alpha = 0.98 \implies$ Gyroscope integration dominates, rejecting centripetal acceleration ($r\omega^2$) and rod vibrations.

---

## 5. Period Detection Algorithms

### 5.1 Gyroscope Zero-Crossing Detection (Reversals)

At the extreme points of swing, velocity reaches zero ($\omega = 0$) and reverses direction.

```
          ω > 0 (swinging right)
                 ▲
                 │        t_zero (reversal)
─────────────────┼───────────X───────────────────► time
                 │            \
                 ▼             ω_curr < 0
          ω_prev > 0
```

#### Gate 1: Peak Angular Velocity Threshold
To prevent sensor noise near $\omega = 0$ from triggering false events, every half-swing must achieve a minimum velocity:

$$\max(|\omega|) \ge \omega_{\text{min\_peak}} = 3.0^\circ/\text{s}$$

#### Gate 2: Strict Direction Alternation
Reversals must alternate strictly: $\text{Left} \to \text{Right} \to \text{Left} \to \text{Right}$.

#### Gate 3: Sub-Sample Linear Interpolation
Because samples arrive at discrete 10 ms intervals, the zero-crossing timestamp $t_{\text{zero}}$ is linearly interpolated between $t_{k-1}$ and $t_k$:

$$t_{\text{zero}} = t_{k-1} - \omega_{k-1} \left( \frac{t_k - t_{k-1}}{\omega_k - \omega_{k-1}} \right)$$

#### Gate 4: Minimum Half-Period Rejection
Events occurring within $0.35\text{ s}$ of the previous reversal are rejected:

$$t_{\text{zero}} - t_{\text{last\_reversal}} \ge 0.35\text{ s}$$

#### Full Period Calculation
A complete period $T$ requires two full half-swings. Periods are recorded on every **Right reversal**:

$$T_{\text{gyro}} = t_{\text{zero, right}}[k] - t_{\text{zero, right}}[k-1]$$

---

### 5.2 IR Break-Beam Center-Pass Detection

The pendulum crosses the center position **twice per full oscillation**:
1. Pass $k=1$: Moving **Left $\to$ Right**
2. Pass $k=2$: Moving **Right $\to$ Left**
3. Pass $k=3$: Moving **Left $\to$ Right** (1 full cycle complete)

Measuring between consecutive passes ($k$ and $k-1$) would yield a half-period ($T/2$), causing calculated $g$ to be $4\times$ too high. The software stores center passage timestamps and measures between every **second** passage:

$$T_{\text{ir}} = t_{\text{center}}[k] - t_{\text{center}}[k-2] \qquad \text{for } k \in \{3, 5, 7, \dots\}$$

The amplitude for Borda correction is linked from the nearest gyro turning point:

$$T_{\text{ir, corrected}} = T_{\text{ir}} \left(1 - \frac{\theta_0^2}{16}\right)$$

---

## 6. Uncertainty Propagation & Error Analysis

The total uncertainty in calculated $g$ is derived via partial derivatives:

$$g = \frac{4\pi^2 L}{T^2}$$

$$\ln g = \ln(4\pi^2) + \ln L - 2\ln T$$

Differentiating:

$$\frac{\delta g}{g} = \frac{\delta L}{L} - 2\frac{\delta T}{T}$$

Assuming independent, random, Gaussian errors:

$$\frac{\sigma_g}{g} = \sqrt{\left(\frac{\sigma_L}{L}\right)^2 + \left(2\frac{\sigma_{\bar{T}}}{\bar{T}}\right)^2}$$

where:
$$\sigma_{\bar{T}} = \frac{\sigma_T}{\sqrt{N}} = \frac{1}{\sqrt{N}}\sqrt{\frac{1}{N-1}\sum_{i=1}^N (T_i - \bar{T})^2}$$

* For $L = 1.0000 \pm 0.0005\text{ m}$ ($0.05\%$ error)
* For $\bar{T} = 2.0062\text{ s}$ with $\sigma_{\bar{T}} = 0.0002\text{ s}$ ($0.01\%$ error)
* Total expected uncertainty:
  $$\frac{\sigma_g}{g} = \sqrt{(0.0005)^2 + (2 \times 0.0001)^2} = \sqrt{2.5 \times 10^{-7} + 4 \times 10^{-8}} \approx 0.054\%$$
  $$\sigma_g \approx 9.81 \times 0.00054 \approx \pm 0.005\text{ m/s}^2$$

---

## 7. Parameters & Configuration Reference

| Parameter | Location | Default Value | Physical Units | Function |
| :--- | :--- | :--- | :--- | :--- |
| `SERIAL_BAUD` | `firmware/include/config.h` | `115200` | baud | UART baud rate between ESP8266 and PC |
| `STREAM_INTERVAL_MS` | `firmware/include/config.h` | `10` | ms | Telemetry frame interval ($100\text{ Hz}$) |
| `IR_DEBOUNCE_US` | `firmware/src/main.cpp` | `2000` | $\mu\text{s}$ | ISR noise debounce filter |
| `comp_alpha` | `python/data_processor.py` | `0.98` | unitless | High-speed complementary filter weight |
| `comp_alpha_slow` | `python/data_processor.py` | `0.88` | unitless | Low-speed / static tilt weight |
| `lpf_alpha` | `python/data_processor.py` | `0.25` | unitless | Pre-filter single-pole smoothing factor |
| `min_peak_omega_deg` | `python/data_processor.py` | `3.0` | $^\circ/\text{s}$ | Zero-crossing peak threshold |
| `min_half_period` | `python/data_processor.py` | `0.35` | s | Glitch and chatter rejection window |
| `L` | `python/experiment.py` | `1.000` | m | Distance between knife-edges |
| `h1_minus_h2` | `python/experiment.py` | `0.050` | m | Distance difference from CM to knife-edges |
| `g_accepted` | `python/experiment.py` | `9.80665` | $\text{m/s}^2$ | Standard local gravitational reference |
| `WINDOW_SIZE` | `python/widgets/trial_page.py`| `400` | samples | Scrolling graph width ($4\text{ s}$ at $100\text{ Hz}$) |

---

## 8. Summary of Results Output

At the conclusion of Pivot 1 and Pivot 2 trials, the software generates:
1. **Measured Periods ($T_1, T_2$):** Mean and standard deviation across all recorded cycles.
2. **Corrected Periods ($T_{1,0}, T_{2,0}$):** Small-amplitude corrected periods using peak amplitude tracking.
3. **Calculated $g$:** Computed via both Bessel's exact equation and the ideal simple-pendulum approximation.
4. **Accuracy Comparison:** Relative percentage error against standard $g = 9.80665\text{ m/s}^2$.
5. **Damping Analysis:** Fitted decay constant $\gamma$, quality factor $Q$, and logarithmic decrement $\delta$.
6. **Data Export:** Complete raw sample telemetry saved to timestamped CSV files and session metrics saved to JSON.
