# Kater's Pendulum Lab — Complete Teammate Hand-Off Guide & Physics Diagnosis

> **For Tomorrow's Lab Session**  
> Read this document before entering the lab. It explains why our previous runs gave $g \approx 13.2\text{--}13.9\text{ m/s}^2$, how to measure and set the physical apparatus with 100% clarity, and how to run the software with a single click.

---

## 1. Why Did the Previous Run Give $g \approx 13.2\text{--}13.9\text{ m/s}^2$?

### The Good News First
Our telemetry data from the MPU-6050 was **extraordinarily clean and accurate**:
* The oscillation waveform was a **textbook damped sinusoid**.
* Period on Pivot 1: $T_1 = \mathbf{1.6759\text{ s}} \pm 0.004\text{ s}$ across 50 full cycles.
* Period on Pivot 2: $T_2 = \mathbf{1.7602\text{ s}} \pm 0.003\text{ s}$ across 54 full cycles.
* Gyroscope drift was virtually zero ($\approx -0.07^\circ/\text{s}$).
* Damping factor $Q \approx 350$.

The sensor, firmware, and signal processing worked **flawlessly**.

---

### The Root Cause of the $13.2\text{--}13.9$ Value

The error came down to **one single input parameter: Length $L$**:

1. In the software setup screen, the knife-edge distance $L$ was left as the default **$L = 1.000\text{ m}$**.
2. The formula for a simple pendulum is:
   $$g = \frac{4\pi^2 L}{T^2}$$
3. When the software took our measured period $T_{\text{avg}} = 1.729\text{ s}$ and plugged in the default $L = 1.000\text{ m}$:
   $$g = \frac{4\pi^2 \times 1.000}{(1.729)^2} = \frac{39.4784}{2.9899} = \mathbf{13.20\text{ m/s}^2}$$
   And for Pivot 1 alone ($T_1 = 1.684\text{ s}$):
   $$g = \frac{4\pi^2 \times 1.000}{(1.684)^2} = \mathbf{13.92\text{ m/s}^2}$$

#### The Physical Reality:
On Earth ($g = 9.807\text{ m/s}^2$), a pendulum oscillating at $T = 1.729\text{ seconds}$ physically has an equivalent length of:
$$L_{\text{actual}} = \frac{g T^2}{4\pi^2} = \frac{9.807 \times (1.729)^2}{39.4784} = \mathbf{0.743\text{ m} = 74.3\text{ cm}}$$

**Conclusion:** The knife edges on our physical rod were clamped $\approx \mathbf{74\text{ cm}}$ apart, but the software was told $L = \mathbf{100\text{ cm}}$ ($1.000\text{ m}$). This 35% length mismatch directly multiplied $g$ by $1.35$, turning $9.81$ into $13.3\text{ m/s}^2$!

---

## 2. Clarifying the Physical Measurements (Zero Confusion)

### What is the "Knife Edge"?
In the lab, the pendulum rod has two clamping collars with triangular steel wedges sticking out. 
* The **Knife Edge** is **NOT** the clamping block or the tightening screw.
* The **Knife Edge** is the **sharp apex / sharp blade line** of the triangular wedge that physically rests on the agate bearing plate of the wall suspension bracket.
* **That sharp contact line is the axis of rotation.** All measurements must be taken from that line!

```
                    [ Wall Suspension Bracket ]
                    ═══════════════════════════
                                ▲
                                │  <── PIVOT POINT (Sharp apex of triangular blade)
                             ┌─────┐       ALL MEASUREMENTS START HERE!
                             │  ▲  │
                             │ / \ │  <── Triangular steel wedge
   ┌─────────────────────────┴─────┴─────────────────────────┐
   │                  Clamping Bracket / Collar              │
   │                                                         │
   │  ═════════════════════════════════════════════════════  │
   │                     Metal Pendulum Rod                  │
   │  ═════════════════════════════════════════════════════  │
   │                         [ Screw ]                       │
   └─────────────────────────────────────────────────────────┘
```

---

### The Three Required Lengths: $L$, $h_1$, and $h_2$

```
                   [Knife Edge 1]                                 [Knife Edge 2]
                     (Pivot 1)                                      (Pivot 2)
                         │                                              │
                         ├───────────── h1 ─────────────►◄───── h2 ─────┤
                         │                               │              │
═════════════════════════╪═══════════════════════════════▲══════════════╪════════════════════════
(Rod top end)            │                           [Balance]          │          (Rod bottom end)
                         │                         (Pencil line)        │
                         │                                              │
                         ├────────────────────── L ─────────────────────┤
```

| Parameter | What it is | Where to measure from | What to avoid |
| :--- | :--- | :--- | :--- |
| **$L$** | **Knife-Edge Distance** | From the **sharp line of Knife Edge 1** directly to the **sharp line of Knife Edge 2**. | **DO NOT** measure from the outer ends of the metal rod! The rod overhang does not count. |
| **$h_1$** | **Distance to CM from Pivot 1** | From the **sharp line of Knife Edge 1** to the **pencil balance line** (Center of Mass). | |
| **$h_2$** | **Distance to CM from Pivot 2** | From the **sharp line of Knife Edge 2** to the **pencil balance line** (Center of Mass). | |

> **The Golden Check:** $h_1 + h_2$ **MUST** equal $L$!  
> If $L = 100\text{ cm}$, and you measure $h_1 = 43\text{ cm}$, then $h_2$ **must** be $57\text{ cm}$ ($43 + 57 = 100$).  
> *(Last time, $h_1 = 43$ and $h_2 = 78$ added up to $121\text{ cm}$, which meant the measurements were taken from the ends of the $120\text{ cm}$ metal rod rather than the knife edges).*

---

## 3. How to Set Up the Physical Apparatus Tomorrow

### Option A (Recommended): Set $L = 1.000\text{ m}$ ($100.0\text{ cm}$)
If your lab manual specifies a 1-meter knife-edge distance:
1. Clamp **Knife Edge 1** about $10\text{ cm}$ from the top end of the rod.
2. Use a steel meter tape to place **Knife Edge 2** exactly **$100.0\text{ cm}$ ($1.000\text{ m}$)** away from Knife Edge 1 (measuring sharp apex to sharp apex). Tighten both knife edges firmly.
3. Clamp the **Heavy Weight** about $8\text{--}10\text{ cm}$ below Knife Edge 1.
4. Clamp the **Light Weight (Tuning Bob)** about $25\text{--}30\text{ cm}$ above Knife Edge 2.
5. Tape the **MPU-6050** flat against the rod near the middle.
6. **Balance the rod:** Place the fully assembled rod horizontally across a pencil on your desk. Find where it balances like a seesaw. Mark that line with a pencil.
7. Measure $h_1$ (Knife 1 to line) and $h_2$ (Knife 2 to line). Check that $h_1 + h_2 = 1.000\text{ m}$.
8. **In the software:** Enter $L = 1.000$, and enter $(h_1 - h_2)$ (e.g. `0.100`).
9. **Expected period:** Will be right around **$\approx 2.00\text{ seconds}$**!

---

### Option B: Keep Existing Knife-Edge Spacing
If the knife edges are already fixed on the rod and you don't want to move them:
1. **Carefully measure the exact distance $L$ between the two sharp knife-edge blades.**  
   *(It will likely be around $73.5\text{ cm} = 0.735\text{ m}$ or similar).*
2. Balance the rod on a pencil to find the balance line (CM).
3. Measure $h_1$ (Knife 1 to balance line) and $h_2$ (Knife 2 to balance line).
4. **In the software:** Type your **actual measured $L$** (e.g. `0.735`) into the Knife-edge distance box! Do NOT leave it as `1.0`.
5. **Expected period:** Around **$\approx 1.72\text{ seconds}$**, and $g$ will compute to **$9.81\text{ m/s}^2$**!

---

### Tuning the Two Periods ($T_1 \approx T_2$)
* Hang on Knife Edge 1 $\implies$ deflect $5^\circ$ $\implies$ watch period $T_1$ on screen.
* Invert and hang on Knife Edge 2 $\implies$ deflect $5^\circ$ $\implies$ watch period $T_2$ on screen.
* If $T_1$ and $T_2$ are within **$0.05\text{ s}$** of each other, you are ready to record!
* If they differ by more than $0.1\text{ s}$, slide the **Light Weight** $1\text{--}2\text{ cm}$ up or down and re-check.

---

## 4. How to Run the Software (One-Click Launch)

No commands, no terminals, no scripts to type!

### How to Start:
1. Plug the ESP8266 NodeMCU into the PC via USB.
2. In the project folder `physicsproject`, **double-click `run.bat`**.
   * It automatically checks Python.
   * It automatically installs any missing dependencies.
   * It opens the Kater's Pendulum GUI window immediately.

---

### In-App Step-by-Step Procedure:

#### Screen 0: Setup Page
1. Select the **COM Port** (usually `COM13` or click Refresh to see which port appears).
2. Enter your measured values:
   * **Knife-edge distance $L$ (m):** (e.g. `1.000` or `0.735`)
   * **Distance diff $(h_1 - h_2)$ (m):** (e.g. `0.100`)
   * **Accepted $g$ (m/s²):** `9.80665`
3. Click **Connect to Hardware**. The status will turn green: `Connected ✅`.
4. Click **Proceed to Pivot 1 Trial ▶**.

#### Screen 1: Pivot 1 Trial
1. Hang pendulum on **Knife Edge 1**. Let it hang completely stationary.
2. Click **📐 Calibrate Zero**. Wait 3 seconds until status turns green: `Status: Calibrated ✅`.
3. Deflect the pendulum gently by $\approx 5^\circ$ and release.
4. Click **▶ Start Recording**.
5. Let it swing for **25 to 30 oscillations** (about 50 seconds).
   *(Optional: If your lab has a photogate timer, note down its reading. If timing with a phone stopwatch, count 25 swings and note the total time).*
6. Click **⏹ Stop Recording**.
7. Enter stopwatch time (if you timed it), then click **✅ Accept & Continue**.

#### Screen 2: Pivot 2 Trial
1. Unhook the pendulum, **invert it upside-down**, and hang it on **Knife Edge 2**.
2. Let it hang completely stationary.
3. Click **📐 Calibrate Zero**. Wait 3 seconds until status turns green: `Status: Calibrated ✅`.
4. Deflect gently by $\approx 5^\circ$ and release.
5. Click **▶ Start Recording**.
6. Let it swing for **25 to 30 oscillations**.
7. Click **⏹ Stop Recording**.
8. Click **✅ Accept & Continue**.

#### Screen 3: Results Dashboard
1. The table will immediately display:
   * Period $T_1$ and $T_2$ (raw $\pm$ std dev).
   * Amplitude-corrected periods $T_{1,0}$ and $T_{2,0}$.
   * Calculated $g$ and percentage error vs accepted $9.80665\text{ m/s}^2$.
   * Amplitude decay curve, Quality factor $Q$, and damping constant $\gamma$.
2. Click **💾 Export Raw CSV Data** and **📋 Export Session Summary JSON**.
   * All files are saved into `python/data/` for the final report.

---

## 5. Quick Hardware Troubleshooting Checklist

| Issue | Quick Fix |
| :--- | :--- |
| **PermissionError (Code 31 / 13) on COM port** | The CH340 driver rolled back. Open Device Manager $\to$ Ports $\to$ USB-SERIAL CH340 $\to$ Update Driver $\to$ Browse my computer $\to$ Let me pick $\to$ choose driver version **3.4.2014.8** (not 3.9.2024). |
| **"Access is denied" on COM port** | Another program (like Arduino IDE Serial Monitor or a second Python terminal) is holding the port. Close all other windows and relaunch `run.bat`. |
| **MPU wires affecting swing** | Ensure the 4 wires coming off the MPU are taped along the rod, with a **loose, relaxed loop of wire** at the top pivot so they do not exert spring torque on the knife edge. |
| **Pendulum wobble / out-of-plane swinging** | Release the pendulum cleanly using a thread or pencil rather than your fingers to avoid twisting the rod. |
