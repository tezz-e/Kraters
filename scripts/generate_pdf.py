"""Generate a publication-grade PDF from docs/RESEARCH_REPORT.md using MathJax and Microsoft Edge headless."""

import os
import re
import subprocess
import time
import markdown

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
INPUT_MD = os.path.join(PROJECT_DIR, "docs", "RESEARCH_REPORT.md")
HTML_OUT = os.path.join(PROJECT_DIR, "docs", "report_render.html")
PDF_OUT = os.path.join(PROJECT_DIR, "docs", "Katers_Pendulum_Research_Report.pdf")

# Read markdown
with open(INPUT_MD, "r", encoding="utf-8") as f:
    raw_md = f.read()

# 1. Protect math expressions from Markdown parser (prevent underscores from becoming <em>)
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
# Inline math $...$ (not preceded or followed by $)
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

# 4. Wrap in high-quality academic journal CSS template
academic_css = """
@page {
    size: A4 portrait;
    margin: 20mm 18mm 22mm 18mm;
    @bottom-right {
        content: counter(page);
        font-family: 'Times New Roman', Times, serif;
        font-size: 10pt;
    }
    @bottom-left {
        content: "Physics Laboratory Research Group — Kater's Reversible Pendulum Gravimetry";
        font-family: 'Times New Roman', Times, serif;
        font-size: 8.5pt;
        color: #555;
    }
}

body {
    font-family: 'Times New Roman', 'Nimbus Roman No9 L', Times, serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: #111;
    background: #fff;
    text-align: justify;
    margin: 0;
    padding: 0;
}

h1:first-of-type {
    font-size: 18pt;
    font-weight: bold;
    text-align: center;
    line-height: 1.3;
    margin-top: 5mm;
    margin-bottom: 3mm;
}

/* Author block */
p:has(strong:first-child) {
    text-align: center;
}

h2 {
    font-size: 13pt;
    font-weight: bold;
    border-bottom: 1pt solid #222;
    padding-bottom: 1.5mm;
    margin-top: 6mm;
    margin-bottom: 3mm;
    page-break-after: avoid;
}

h3 {
    font-size: 11pt;
    font-weight: bold;
    font-style: italic;
    margin-top: 4mm;
    margin-bottom: 2mm;
    page-break-after: avoid;
}

h4 {
    font-size: 10.5pt;
    font-weight: bold;
    margin-top: 3mm;
    margin-bottom: 1.5mm;
    page-break-after: avoid;
}

/* Abstract block */
blockquote, .abstract {
    margin: 4mm 8mm;
    font-size: 9.5pt;
    line-height: 1.45;
    font-style: italic;
    background: #fdfdfd;
    border-left: 2pt solid #666;
    padding: 2mm 4mm;
}

/* Tables in academic booktabs style */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 4mm 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}

th {
    border-top: 1.5pt solid #111;
    border-bottom: 1pt solid #111;
    padding: 2mm 3mm;
    font-weight: bold;
    text-align: left;
    background-color: #f7f7f7;
}

td {
    border-bottom: 0.5pt solid #ddd;
    padding: 2mm 3mm;
    vertical-align: middle;
}

tr:last-child td {
    border-bottom: 1.5pt solid #111;
}

/* Equations */
mjx-container[jax="CHTML"][display="true"] {
    margin: 3mm 0 !important;
    page-break-inside: avoid;
}

/* Code blocks & Diagrams */
pre {
    background-color: #f8f9fa;
    border: 0.5pt solid #ccc;
    border-radius: 3px;
    padding: 3mm 4mm;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 8.5pt;
    line-height: 1.35;
    overflow-x: auto;
    page-break-inside: avoid;
}

code {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
    background: #f2f2f2;
    padding: 1px 3px;
    border-radius: 2px;
}

/* Lists */
ul, ol {
    margin-top: 1.5mm;
    margin-bottom: 2mm;
    padding-left: 6mm;
}

li {
    margin-bottom: 1mm;
}

hr {
    border: none;
    border-top: 0.5pt solid #bbb;
    margin: 5mm 0;
}

/* References section */
ol:last-of-type li {
    font-size: 9pt;
    line-height: 1.35;
    margin-bottom: 2mm;
    text-align: left;
}
"""

html_full = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Precision Determination of Gravitational Acceleration (g)</title>
<style>
{academic_css}
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
    "--virtual-time-budget=6000",
    f"--print-to-pdf={PDF_OUT}",
    file_url
]

subprocess.run(cmd, check=True)

if os.path.exists(PDF_OUT):
    size_kb = os.path.getsize(PDF_OUT) / 1024.0
    print(f"[SUCCESS] PDF generated successfully!")
    print(f"Path: {PDF_OUT}")
    print(f"Size: {size_kb:.1f} KB")
else:
    print("[ERROR] PDF generation failed.")
