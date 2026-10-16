# Kater's Pendulum Lab — Complete Teammate Hand-Off Guide & Physics Solution

> **For Tomorrow's Lab Session**  
> Read this document before entering the lab. It explains why our previous runs displayed $g \approx 13.2\text{--}13.9\text{ m/s}^2$ on screen, proves step-by-step how our sensor data already gives **$g = 9.8099\text{ m/s}^2$** ($0.03\%$ error), provides zero-doubt diagrams for measuring $L$, $h_1$, and $h_2$, and details the one-click launch procedure.

---

## 1. Why Did the Previous Run Display $g \approx 13.2\text{--}13.9\text{ m/s}^2$? (Mystery Solved)

### The Good News
Our hardware telemetry was **phenomenally clean**:
* Waveforms recorded from the MPU-6050 are smooth, symmetrical textbook damped sine waves.
* Period on Pivot 1: $T_1 = \mathbf{1.69116\text{ s}}$ across 50 full cycles (Borda amplitude-corrected: $T_{1,0} = \mathbf{1.69047\text{ s}}$).
* Period on Pivot 2: $T_2 = \mathbf{1.77580\text{ s}}$ across 50 full cycles (Borda amplitude-corrected: $T_{2,0} = \mathbf{1.77320\text{ s}}$).
* Gyroscope drift was virtually zero ($\approx -0.07^\circ/\text{s}$).

### Step-by-Step Plain-English Explanation

#### Step 1: The Ideal Pendulum Formula vs. Bessel's Formula
In an ideal textbook Kater's pendulum, the movable weights are adjusted until the two periods are **strictly equal** ($T_1 = T_2$). When $T_1 = T_2 = T$, gravity is calculated using the simple formula:
$$g = \frac{4\pi^2 L}{T^2}$$

However, in real-world experiments, $T_1$ and $T_2$ are rarely 100% identical without hours of fine micro-adjustments. When $T_1 \neq T_2$, you **cannot** use the simple formula! If you take an average period $T_{\text{avg}} = \frac{1.690 + 1.773}{2} = 1.732\text{ s}$ and plug it into the simple formula:
$$g = \frac{4\pi^2 \times 1.000}{(1.732)^2} = \frac{39.4784}{2.999} = \mathbf{13.16\text{ m/s}^2}$$
And for Pivot 1 alone ($T_1 = 1.690\text{ s}$):
$$g = \frac{4\pi^2 \times 1.000}{(1.690)^2} = \frac{39.4784}{2.858} = \mathbf{13.81\text{ m/s}^2}$$
That is **exactly** the $\approx 13.2\text{--}13.9\text{ m/s}^2$ number that was seen on screen!

#### Step 2: What Bessel's Formula Does
To eliminate the need for hours of trial-and-error balancing, mathematician Friedrich Bessel proved the exact formula for a compound pendulum with unequal periods:
$$g = \frac{8\pi^2}{\dfrac{T_1^2 + T_2^2}{L} + \dfrac{T_1^2 - T_2^2}{h_1 - h_2}}$$

Where:
* $L$ is the distance between the two knife edges ($1.000\text{ m}$).
* $h_1$ is the distance from Knife Edge 1 to the Center of Mass (balance point) ($0.430\text{ m}$).
* $h_2$ is the distance from Knife Edge 2 to the Center of Mass ($0.570\text{ m}$).
* $(h_1 - h_2)$ is the asymmetry term ($0.43 - 0.57 = \mathbf{-0.140\text{ m}}$).

#### Step 3: Plugging Our Exact CSV Data into Bessel's Formula
Let's calculate it by hand using the actual recorded numbers:
1. $T_1^2 = (1.69047)^2 = 2.85769\text{ s}^2$
2. $T_2^2 = (1.77320)^2 = 3.14424\text{ s}^2$
3. First term in denominator:
   $$\frac{T_1^2 + T_2^2}{L} = \frac{2.85769 + 3.14424}{1.000} = 6.00193$$
4. Second term in denominator:
   $$\frac{T_1^2 - T_2^2}{h_1 - h_2} = \frac{2.85769 - 3.14424}{-0.140} = \frac{-0.28655}{-0.140} = \mathbf{+2.04679}$$
   *(Notice: negative divided by negative gives a **positive** number!)*
5. Total denominator:
   $$\text{Denominator} = 6.00193 + 2.04679 = \mathbf{8.04872}$$
6. Numerator:
   $$8\pi^2 = 8 \times 9.8696044 = \mathbf{78.95684}$$
7. Final $g$:
   $$g = \frac{78.95684}{8.04872} = \mathbf{9.80988\text{ m/s}^2}!$$

| Standard Accepted $g$ | Our Calculated $g$ | Percentage Error |
| :---: | :---: | :---: |
| **$9.80665\text{ m/s}^2$** | **$9.80988\text{ m/s}^2$** | **$+0.033\%$ (Less than $1/30^{\text{th}}$ of $1\%$)** |

**Conclusion:** The physical setup and the sensor readings were already **extraordinarily accurate**!

#### Step 4: Why Did the Screen Display 13.9 Instead of 9.81?
There was a software parameter timing bug:
1. The app previously only captured setup inputs the moment the user clicked **"Connect"**.
2. When anyone sets up the experiment, they naturally click "Connect" first (while $(h_1 - h_2)$ was still at its default `0.0` / None).
3. Then the user typed $(h_1 - h_2)$ into the box and clicked "Next".
4. Because the old code did not re-read parameters upon clicking "Next", $(h_1 - h_2)$ remained `None`.
5. When $(h_1 - h_2)$ is `None`, the software automatically fell back to the simple pendulum formula, outputting $13.16\text{--}13.9\text{ m/s}^2$!

### The Software Upgrades Applied
The code has been updated and verified:
1. **Guaranteed Parameter Capture:** Parameters are now re-read the moment you click "Next -> Begin Pivot 1 Trial".
2. **Dedicated $h_1$ and $h_2$ Inputs:** You can now enter $h_1$ (e.g. `0.4300`) and $h_2$ (e.g. `0.5700`) directly. The app calculates $(h_1 - h_2) = -0.1400\text{ m}$ automatically.
3. **Live Measurement Verification Badge:** Shows a green badge (`✅ h1 + h2 = 1.0000 m (matches L)`) or warns you if $h_1 + h_2 \neq L$.
4. **Live Recalculation on Results Screen:** If you ever reach the Results Screen and want to tweak $L$ or $(h_1 - h_2)$ without redoing the swings, there is a **"⟳ Recalculate g"** button right there.

---

## 2. Physical Measurement Guide (Zero Confusion)

### What is the "Knife Edge"?
In the lab, the pendulum rod has two clamping collars with triangular steel wedges sticking out. 
* The **Knife Edge** is **NOT** the clamping block, NOT the tightening screw, and NOT the rod end.
* The **Knife Edge** is the **sharp blade line / apex** of the triangular wedge that physically rests on the agate bearing plate of the wall suspension bracket.
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
(Rod top end)            │                         [Balance Line]       │          (Rod bottom end)
                         │                          (Pencil mark)       │
                         │                                              │
                         ├────────────────────── L ─────────────────────┤
```

| Parameter | What it is | Where to measure from | What to avoid |
| :--- | :--- | :--- | :--- |
| **$L$** | **Knife-Edge Distance** | From the **sharp apex line of Knife Edge 1** directly to the **sharp apex line of Knife Edge 2**. Typically $1.000\text{ m}$ ($100.0\text{ cm}$). | **DO NOT** measure from outer rod tips! |
| **$h_1$** | **Pivot 1 to Center of Mass** | From the **sharp line of Knife Edge 1** to the **pencil balance line**. Typically $\approx 0.430\text{ m}$ ($43.0\text{ cm}$). | |
| **$h_2$** | **Pivot 2 to Center of Mass** | From the **sharp line of Knife Edge 2** to the **pencil balance line**. Typically $\approx 0.570\text{ m}$ ($57.0\text{ cm}$). | |
| **$h_1 - h_2$** | **Bessel Asymmetry** | $h_1 - h_2 = 0.430 - 0.570 = \mathbf{-0.140\text{ m}}$. *(Must be **negative** because Knife Edge 1 is closer to the Heavy Weight and Center of Mass).* | |

> **The Golden Check:** $h_1 + h_2$ **MUST** equal $L$!  
> If $L = 100\text{ cm}$, and you measure $h_1 = 43\text{ cm}$, then $h_2$ **must** be $57\text{ cm}$ ($43 + 57 = 100$).  
> *(Last time, $h_1 = 43$ and $h_2 = 78$ added up to $121\text{ cm}$, which meant $h_2$ was accidentally measured to the end of the $120\text{ cm}$ metal rod instead of Knife Edge 2).*

---

### How to Find the Center of Mass (30 Seconds)
1. Assemble the rod completely with both knife edges, the heavy cylinder, the light bob, and the MPU-6050 taped on.
2. Place the rod horizontally across a triangular wooden block or a round pencil on the lab table.
3. Slide the rod back and forth until it balances perfectly like a seesaw.
4. Draw a sharp pencil line across the rod right above the pencil. **That is your Center of Mass.**
5. Measure $h_1$ and $h_2$ from each knife edge blade to that line using a meter scale.

---

## 3. Step-by-Step Procedure for Tomorrow's Run

### Step 1: Launch the Software (One Click)
* Plug the ESP8266 NodeMCU into the PC via USB.
* In the project folder `physicsproject`, **double-click `run.bat`** (or `dist\KatersPendulum\KatersPendulum.exe`).
* The application window opens immediately.

---

### Step 2: Screen 1 — Setup Page
1. **COM Port:** Select your port (usually `COM13` or the available CH340 port) and click **"Connect"**.
2. **Experiment Geometry & Parameters:**
   * **Knife-edge distance ($L$):** Set to `1.0000 m` (or measure your exact blade-to-blade spacing).
   * **$h_1$ (Pivot 1 to CoM):** Set to `0.4300 m` (or your measured value).
   * **$h_2$ (Pivot 2 to CoM):** Set to `0.5700 m` (or your measured value).
   * Look at the green confirmation badge:  
     `✅ h1 + h2 = 1.0000 m (matches L). Bessel asymmetry = -0.1400 m`
3. Click **"Next -> Begin Pivot 1 Trial"**.

---

### Step 3: Screen 2 — Pivot 1 Trial
1. Hang the pendulum on **Knife Edge 1** (heavy cylinder near the top pivot).
2. Ensure the pendulum is hanging completely still.
3. Click **"Calibrate Zero"** (takes $\approx 3$ seconds). Status turns green: *"Calibrated & Ready"*.
4. Gently deflect the pendulum by about **$4^\circ\text{--}5^\circ$** and release it cleanly without twisting or wobbling.
5. Click **"▶ Start Trial"**.
6. The screen plots the live sine wave and counts oscillations in real time.
7. *(Optional)* Use a stopwatch to time 50 oscillations and enter it into the stopwatch box.
8. Once 40–50 swings are recorded, click **"⏹ Finish Trial & Proceed to Pivot 2"**.

---

### Step 4: Screen 3 — Pivot 2 Trial
1. Carefully lift the pendulum off the wall bracket, **invert it**, and hang it on **Knife Edge 2** (heavy cylinder is now near the bottom).
2. Keep the pendulum completely still.
3. Click **"Calibrate Zero"**.
4. Deflect the pendulum by **$4^\circ\text{--}5^\circ$** and release cleanly.
5. Click **"▶ Start Trial"**.
6. Let it record 40–50 oscillations.
7. Click **"⏹ Finish Trial & View Results"**.

---

### Step 5: Screen 4 — Results & Exports
1. The dashboard immediately displays the side-by-side comparison table:
   * **$T_1$** ($\approx 1.69\text{ s}$)
   * **$T_2$** ($\approx 1.77\text{ s}$)
   * **Borda amplitude-corrected periods**
   * **Calculated $g$**: $\approx \mathbf{9.81\text{ m/s}^2}$
   * **Error %**: $\approx \mathbf{0.03\%}$
   * **Formula**: `Bessel's formula (h1 - h2 = -0.1400 m)`
2. **If you ever need to adjust parameters:**
   Use the **"Geometry Parameters & Live Recalculation"** bar right above the decay plot:
   Type your new $L$ or $(h_1 - h_2)$ and click **"⟳ Recalculate g"** — the table updates instantly!
3. Click **"💾 Export Raw CSV Data"** to save the full raw waveform CSV.
4. Click **"📋 Export Session Summary JSON"** to save the final report.

---

## 4. Quick Troubleshooting Cheat Sheet

| Problem | Cause | Quick Fix |
| :--- | :--- | :--- |
| Status says *Connection failed* | Wrong COM port or USB cable unplugged | Click *Refresh Ports*, select the CH340 COM port, click *Connect*. |
| Amber warning badge on Setup screen: *h1 + h2 != L* | Distances measured from rod ends instead of knife edges | Measure strictly from the sharp blade line of Knife Edge 1 and Knife Edge 2 to the pencil balance line. |
| Calculated $g$ is showing $\approx 19.9\text{ m/s}^2$ | Sign of $(h_1 - h_2)$ was entered as positive `+0.14` | Change it to **`-0.1400`** in the recalculate box and click *Recalculate g*. $(h_1 - h_2)$ must be negative because Pivot 1 is closer to the heavy bob. |
| Calculated $g$ is showing $\approx 13.2\text{ m/s}^2$ | $(h_1 - h_2)$ was left at `0.0` (ideal formula fallback) | Enter **`-0.1400`** in the recalculate box and click *Recalculate g*. |
