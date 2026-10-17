"""Generate a publication-grade Microsoft Word (.docx) document from docs/RESEARCH_REPORT.md.
Uses python-docx, latex2mathml, and Microsoft Office's native MML2OMML.XSL to produce
genuine Office Math equations, styled tables, high-res figures, and academic typography.
"""

import os
import re
import shutil
import lxml.etree as ET
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import latex2mathml.converter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
INPUT_MD = os.path.join(PROJECT_DIR, "docs", "RESEARCH_REPORT.md")
DOCX_OUT = os.path.join(PROJECT_DIR, "docs", "Katers_Pendulum_Research_Report.docx")
DESKTOP_OUT = r"c:\Users\manee\Desktop\Katers_Pendulum_Research_Report.docx"
XSLT_PATH = r"C:\Program Files\Microsoft Office\Root\Office16\MML2OMML.XSL"

# Load XSLT transform
xslt_doc = ET.parse(XSLT_PATH)
transform = ET.XSLT(xslt_doc)

def latex_to_omml(latex_str):
    """Convert LaTeX string to Word OMML element."""
    try:
        cleaned = latex_str.strip()
        # Remove tag if present
        cleaned = re.sub(r'\\tag\{.*?\}', '', cleaned).strip()
        # Remove alignment environments
        cleaned = re.sub(r'\\begin\{aligned\}|\\end\{aligned\}', '', cleaned).strip()
        cleaned = cleaned.replace('&', '').strip()
        cleaned = cleaned.replace(r'\implies', r'\rightarrow')
        
        mml = latex2mathml.converter.convert(cleaned)
        mml_root = ET.fromstring(mml)
        omml_tree = transform(mml_root)
        omml_xml_str = ET.tostring(omml_tree.getroot(), encoding='unicode')
        return parse_xml(omml_xml_str)
    except Exception as e:
        return None

def convert_display_equation(raw_math):
    """Convert a display math block (including multi-line / aligned) into a list of tuples:
    [(omml_element, fallback_text, tag_str), ...]
    """
    tag_match = re.search(r'\\tag\{(\d+)\}', raw_math)
    tag_str = f"({tag_match.group(1)})" if tag_match else None
    
    cleaned = re.sub(r'\\tag\{.*?\}', '', raw_math).strip()
    cleaned = re.sub(r'\\begin\{aligned\}|\\end\{aligned\}', '', cleaned).strip()
    
    # Check if multi-line (contains \\)
    if r'\\' in cleaned:
        sub_lines = [l.strip() for l in cleaned.split(r'\\')]
        results = []
        valid_lines = [l for l in sub_lines if l.strip()]
        for idx, sub_line in enumerate(valid_lines):
            sub_line_clean = sub_line.replace('&', '').strip()
            omml_el = latex_to_omml(sub_line_clean)
            sub_tag = tag_str if (idx == len(valid_lines) - 1) else None
            results.append((omml_el, sub_line_clean, sub_tag))
        return results
    else:
        cleaned_single = cleaned.replace('&', '').strip()
        omml_el = latex_to_omml(cleaned_single)
        return [(omml_el, cleaned_single, tag_str)]

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner cell padding in twips (1 pt = 20 twips)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for margin_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{margin_name}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_background(cell, hex_color):
    """Set background shading for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_table_borders(table):
    """Apply academic booktabs style borders (top/bottom thick, header thin)."""
    tblPr = table._tbl.tblPr
    tblBorders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="12" w:space="0" w:color="111111"/>\n'
        f'  <w:bottom w:val="single" w:sz="12" w:space="0" w:color="111111"/>\n'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="DDDDDD"/>\n'
        f'  <w:left w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'  <w:insideV w:val="none"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(tblBorders)

def add_formatted_text(p, text, is_bold=False, is_italic=False):
    """Parse inline bold, italic, code, and inline math into runs with arbitrary nesting."""
    token_pattern = re.compile(
        r'(\\\(.*?\\\)|\$(?!\$)[^\$]+?\$(?!\$)|\*\*.*?\*\*|(?<!\*)\*[^\*]+?\*(?!\*)|`.*?`)'
    )
    tokens = token_pattern.split(text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith(r'\(') and tok.endswith(r'\)'):
            math_content = tok[2:-2]
            omml_el = latex_to_omml(math_content)
            if omml_el is not None:
                p._p.append(omml_el)
            else:
                run = p.add_run(math_content)
                run.italic = True
                run.bold = is_bold
        elif tok.startswith('$') and tok.endswith('$'):
            math_content = tok[1:-1]
            omml_el = latex_to_omml(math_content)
            if omml_el is not None:
                p._p.append(omml_el)
            else:
                run = p.add_run(math_content)
                run.italic = True
                run.bold = is_bold
        elif tok.startswith('**') and tok.endswith('**'):
            inner = tok[2:-2]
            add_formatted_text(p, inner, is_bold=True, is_italic=is_italic)
        elif tok.startswith('*') and tok.endswith('*'):
            inner = tok[1:-1]
            add_formatted_text(p, inner, is_bold=is_bold, is_italic=True)
        elif tok.startswith('`') and tok.endswith('`'):
            run = p.add_run(tok[1:-1])
            run.font.name = 'Consolas'
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(40, 40, 40)
        else:
            run = p.add_run(tok)
            run.bold = is_bold
            run.italic = is_italic

def generate_docx():
    print(f"[1/4] Reading {INPUT_MD}...")
    with open(INPUT_MD, "r", encoding="utf-8") as f:
        content = f.read()

    doc = Document()

    # 1. Page Setup: 1 inch normal margins
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)
        s.page_width = Inches(8.5)
        s.page_height = Inches(11.0)
        # Add running footer
        footer = s.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        f_run = f_p.add_run("Precision Determination of g — Kater's Pendulum")
        f_run.font.name = 'Times New Roman'
        f_run.font.size = Pt(8.5)
        f_run.font.color.rgb = RGBColor(120, 120, 120)

    # 2. Configure base Normal style
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(11)
    style_normal.font.color.rgb = RGBColor(20, 20, 20)
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(4)

    lines = content.split('\n')
    i = 0
    in_abstract = False
    in_code_block = False
    code_buffer = []

    print("[2/4] Parsing and formatting document sections...")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Handle code blocks (e.g. ASCII diagrams)
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.2)
                p.paragraph_format.right_indent = Inches(0.2)
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.line_spacing = 1.05
                run = p.add_run("\n".join(code_buffer))
                run.font.name = 'Consolas'
                run.font.size = Pt(8.5)
                code_buffer = []
            else:
                in_code_block = True
                code_buffer = []
            i += 1
            continue

        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue

        # Handle figures embedded as HTML <figure>...</figure>
        if stripped.startswith("<figure>"):
            fig_lines = []
            while i < len(lines) and not lines[i].strip().endswith("</figure>"):
                fig_lines.append(lines[i])
                i += 1
            if i < len(lines):
                fig_lines.append(lines[i])
            fig_html = "\n".join(fig_lines)

            # Extract image src and caption text
            src_match = re.search(r'<img\s+src=["\']([^"\']+)["\']', fig_html)
            cap_match = re.search(r'<figcaption>(.*?)</figcaption>', fig_html, re.DOTALL)

            if src_match:
                img_rel = src_match.group(1).replace("/", os.sep)
                img_full = os.path.join(PROJECT_DIR, "docs", img_rel)
                if not os.path.exists(img_full):
                    img_full = os.path.join(PROJECT_DIR, img_rel)

                if os.path.exists(img_full):
                    p_img = doc.add_paragraph()
                    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_img.paragraph_format.space_before = Pt(10)
                    p_img.paragraph_format.space_after = Pt(3)
                    p_img.paragraph_format.keep_with_next = True
                    run_img = p_img.add_run()
                    run_img.add_picture(img_full, width=Inches(6.2))

                    if cap_match:
                        raw_caption = cap_match.group(1).strip()
                        p_cap = doc.add_paragraph()
                        p_cap.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        p_cap.paragraph_format.left_indent = Inches(0.25)
                        p_cap.paragraph_format.right_indent = Inches(0.25)
                        p_cap.paragraph_format.space_before = Pt(2)
                        p_cap.paragraph_format.space_after = Pt(10)
                        
                        strong_m = re.search(r'<(?:strong|b)>(.*?)</(?:strong|b)>', raw_caption)
                        if strong_m:
                            pref = strong_m.group(1).strip()
                            add_formatted_text(p_cap, pref + " ", is_bold=True)
                            rem_text = raw_caption[strong_m.end():].strip()
                            rem_text = re.sub(r'</?(?:em|i|span|p)>', '', rem_text)
                            add_formatted_text(p_cap, rem_text)
                        else:
                            clean_caption = re.sub(r'</?(?:strong|b|em|i)>', '', raw_caption)
                            fig_m = re.match(r'^(Figure\s+\d+\.)', clean_caption)
                            if fig_m:
                                pref = fig_m.group(1)
                                add_formatted_text(p_cap, pref + " ", is_bold=True)
                                rem_text = clean_caption[len(pref):].strip()
                                add_formatted_text(p_cap, rem_text)
                            else:
                                add_formatted_text(p_cap, clean_caption)
                        
                        for r in p_cap.runs:
                            r.font.size = Pt(9.5)
            i += 1
            continue

        # Handle Title (H1)
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title_text = stripped[2:].strip()
            # Clean math formatting from title if present
            title_text = title_text.replace(r'\(g\)', 'g').replace('$g$', 'g')
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(18)
            run = p.add_run(title_text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(18)
            run.bold = True
            
            # Add a clean author placeholder line for the user to fill manually
            p_author = doc.add_paragraph()
            p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_author.paragraph_format.space_before = Pt(0)
            p_author.paragraph_format.space_after = Pt(18)
            r_auth = p_author.add_run("[ Author Names and Institutional Affiliations ]")
            r_auth.font.name = 'Times New Roman'
            r_auth.font.size = Pt(11)
            r_auth.italic = True
            r_auth.font.color.rgb = RGBColor(100, 100, 100)
            
            i += 1
            continue

        # Handle Section (H2)
        if stripped.startswith("## ") and not stripped.startswith("### "):
            sec_title = stripped[3:].strip()
            if sec_title.lower() == "abstract":
                in_abstract = True
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.keep_with_next = True
                run = p.add_run("Abstract")
                run.bold = True
                run.font.size = Pt(12)
            else:
                in_abstract = False
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(14)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.keep_with_next = True
                add_formatted_text(p, sec_title)
                for r in p.runs:
                    r.bold = True
                    r.font.size = Pt(13)
            i += 1
            continue

        # Handle Subsection (H3)
        if stripped.startswith("### ") and not stripped.startswith("#### "):
            subsec_title = stripped[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            add_formatted_text(p, subsec_title)
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(11.5)
            i += 1
            continue

        # Handle Sub-subsection (H4)
        if stripped.startswith("#### "):
            sub3_title = stripped[5:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            add_formatted_text(p, sub3_title)
            for r in p.runs:
                r.bold = True
                r.italic = True
                r.font.size = Pt(11)
            i += 1
            continue

        # Handle Separators (---)
        if stripped == "---":
            # Can be treated as clean section break spacing
            i += 1
            continue

        # Handle Display Math ($$...$$)
        if stripped.startswith("$$"):
            math_lines = []
            if stripped.endswith("$$") and len(stripped) > 4:
                math_lines.append(stripped[2:-2])
            else:
                math_lines.append(stripped[2:])
                i += 1
                while i < len(lines) and not lines[i].strip().endswith("$$"):
                    math_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    tail = lines[i].strip()
                    if tail.endswith("$$"):
                        math_lines.append(tail[:-2])
            
            raw_math = "\n".join(math_lines).strip()
            eq_items = convert_display_equation(raw_math)
            
            for idx, (omml_el, eq_text, tag_str) in enumerate(eq_items):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if len(eq_items) > 1:
                    p.paragraph_format.space_before = Pt(2) if idx > 0 else Pt(6)
                    p.paragraph_format.space_after = Pt(2) if idx < len(eq_items) - 1 else Pt(6)
                    if idx < len(eq_items) - 1:
                        p.paragraph_format.keep_with_next = True
                else:
                    p.paragraph_format.space_before = Pt(6)
                    p.paragraph_format.space_after = Pt(6)
                
                if omml_el is not None:
                    p._p.append(omml_el)
                    if tag_str:
                        r_tab = p.add_run(f"    {tag_str}")
                        r_tab.font.name = 'Times New Roman'
                        r_tab.font.size = Pt(11)
                else:
                    r = p.add_run(eq_text)
                    r.italic = True
                    if tag_str:
                        p.add_run(f"    {tag_str}")
            i += 1
            continue

        # Handle Tables (| col1 | col2 |)
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            
            # Parse rows
            rows_data = []
            for tl in table_lines:
                # Skip separator rows | :--- | :--- |
                if re.match(r'^\|[\s\-:]+(\|[\s\-:]+)+\|$', tl):
                    continue
                cells = [c.strip() for c in tl.split("|")[1:-1]]
                rows_data.append(cells)
            
            if rows_data:
                num_cols = max(len(r) for r in rows_data)
                tbl = doc.add_table(rows=len(rows_data), cols=num_cols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl)
                
                for r_idx, row in enumerate(rows_data):
                    is_header = (r_idx == 0)
                    for c_idx in range(num_cols):
                        cell = tbl.cell(r_idx, c_idx)
                        set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
                        if is_header:
                            set_cell_background(cell, "F2F2F2")
                        
                        c_text = row[c_idx] if c_idx < len(row) else ""
                        p = cell.paragraphs[0]
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(0)
                        p.paragraph_format.line_spacing = 1.1
                        
                        add_formatted_text(p, c_text)
                        
                        for r in p.runs:
                            r.font.name = 'Times New Roman'
                            r.font.size = Pt(9.5)
                            if is_header:
                                r.bold = True
                
                # Add spacing after table
                p_spacer = doc.add_paragraph()
                p_spacer.paragraph_format.space_before = Pt(0)
                p_spacer.paragraph_format.space_after = Pt(6)
            continue

        # Handle Bulleted Lists (* or -)
        if stripped.startswith("* ") or stripped.startswith("- "):
            list_text = stripped[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, list_text)
            i += 1
            continue

        # Handle Numbered Lists (1. )
        num_match = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if num_match:
            item_text = num_match.group(2).strip()
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_text(p, item_text)
            i += 1
            continue

        # Handle Regular Paragraphs
        if stripped:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            if in_abstract:
                p.paragraph_format.left_indent = Inches(0.4)
                p.paragraph_format.right_indent = Inches(0.4)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(8)
                p.paragraph_format.line_spacing = 1.15
                add_formatted_text(p, stripped)
                for r in p.runs:
                    r.font.size = Pt(10)
                    r.italic = True
            else:
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.line_spacing = 1.15
                add_formatted_text(p, stripped)

        i += 1

    print(f"[3/4] Saving to {DOCX_OUT}...")
    doc.save(DOCX_OUT)
    print(f"[4/4] Copying to Desktop: {DESKTOP_OUT}...")
    shutil.copy2(DOCX_OUT, DESKTOP_OUT)
    print("SUCCESS: Research report docx generated and verified!")

if __name__ == "__main__":
    generate_docx()
