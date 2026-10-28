"""Assemble all 3 Kater's Pendulum experimental graphs onto a single A4 printable page with scissors cut guidelines."""

import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Rectangle
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
FIG_DIR = os.path.join(PROJECT_DIR, "docs", "figures")

PDF_OUT = os.path.join(PROJECT_DIR, "docs", "Katers_Pendulum_Lab_Graphs_Printable_A4.pdf")
PNG_OUT = os.path.join(PROJECT_DIR, "docs", "Katers_Pendulum_Lab_Graphs_Printable_A4.png")
DESKTOP_PDF = r"C:\Users\manee\Desktop\Katers_Pendulum_Lab_Graphs_Printable_A4.pdf"
DESKTOP_PNG = r"C:\Users\manee\Desktop\Katers_Pendulum_Lab_Graphs_Printable_A4.png"

# A4 dimensions in inches: 8.27 x 11.69 inches
A4_WIDTH = 8.27
A4_HEIGHT = 11.69

# Load images
img1_path = os.path.join(FIG_DIR, "fig1_waveforms.png")
img2_path = os.path.join(FIG_DIR, "fig3_decay_fits.png")
img3_path = os.path.join(FIG_DIR, "fig4_phase_space_and_bessel_sensitivity.png")

img1 = mpimg.imread(img1_path)
img2 = mpimg.imread(img2_path)
img3 = mpimg.imread(img3_path)

fig = plt.figure(figsize=(A4_WIDTH, A4_HEIGHT), dpi=300)

# Main Title at the very top
plt.figtext(
    0.5, 0.975,
    "KATER'S REVERSIBLE PENDULUM — EXPERIMENTAL TELEMETRY GRAPHS",
    fontsize=11.5, fontweight='bold', fontfamily='serif', ha='center', va='top'
)
plt.figtext(
    0.5, 0.960,
    "Instructions: Print this sheet on A4 paper at 100% scale. Cut along dashed guidelines and paste into your lab record book.",
    fontsize=8, fontstyle='italic', fontfamily='serif', ha='center', va='top', color='#444'
)

# Coordinates in figure fraction [left, bottom, width, height]
# Usable vertical space: bottom 0.03 to top 0.94 -> span = 0.91
# 3 boxes, each height ~ 0.285, gap ~ 0.018

boxes = [
    {
        "title": "GRAPH 1: Angular Velocity Waveforms & Sub-Sample Zero-Crossing Detection",
        "caption": "Figure 1: Real-time angular velocity ω_z(t) at 100 Hz for Pivot 1 (T₁ ≈ 1.69 s) and Pivot 2 (T₂ ≈ 1.77 s). Red markers show linear-interpolated zero-crossings (turning points) that eliminate human reaction latency.",
        "img": img1,
        "box_y": 0.655,
        "box_h": 0.292,
        "img_y": 0.690,
        "img_h": 0.222
    },
    {
        "title": "GRAPH 2: Peak Amplitude Exponential Decay Envelopes & Quality Factor (Q)",
        "caption": "Figure 2: Peak amplitude decay fits θ(n) = θ₀ e^(-γ n) evaluating system damping. Pivot 1 quality factor Q₁ = 681.1 (decay γ₁ = 0.00460) and Pivot 2 quality factor Q₂ = 601.2 (decay γ₂ = 0.00534).",
        "img": img2,
        "box_y": 0.345,
        "box_h": 0.292,
        "img_y": 0.380,
        "img_h": 0.222
    },
    {
        "title": "GRAPH 3: Phase-Space Orbit (ω vs. θ) & Bessel Sensitivity Error Attenuation",
        "caption": "Figure 3: (a) Dissipative spiral phase-space trajectory ω_z(θ) confirming low-friction planar motion. (b) Bessel error suppression surface demonstrating a 4× attenuation of center-of-mass balance uncertainty.",
        "img": img3,
        "box_y": 0.035,
        "box_h": 0.292,
        "img_y": 0.070,
        "img_h": 0.222
    }
]

margin_x = 0.05
box_w = 0.90

for b in boxes:
    # 1. Draw dashed cut box
    rect = Rectangle(
        (margin_x, b["box_y"]), box_w, b["box_h"],
        transform=fig.transFigure,
        fill=True, facecolor='#fafafa',
        edgecolor='#666666', linestyle='--', linewidth=0.9
    )
    fig.patches.append(rect)
    
    # Scissors label on top edge
    plt.figtext(
        margin_x + 0.02, b["box_y"] + b["box_h"] - 0.003,
        "- - - - - - - - - - - - - - - - - - - - - - - - - [ CUT HERE ] - - - - - - - - - - - - - - - - - - - - - - - - -",
        fontsize=6.5, fontfamily='sans-serif', color='#777', va='center'
    )
    
    # Title inside box
    plt.figtext(
        margin_x + box_w / 2.0, b["box_y"] + b["box_h"] - 0.015,
        b["title"],
        fontsize=9, fontweight='bold', fontfamily='serif', ha='center', va='top', color='#111'
    )
    
    # Image Axes
    ax = fig.add_axes([margin_x + 0.02, b["img_y"], box_w - 0.04, b["img_h"]])
    ax.imshow(b["img"])
    ax.axis('off')
    
    # Caption inside box below image
    plt.figtext(
        margin_x + box_w / 2.0, b["box_y"] + 0.012,
        b["caption"],
        fontsize=7.2, fontstyle='italic', fontfamily='serif', ha='center', va='bottom', color='#222',
        wrap=True
    )

# Save PDF & PNG
plt.savefig(PDF_OUT, format='pdf', dpi=300)
plt.savefig(PNG_OUT, format='png', dpi=300)
plt.close()

import shutil
shutil.copy2(PDF_OUT, DESKTOP_PDF)
shutil.copy2(PNG_OUT, DESKTOP_PNG)

print("[SUCCESS] Printable A4 sheet generated successfully!")
print(f"Desktop PDF: {DESKTOP_PDF}")
print(f"Desktop PNG: {DESKTOP_PNG}")
