"""Generate a publication-grade PDF from docs/LAB_NOTEBOOK_REPORT.md using MathJax and Microsoft Edge headless."""

import os
import re
import subprocess
import time
import shutil
import markdown

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
INPUT_MD = os.path.join(PROJECT_DIR, "docs", "LAB_NOTEBOOK_REPORT.md")
HTML_OUT = os.path.join(PROJECT_DIR, "docs", "notebook_render.html")
PDF_OUT = os.path.join(PROJECT_DIR, "docs", "LAB_NOTEBOOK_REPORT.pdf")
DESKTOP_PDF = r"C:\Users\manee\Desktop\LAB_NOTEBOOK_REPORT.pdf"

# Read markdown
with open(INPUT_MD, "r", encoding="utf-8") as f:
    raw_md = f.read()

# 1. Protect math expressions from Markdown parser
math_blocks = []
math_inlines = []

def save_math_block(match):
    idx = len(math_blocks)
    math_blocks.append(match.group(0))
    return f"@@MATH_BLOCK_{idx}@@"

def save_math_inline(match):
    idx = len(math_inlines)
    math_inlines.append(match.group(0))
    return f"@@MATH_INLINE_{idx}@@"

# Display math $$...$$
protected_md = re.sub(r"\$\$(.*?)\$\$", save_math_block, raw_md, flags=re.DOTALL)
# Display math \[...\]
protected_md = re.sub(r"\\\[(.*?)\\\]", save_math_block, protected_md, flags=re.DOTALL)
# Inline math \(...\)
protected_md = re.sub(r"\\\((.*?)\\\)", save_math_inline, protected_md)
# Inline math $...$
protected_md = re.sub(r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)", save_math_inline, protected_md)

# 2. Convert markdown to HTML
html_body = markdown.markdown(
    protected_md,
    extensions=['tables', 'fenced_code', 'def_list', 'attr_list']
)

# 3. Restore math expressions
for idx, m in enumerate(math_blocks):
    html_body = html_body.replace(f"@@MATH_BLOCK_{idx}@@", m)
for idx, m in enumerate(math_inlines):
    html_body = html_body.replace(f"@@MATH_INLINE_{idx}@@", m)

# 4. Wrap in high-quality academic notebook CSS template
notebook_css = """
@page {
    size: A4 portrait;
    margin: 15mm 15mm 16mm 15mm;
    @bottom-right {
        content: "Page " counter(page);
        font-family: 'Times New Roman', Times, serif;
        font-size: 9pt;
    }
    @bottom-left {
        content: "Physics Practical Record — Kater's Reversible Compound Pendulum";
        font-family: 'Times New Roman', Times, serif;
        font-size: 8.5pt;
        color: #555;
    }
}

body {
    font-family: 'Times New Roman', 'Nimbus Roman No9 L', Times, serif;
    font-size: 10pt;
    line-height: 1.4;
    color: #111;
    background: #fff;
    margin: 0;
    padding: 0;
}

h1 {
    font-size: 13.5pt;
    font-weight: bold;
    margin-top: 1mm;
    margin-bottom: 2mm;
    border-bottom: 1.2pt solid #222;
    padding-bottom: 1mm;
}

h2 {
    font-size: 12pt;
    font-weight: bold;
    text-align: center;
    margin-top: 2.5mm;
    margin-bottom: 2.5mm;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

h3 {
    font-size: 11pt;
    font-weight: bold;
    margin-top: 3.5mm;
    margin-bottom: 1.5mm;
    border-bottom: 0.8pt solid #444;
    padding-bottom: 0.5mm;
    page-break-after: avoid;
}

h4 {
    font-size: 10pt;
    font-weight: bold;
    margin-top: 3mm;
    margin-bottom: 1mm;
    page-break-after: avoid;
}

p {
    margin-top: 1mm;
    margin-bottom: 1.5mm;
    text-align: justify;
}

ul, ol {
    margin-top: 1mm;
    margin-bottom: 2mm;
    padding-left: 5mm;
}

li {
    margin-bottom: 0.8mm;
}

hr {
    border: none;
    border-top: 0.5pt solid #bbb;
    margin: 2.5mm 0;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 2mm;
    margin-bottom: 3mm;
    font-size: 9pt;
    page-break-inside: avoid;
}

th, td {
    border: 0.6pt solid #333;
    padding: 1.5mm 2mm;
    text-align: left;
}

th {
    background-color: #f2f2f2;
    font-weight: bold;
    text-align: center;
}

/* Code blocks (Diagrams) */
pre {
    background-color: #f8f8f8;
    border: 0.6pt solid #ccc;
    border-radius: 3px;
    padding: 2mm 3mm;
    font-family: 'Courier New', Courier, monospace;
    font-size: 8pt;
    line-height: 1.2;
    overflow-x: auto;
    page-break-inside: avoid;
    margin: 2.5mm 0;
}

/* Figures */
figure {
    margin: 3mm 0;
    text-align: center;
    page-break-inside: avoid;
}

figure img {
    max-width: 90%;
    max-height: 250px;
    height: auto;
    border: 0.5pt solid #ddd;
    border-radius: 2px;
}

figcaption {
    font-size: 8pt;
    color: #333;
    margin-top: 1mm;
    line-height: 1.3;
    text-align: justify;
    padding: 0 3mm;
}

/* Math */
.MathJax_Display, .MathJax {
    font-size: 102% !important;
}

mjx-container[display="true"] {
    margin: 1.5mm 0 !important;
}
"""

html_full = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Physics Laboratory Practical Report — Kater's Pendulum</title>
<style>
{notebook_css}
</style>
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
    processEscapes: true
  }},
  options: {{
    renderActions: {{
      addMenu: []
    }}
  }},
  startup: {{
    pageReady: () => {{
      return MathJax.startup.defaultPageReady().then(() => {{
        document.body.classList.add('mathjax-ready');
      }});
    }}
  }}
}};
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
{html_body}
</body>
</html>
"""

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(html_full)
print(f"[OK] Wrote rendered HTML to {HTML_OUT}")

# 5. Run Microsoft Edge headless to print to PDF
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge_path):
    edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

print(f"[..] Rendering PDF using Microsoft Edge ({edge_path})...")

file_url = "file:///" + HTML_OUT.replace("\\", "/")

cmd = [
    edge_path,
    "--headless=new",
    "--disable-gpu",
    "--allow-file-access-from-files",
    "--no-pdf-header-footer",
    "--virtual-time-budget=7000",
    f"--print-to-pdf={PDF_OUT}",
    file_url
]

subprocess.run(cmd, check=True)

if os.path.exists(PDF_OUT):
    size_kb = os.path.getsize(PDF_OUT) / 1024.0
    shutil.copy2(PDF_OUT, DESKTOP_PDF)
    print(f"[SUCCESS] PDF generated and copied successfully!")
    print(f"Local Path: {PDF_OUT}")
    print(f"Desktop Path: {DESKTOP_PDF}")
    print(f"Size: {size_kb:.1f} KB")
else:
    print("[ERROR] PDF generation failed.")
