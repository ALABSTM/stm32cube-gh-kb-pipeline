"""
STM32Cube Preprocessing Pipeline — Workshop Presentation (Final Version)
Merges reference deck content with new professional English structure.
Includes: architecture, full pipeline, ALFRED, operational details, troubleshooting.

Run:  python docs/generate_workshop_pptx_final.py
Output: docs/Atelier_Pratique_Pipeline_STM32Cube.pptx

Companion draw.io diagrams: docs/diagrams/01..04_*.drawio
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Cm, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS — STMicroelectronics corporate palette
# ═══════════════════════════════════════════════════════════════════════════════
ST_BLUE = RGBColor(0x03, 0x23, 0x4B)
ST_LIGHT_BLUE = RGBColor(0x3C, 0xB4, 0xE6)
ST_GREEN = RGBColor(0x4C, 0xAF, 0x50)
ST_ORANGE = RGBColor(0xFF, 0x98, 0x00)
ST_RED = RGBColor(0xF4, 0x43, 0x36)
ST_PURPLE = RGBColor(0x9C, 0x27, 0xB0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF5, 0xF5, 0xF5)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title_slide(prs, title, subtitle=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, ST_BLUE)
    txBox = slide.shapes.add_textbox(Inches(0.8), Inches(2.5), Inches(8.4), Inches(2))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.LEFT
    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(18)
        p2.font.color.rgb = ST_LIGHT_BLUE
        p2.alignment = PP_ALIGN.LEFT
    return slide


def add_section_slide(prs, title):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, ST_LIGHT_BLUE)
    txBox = slide.shapes.add_textbox(Inches(1), Inches(3), Inches(8), Inches(1.5))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER
    return slide


def add_content_slide(prs, title, bullets, note=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    # Title bar
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(1))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ST_BLUE
    shape.line.fill.background()
    tf = shape.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.LEFT
    # Bullets
    txBox = slide.shapes.add_textbox(Inches(0.6), Inches(1.3), Inches(8.8), Inches(5.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        if bullet.startswith("##"):
            p.text = bullet[2:].strip()
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = ST_BLUE
            p.space_before = Pt(12)
        elif bullet.startswith("```"):
            p.text = bullet[3:].strip()
            p.font.size = Pt(12)
            p.font.name = "Consolas"
            p.font.color.rgb = DARK_GRAY
            p.space_before = Pt(4)
        else:
            p.text = bullet
            p.font.size = Pt(14)
            p.font.color.rgb = DARK_GRAY
            p.space_before = Pt(6)
    if note:
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = note
    return slide


def add_diagram_slide(prs, title, boxes, arrows_text=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(0.9))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ST_BLUE
    shape.line.fill.background()
    tf = shape.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = WHITE
    colors = [ST_LIGHT_BLUE, ST_GREEN, ST_ORANGE, ST_PURPLE, ST_RED, RGBColor(0x00, 0x96, 0x88), ST_BLUE]
    start_y = 1.2
    box_h = 0.7
    gap = 0.15
    for i, (label, desc) in enumerate(boxes):
        y = start_y + i * (box_h + gap)
        color = colors[i % len(colors)]
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(y), Inches(2.5), Inches(box_h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        tf = shape.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = label
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER
        txBox = slide.shapes.add_textbox(Inches(3.2), Inches(y), Inches(6.5), Inches(box_h))
        tf2 = txBox.text_frame
        tf2.vertical_anchor = MSO_ANCHOR.MIDDLE
        p2 = tf2.paragraphs[0]
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = DARK_GRAY
        if i < len(boxes) - 1:
            arrow_y = y + box_h
            shape_arrow = slide.shapes.add_shape(
                MSO_SHAPE.DOWN_ARROW, Inches(1.6), Inches(arrow_y), Inches(0.3), Inches(gap)
            )
            shape_arrow.fill.solid()
            shape_arrow.fill.fore_color.rgb = LIGHT_GRAY
            shape_arrow.line.fill.background()
    return slide


def add_horizontal_flow_slide(prs, title, rows):
    """Create a slide with horizontal flow rows. Each row is (row_label, [(box_label, color), ...])."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(0.9))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ST_BLUE
    shape.line.fill.background()
    tf = shape.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = WHITE
    row_h = 0.65
    gap_y = 0.25
    start_y = 1.1
    for r_idx, (row_label, boxes) in enumerate(rows):
        y = start_y + r_idx * (row_h + gap_y)
        # Row label
        lbl = slide.shapes.add_textbox(Inches(0.1), Inches(y), Inches(1.4), Inches(row_h))
        tf_lbl = lbl.text_frame
        tf_lbl.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_lbl = tf_lbl.paragraphs[0]
        p_lbl.text = row_label
        p_lbl.font.size = Pt(9)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = DARK_GRAY
        p_lbl.alignment = PP_ALIGN.RIGHT
        # Boxes in this row
        n = len(boxes)
        available_w = 8.2
        box_w = min(1.4, (available_w - 0.15 * (n - 1)) / max(n, 1))
        gap_x = 0.15
        for b_idx, (box_label, color) in enumerate(boxes):
            x = 1.6 + b_idx * (box_w + gap_x)
            bx = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(box_w), Inches(row_h))
            bx.fill.solid()
            bx.fill.fore_color.rgb = color
            bx.line.fill.background()
            tf_b = bx.text_frame
            tf_b.word_wrap = True
            tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_b = tf_b.paragraphs[0]
            p_b.text = box_label
            p_b.font.size = Pt(8)
            p_b.font.bold = True
            p_b.font.color.rgb = WHITE
            p_b.alignment = PP_ALIGN.CENTER
            # Arrow between boxes
            if b_idx < n - 1:
                ax = x + box_w
                ay = y + row_h / 2 - 0.08
                arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax), Inches(ay), Inches(gap_x), Inches(0.16))
                arr.fill.solid()
                arr.fill.fore_color.rgb = LIGHT_GRAY
                arr.line.fill.background()
    return slide


def add_table_slide(prs, title, headers, rows):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(0.9))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ST_BLUE
    shape.line.fill.background()
    tf = shape.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = WHITE
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(0.3), Inches(1.1), Inches(9.4), Inches(0.4 * num_rows))
    table = table_shape.table
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = ST_BLUE
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = WHITE
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = str(val)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.color.rgb = DARK_GRAY
    return slide


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — Build the presentation
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 0 — TITLE & AGENDA
    # ══════════════════════════════════════════════════════════════════════

    add_title_slide(
        prs,
        "STM32Cube Preprocessing Pipeline\nFrom Raw GitHub Data to AI-Ready Knowledge",
        "Practical Workshop \u2014 Full End-to-End Workflow"
    )

    add_content_slide(prs, "Agenda", [
        "## 1. Executive Summary",
        "## 2. Context & Business Need",
        "## 3. Architecture Overview (+ Master Diagram)",
        "## 4. End-to-End Pipeline \u2014 23 Steps",
        "## 5. Configuration & Execution",
        "## 6. Preprocessing Deep Dive (Cleaning, Enrichment, Similarity)",
        "## 7. ALFRED Vision Integration (PDF + Images)",
        "## 8. Delivery & Upload to Knowledge Base",
        "## 9. Quality Gates & Validation",
        "## 10. Value Proposition & Impact",
        "## 11. Operational Guide (Troubleshooting, Best Practices)",
        "## 12. Live Demo & Hands-On",
        "## 13. Conclusion & Next Steps",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1 — EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "1. Executive Summary")

    add_content_slide(prs, "What This Workshop Is About", [
        "## Problem",
        "\u2022 STM32 technical knowledge is fragmented across 25+ GitHub repos, 10k+ issues, PDFs, and images.",
        "\u2022 Without structured preprocessing, AI assistants produce generic, unsourced, or inaccurate answers.",
        "",
        "## Solution",
        "\u2022 A 7-stage automated pipeline that transforms raw GitHub signals into structured,",
        "  traceable, upload-ready Knowledge Base artifacts for ST ChatGPT.",
        "",
        "## What You Will Learn",
        "\u2022 How to configure, run, validate, and deploy the full pipeline for any STM32 series.",
        "\u2022 How ALFRED Vision enriches images and PDF figures into searchable descriptions.",
        "\u2022 How quality gates ensure production-grade reliability before each KB upload.",
    ])

    add_content_slide(prs, "Key Message \u2014 30 Seconds", [
        "## One sentence",
        "\u2022 This pipeline turns scattered, heterogeneous GitHub data into AI-ready knowledge",
        "  that makes STM32 support answers more relevant, traceable, and actionable.",
        "",
        "## By the numbers",
        "\u2022 25 MCU series configured | 19 fully processed with PDF enrichment",
        "\u2022 242 PDF figure descriptions generated via ALFRED Vision",
        "\u2022 4 artifact types per series: Issues, Files, Resolver Cases, Diagnostic Cards",
        "\u2022 Quality Index: 94/100 on pilot series H7 with Diagnostic Cards",
        "",
        "## Impact",
        "\u2022 KB-first answers are +39% more relevant than generic LLM on STM32 technical questions.",
        "\u2022 This is not just an ETL \u2014 it\u2019s a quality chain for reliable AI-powered support.",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 2 — CONTEXT & BUSINESS NEED
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "2. Context & Business Need")

    add_content_slide(prs, "The Problem Space", [
        "## Current Challenges",
        "\u2022 Customer support engineers spend significant time searching fragmented sources.",
        "\u2022 Raw GitHub issues contain noise: off-topic, duplicates, short questions, images without text.",
        "\u2022 PDF documentation contains critical figures that are invisible to text-based search.",
        "\u2022 No automated link between issues, root causes, and resolutions.",
        "",
        "## Business Need",
        "\u2022 A single AI-powered support interface (ST ChatGPT) that answers from verified, structured data.",
        "\u2022 Traceability: every answer must link back to a source (issue, file, commit, figure).",
        "\u2022 Scalability: the solution must work for all 25 STM32 series, not just one.",
        "\u2022 Maintainability: adding a new series must be a simple configuration step.",
    ])

    add_table_slide(prs, "Pain Points vs. Pipeline Solution",
        ["Pain Point", "Without Pipeline", "With Pipeline"],
        [
            ["Fragmented knowledge", "Manual search across repos", "Unified, structured KB artifacts"],
            ["Images/figures not indexed", "Invisible to RAG", "ALFRED descriptions make them searchable"],
            ["No root cause tracing", "Generic LLM guess", "Resolver Cases + Diagnostic Cards"],
            ["Manual per-series work", "Hours of manual curation", "Automated multi-series batch"],
            ["No quality control", "Silent failures", "Schema validation + placeholder gates"],
        ]
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 3 — ARCHITECTURE OVERVIEW
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "3. Architecture Overview")

    add_content_slide(prs, "High-Level System Architecture \u2014 Three Layers", [
        "## Layer 1: DATA SOURCES",
        "\u2022 GitHub API (issues, PRs, commits, files), local repo clones, PDF documents.",
        "\u2022 25 series configured via shared/config/config_<serie>.json.",
        "",
        "## Layer 2: PROCESSING ENGINE",
        "\u2022 Python pipeline: Ingestion \u2192 Cleaning \u2192 Enrichment \u2192 Similarity \u2192 Evaluation \u2192 Delivery.",
        "\u2022 ALFRED Vision API: PDF figure descriptions + issue image descriptions.",
        "\u2022 PowerShell orchestration scripts for batch multi-series workflows.",
        "",
        "## Layer 3: CONSUMPTION",
        "\u2022 KB #793: ST ChatGPT Knowledge Base with Hybrid search (semantic + full-text).",
        "\u2022 Persona: \u201cST GitHub Analyzer\u201d \u2014 KB-first, ALFRED fallback only when KB has no match.",
        "\u2022 End user: support engineer or developer asking STM32 technical questions.",
    ])

    add_content_slide(prs, "Master Architecture Diagram", [
        "## Single-page view of the entire system:",
        "",
        "```\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510    \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510    \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510",
        "```\u2502 DATA SOURCES    \u2502    \u2502 PROCESSING ENGINE (Python)        \u2502    \u2502 CONSUMPTION   \u2502",
        "```\u2502                 \u2502    \u2502                                    \u2502    \u2502               \u2502",
        "```\u2502 GitHub API      \u2502\u2500\u2500\u2500\u25b6\u2502 1.Ingest \u2192 2.Clean \u2192 3.Enrich    \u2502    \u2502 KB #793       \u2502",
        "```\u2502 Local Clones    \u2502\u2500\u2500\u2500\u25b6\u2502 4.Similarity \u2192 5.Eval \u2192 6.Deliver\u2502\u2500\u2500\u2500\u25b6\u2502 (Hybrid)      \u2502",
        "```\u2502 PDF Documents   \u2502\u2500\u2500\u2500\u25b6\u2502 7.Upload                          \u2502    \u2502       \u2502       \u2502",
        "```\u2502 Config JSON     \u2502    \u2502                                    \u2502    \u2502       \u25bc       \u2502",
        "```\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518    \u2502 \u250c\u2500\u2500\u2500\u2500\u2500 ALFRED VISION \u2500\u2500\u2500\u2500\u2500\u2510    \u2502    \u2502 ST ChatGPT    \u2502",
        "```                      \u2502 \u2502 Path A: PDF (step 7)     \u2502    \u2502    \u2502 Persona       \u2502",
        "```                      \u2502 \u2502 Path B: Images (step 23) \u2502    \u2502    \u2502       \u2502       \u2502",
        "```                      \u2502 \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518    \u2502    \u2502       \u25bc       \u2502",
        "```                      \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518    \u2502 End User      \u2502",
        "```                                                              \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518",
        "",
        "## Also available as editable draw.io: docs/diagrams/01_project_architecture.drawio",
    ])

    add_horizontal_flow_slide(prs, "Architecture Diagram \u2014 Visual Flow", [
        ("SOURCES", [
            ("GitHub API\nIssues/PRs/Commits", ST_LIGHT_BLUE),
            ("Local Clones\nGitHub_repos/", ST_LIGHT_BLUE),
            ("PDF Documents\nUser Manuals", ST_ORANGE),
            ("Config JSON\nshared/config/", DARK_GRAY),
        ]),
        ("PIPELINE", [
            ("1. Ingest", ST_GREEN),
            ("2. Clean", ST_GREEN),
            ("3. Enrich", ST_GREEN),
            ("4. Similarity", ST_GREEN),
            ("5. Evaluate", ST_GREEN),
            ("6. Deliver", ST_GREEN),
        ]),
        ("ALFRED", [
            ("Path A: PDF\n(Step 7)", ST_RED),
            ("Path B: Images\n(Step 23)", ST_RED),
        ]),
        ("DELIVERY", [
            ("Issues JSON", ST_PURPLE),
            ("Files JSON v3", ST_PURPLE),
            ("Resolver Cases", ST_PURPLE),
            ("Diagnostic Cards", ST_PURPLE),
        ]),
        ("KB #793", [
            ("Hybrid Search\nsemantic+fulltext", ST_BLUE),
            ("ST ChatGPT\nPersona", ST_BLUE),
            ("End User\nSupport Eng.", ST_BLUE),
        ]),
    ])

    add_diagram_slide(prs, "Architecture \u2014 Data Flow Overview", [
        ("GITHUB API", "Issues, PRs, Commits, Links \u2192 raw JSON per repo"),
        ("LOCAL CLONES", "Repository files: READMEs, Release Notes, PDFs, source code"),
        ("PIPELINE ENGINE", "7 stages: Ingest \u2192 Clean \u2192 Enrich \u2192 Similarity \u2192 Eval \u2192 Deliver \u2192 Upload"),
        ("ALFRED VISION", "Image descriptions (screenshots) + PDF figure descriptions"),
        ("ST-READY ARTIFACTS", "Structured JSON: issues, files, resolver_cases, diagnostic_cards"),
        ("KB #793", "ST ChatGPT Knowledge Base \u2014 Hybrid semantic + full-text search"),
        ("END USER", "Support engineer asks question \u2192 AI answers with source traceability"),
    ])

    add_content_slide(prs, "Project File Structure", [
        "```PFE_Chatbot_STM32Cube/",
        "```\u251c\u2500\u2500 shared/config/             Config per series (config_h7.json, config_f4.json...)",
        "```\u251c\u2500\u2500 shared/schemas/            JSON schema contracts for validation",
        "```\u251c\u2500\u2500 pipeline/",
        "```\u2502   \u251c\u2500\u2500 ingestion/             fetch_issues, fetch_prs, fetch_files, repo_sync",
        "```\u2502   \u251c\u2500\u2500 cleaning/              clean_issues, clean_files (normalize, images)",
        "```\u2502   \u251c\u2500\u2500 enrichment/            issues_to_docs_v2, files_to_docs_v2 (classify)",
        "```\u2502   \u251c\u2500\u2500 similarity/            TF-IDF cosine \u2192 related_issue_ids",
        "```\u2502   \u251c\u2500\u2500 chunking/              docs_to_chunks (paragraph-based)",
        "```\u2502   \u251c\u2500\u2500 delivery/              export_st_ready_* (4 artifact types)",
        "```\u2502   \u2514\u2500\u2500 evaluation/            stats, TF-IDF search, schema validation",
        "```\u251c\u2500\u2500 pipeline_Automation/",
        "```\u2502   \u251c\u2500\u2500 alfred/                enrich_json_images, enrich_pdf_figures",
        "```\u2502   \u251c\u2500\u2500 upload/                Add_Data_Source_Files.py, Get_Persona_KBs.py",
        "```\u2502   \u2514\u2500\u2500 workflow/              PowerShell orchestration (batch, single-series)",
        "```\u251c\u2500\u2500 datasets/07_delivery/      Final ST-ready outputs by_series/",
        "```\u251c\u2500\u2500 GitHub_repos/              Auto-cloned repos (by repo_sync_service.py)",
        "```\u251c\u2500\u2500 data/                      Intermediate artifacts (NOT committed to git)",
        "```\u2514\u2500\u2500 docs/                      Documentation, diagrams, this presentation",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4 — END-TO-END PIPELINE WORKFLOW
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "4. End-to-End Pipeline \u2014 23 Steps")

    add_diagram_slide(prs, "Pipeline \u2014 7 Phases, 23 Steps", [
        ("1-6. INGESTION", "GitHub API calls + local repo sync + file collection (incl. PDFs)"),
        ("7. ALFRED PDF", "Extract PDF figures, render pages, crop regions, generate descriptions"),
        ("8-9. CLEANING", "Normalize text, detect [IMAGE ATTACHED], structure content"),
        ("10-12. ENRICHMENT", "Classify: layer, board, component, severity, is_valid + similarity"),
        ("13-17. EVALUATION", "Chunking + stats + TF-IDF search tests + schema validation"),
        ("18-22. DELIVERY", "Export 4 artifact types + issues_with_images variant"),
        ("23. ALFRED IMAGES", "ALFRED Vision on issue screenshots \u2192 [IMAGE DESCRIPTION]"),
    ])

    add_content_slide(prs, "run_full_workflow.py \u2014 Internal Steps (Real Code)", [
        "## STEPS list (executed in order):",
        '```("Ingestion issues",     fetch_issues_main)      # 1',
        '```("Ingestion PRs",        fetch_prs_main)         # 2',
        '```("Ingestion commits",    fetch_commits_main)     # 3',
        '```("Ingestion links",      fetch_links_main)       # 4',
        '```("Ingestion sync repos", sync_local_repos_main)  # 5',
        '```("Ingestion files",      fetch_files_main)       # 6',
        '```("Alfred PDF figures",   _enrich_pdf_main)       # 7',
        '```("Cleaning issues",      clean_issues_main)      # 8',
        '```("Cleaning files",       clean_files_main)       # 9',
        '```("Enrichment issues V2", issues_to_docs_v2_main) # 10',
        '```("Enrichment files V2",  files_to_docs_v2_main)  # 11',
        '```("Similarity issues V2", similarity_main)        # 12',
        '```("Chunking issues V2",   chunks_issues_main)     # 13',
        '```("Chunking files V2",    chunks_files_main)      # 14',
        '```("Stats issues V2",      stats_issues_main)      # 15',
        '```("Stats files V2",       stats_files_main)       # 16',
        '```("Schema validation",    validate_schemas_main)  # 17',
    ])

    add_content_slide(prs, "run_full_workflow.py \u2014 Delivery Steps (--export-st-ready)", [
        "## --export-st-ready adds 6 additional steps:",
        '```("Delivery ST-ready issues",           export_issues_all)      # 18',
        '```("Delivery ST-ready files",            export_files_all)       # 19',
        '```("Delivery ST-ready resolver",         export_resolver_all)    # 20',
        '```("Delivery ST-ready diag cards",       export_diag_all)        # 21',
        '```("Delivery ST-ready issues with imgs", export_with_images_all) # 22',
        '```("Alfred image descriptions",          _enrich_alfred_images)  # 23',
        "",
        "## How flags filter steps:",
        "\u2022 --skip-ingestion \u2192 removes steps where label starts with \u201cIngestion\u201d",
        "\u2022 --skip-chunking \u2192 removes steps with label \u201cChunking\u201d",
        "\u2022 --no-enrich-pdf \u2192 removes \u201cAlfred PDF figures\u201d step",
        "",
        "## Error handling:",
        "\u2022 Without --continue-on-error \u2192 exception = STOP immediately",
        "\u2022 With --continue-on-error \u2192 print [WARN] + continue to next step",
    ])

    add_table_slide(prs, "Pipeline Steps \u2014 Detail Table",
        ["#", "Stage", "Script", "Output"],
        [
            ["1", "Fetch Issues", "pipeline/ingestion/fetch_issues.py", "data/raw_issues_<repo>.json"],
            ["2", "Fetch PRs", "pipeline/ingestion/fetch_prs.py", "data/raw_prs_<repo>.json"],
            ["3", "Fetch Commits", "pipeline/ingestion/fetch_commits.py", "data/raw_commits_<repo>.json"],
            ["4", "Fetch Links", "fetch_issue_pr_commit_links.py", "data/links_<repo>.json"],
            ["5", "Sync Repos", "repo_sync_service.py", "GitHub_repos/<repo>/"],
            ["6", "Fetch Files", "pipeline/ingestion/fetch_files.py", "data/raw_files_<repo>.json"],
            ["7", "Alfred PDF", "pdf_figure_service.py", "data/pdf_image_descriptions.json"],
            ["8", "Clean Issues", "pipeline/cleaning/clean_issues.py", "data/clean_issues_<repo>.json"],
            ["9", "Clean Files", "pipeline/cleaning/clean_files.py", "data/clean_files_<repo>.json"],
            ["10", "Enrich Issues", "enrichment/issues_to_docs_v2.py", "data/docs_issues_<repo>_v2.json"],
            ["11", "Enrich Files", "enrichment/files_to_docs_v2.py", "data/docs_files_<repo>_v2.json"],
            ["12", "Similarity", "compute_issue_similarity_v2.py", "docs_issues_<repo>_v2_sim.json"],
        ]
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 5 — CONFIGURATION & EXECUTION
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "5. Configuration & Execution")

    add_content_slide(prs, "Series Configuration \u2014 config_<serie>.json", [
        "## One JSON file per series: shared/config/config_<serie>.json",
        "",
        "## Actual example (config_g4.json):",
        '```{"owner": "STMicroelectronics",',
        '``` "repos": ["STM32CubeG4", "stm32g4xx-hal-driver", "cmsis_device_g4",',
        '```          "stm32g4xx-nucleo-bsp", "b-g474e-dpow1-bsp", ...],',
        '``` "data_dir": "data",  "repos_dir": "GitHub_repos",',
        '``` "auto_clone_missing_repos": true,',
        '``` "repo_clone_urls": {"b-g474e-dpow1-bsp": "https://github.com/...git"},',
        '``` "linked_repo_refs": {"b-g474e-dpow1-bsp": "4e6afe34..."},',
        '``` "rate_limits": {"issues_sleep": 0.2, "comments_sleep": 0.1}}',
        "",
        "## Environment variable:",
        '```$env:STM32CUBE_CONFIG = "shared/config/config_g4.json"',
        "",
        "## Sub-repo routing (delivery_paths.py):",
        "\u2022 Each sub-repo is routed to by_series/<serie>/drivers/<sub-repo>/",
        "\u2022 Drivers share the parent series datasource in KB",
    ])

    add_content_slide(prs, "Creating config_<serie>.json \u2014 Where Data Comes From", [
        "## Required fields and their sources:",
        "",
        '## \u2022 "owner": always "STMicroelectronics"',
        "",
        '## \u2022 "repos": parent repo + all drivers/BSPs/CMSIS/middleware',
        "  Source: STM32CubeXX GitHub page \u2192 .gitmodules lists all sub-repos",
        "  Or: STM32CubeXX/Release_Notes.html \u2192 component list",
        "",
        '## \u2022 "repo_clone_urls": HTTPS clone URL for each sub-repo',
        "  Format: https://github.com/STMicroelectronics/<repo-name>.git",
        "",
        '## \u2022 "linked_repo_refs": commit SHA for each sub-repo',
        "  Source: .gitmodules or auto-detected by audit_config_submodules --fix",
        "",
        '## \u2022 "rate_limits": {"issues_sleep": 0.2, "comments_sleep": 0.1}',
        "  Increase to 0.5 if GitHub rate-limited",
        "",
        "## Workflow: copy existing config \u2192 change repos[] \u2192 run:",
        "```python -m pipeline.evaluation.audit_config_submodules --fix",
    ])

    add_content_slide(prs, "Running the Full Pipeline \u2014 One Command", [
        "## Set the target series:",
        '```$env:STM32CUBE_CONFIG = "shared/config/config_h7.json"',
        "",
        "## Launch complete workflow with delivery:",
        "```python -m pipeline.run_full_workflow --export-st-ready --continue-on-error",
        "",
        "## What this executes (in order):",
        "\u2022 Steps 1-6: Ingestion (issues, PRs, commits, links, repo sync, files)",
        "\u2022 Step 7: ALFRED PDF figure extraction and task generation",
        "\u2022 Steps 8-9: Cleaning (issues + files)",
        "\u2022 Steps 10-12: Enrichment V2 + Similarity",
        "\u2022 Steps 13-17: Chunking + evaluation + schema validation",
        "\u2022 Steps 18-22: Delivery exports (4 artifact types + with_images)",
        "\u2022 Step 23: ALFRED Vision on issue images (final step)",
        "",
        "## Duration: ~10-30 min per series (depends on issue/file count)",
        "## Config resolution: $env:STM32CUBE_CONFIG \u2192 shared/utils/paths.py \u2192 get_config_path()",
    ])

    add_content_slide(prs, "Pipeline Control Flags", [
        "## --export-st-ready",
        "\u2022 Activates delivery steps (18-23): issues, files, resolver, diag, with_images, ALFRED",
        "\u2022 Without this flag, pipeline stops after evaluation (step 17)",
        "",
        "## --continue-on-error",
        "\u2022 If one step fails (e.g., a sub-repo has no issues), continues to the next",
        "\u2022 Essential for multi-repo series configurations",
        "",
        "## --skip-ingestion",
        "\u2022 Skips GitHub API calls; uses existing raw_* files in data/",
        "\u2022 Saves API rate limit (GitHub: 5000 req/h with token, 60/h without)",
        "\u2022 Tip: increase issues_sleep in config (0.2 \u2192 0.5) if rate-limited",
        "",
        "## --skip-chunking",
        "\u2022 Skips local chunking (steps 13-14) \u2014 ST platform does its own at upload",
        "",
        "## --no-enrich-pdf",
        "\u2022 Skips ALFRED Vision on PDF figures (step 7)",
        "\u2022 Use when PDFs are already enriched or proxy/network is unavailable",
    ])

    add_table_slide(prs, "Script Comparison \u2014 Python vs PowerShell",
        ["Aspect", "run_full_workflow.py", "Run_Single_Series_*.ps1", "Run_Issues_Pipeline.ps1"],
        [
            ["Language", "Python", "PowerShell", "PowerShell"],
            ["Scope", "1 series (current config)", "1 series (-Series H7)", "ALL repos in config"],
            ["Steps", "17 base + 6 delivery", "sync + audit + workflow + delivery + Alfred + patch + validate + upload", "3-5 steps only"],
            ["What it processes", "Issues + Files + ALL", "Issues + Files + Drivers + Upload", "Issues ONLY"],
            ["Ingestion", "\u2713 (steps 1-6)", "\u2713 (via repo_sync + workflow)", "\u2717 (assumes raw data exists)"],
            ["ALFRED PDF", "\u2713 (step 7)", "\u2713 (inside workflow)", "\u2717"],
            ["ALFRED Images", "\u2713 (step 23)", "\u2713 (dedicated step)", "\u2717"],
            ["Drivers/Sub-repos", "Only parent repo", "\u2713 Parent + all drivers", "All repos in config"],
            ["KB Upload", "\u2717", "\u2713 (create+add DS)", "\u2717"],
            ["Schema Validation", "\u2713 (step 17)", "\u2713 + Placeholder gate", "\u2717"],
            ["Mode", "Flags only", "Full / Prepare / Upload", "Flags: -WithSimilarity -WithChunking"],
            ["Use case", "Dev / debug / from scratch", "Production: one-click series", "Quick issues-only reprocess"],
        ]
    )

    add_content_slide(prs, "Run_Single_Series Modes \u2014 Full vs Prepare vs Upload", [
        "## Mode=Full (default): End-to-end in one command",
        "```Sync repos \u2192 Audit configs \u2192 run_full_workflow \u2192 Export parent",
        "```\u2192 Export drivers \u2192 ALFRED images \u2192 Export V3 files \u2192 Patch PDF",
        "```\u2192 Schema validation \u2192 Placeholder gate \u2192 Create DS \u2192 Upload all",
        "",
        "## Mode=Prepare: Pipeline + export only (NO upload)",
        "```Sync repos \u2192 Audit \u2192 workflow \u2192 Export \u2192 ALFRED \u2192 Patch \u2192 Validate",
        "\u2022 Use this to inspect delivery JSON before sending to KB",
        "\u2022 Combine with -PlaceholderPolicy Warn for dry-run",
        "",
        "## Mode=Upload: Upload ONLY (pipeline already done)",
        "```Read saved DS IDs \u2192 Upload parent \u2192 Upload drivers \u2192 Save IDs",
        "\u2022 Requires Mode=Prepare or Mode=Full to have run first",
        "\u2022 Reuses upload_datasource_ids_<slug>.json for idempotent reruns",
        "",
        "## Parameters:",
        "\u2022 -Series H7 | -SkipDrivers | -PlaceholderPolicy Fail/Warn/Off",
        "\u2022 -IssuesDatasourceId 24406 (override saved ID)",
    ])

    add_content_slide(prs, "Step-by-Step: What Each Script Actually Runs", [
        "## run_full_workflow.py (Python, 17+6 steps):",
        "```fetch_issues \u2192 fetch_prs \u2192 fetch_commits \u2192 fetch_links \u2192 repo_sync",
        "```\u2192 fetch_files \u2192 ALFRED_PDF \u2192 clean_issues \u2192 clean_files",
        "```\u2192 issues_to_docs \u2192 files_to_docs \u2192 similarity \u2192 chunk_issues",
        "```\u2192 chunk_files \u2192 stats_issues \u2192 stats_files \u2192 validate_schemas",
        "```[+export] \u2192 issues \u2192 files \u2192 resolver \u2192 diag \u2192 with_images \u2192 ALFRED_IMG",
        "",
        "## Run_Single_Series (PowerShell, 12 macro-steps):",
        "```repo_sync \u2192 audit_config_submodules --fix \u2192 audit_config_submodules",
        "```\u2192 run_full_workflow(--skip-chunking) \u2192 export_parent(issues/resolver/diag/with_images)",
        "```\u2192 export_drivers(same 4 types) \u2192 ALFRED_images(all with_images files)",
        "```\u2192 export_files_v3(all repos) \u2192 files_coverage_gate \u2192 patch_pdf_descriptions",
        "```\u2192 validate_schemas \u2192 placeholder_gate \u2192 [upload parent + drivers]",
        "",
        "## Run_Issues_Pipeline (PowerShell, 3-5 steps):",
        "```clean_issues \u2192 issues_to_docs_v2 [\u2192 similarity] [\u2192 chunking]",
        "```\u2192 export_st_ready_issues",
    ])

    add_content_slide(prs, "Run_Full_Auto_Update_KB.ps1 \u2014 Batch Automation", [
        "## Purpose: Process ALL series + upload to KB in one command",
        "```.\\Run_Full_Auto_Update_KB.ps1 -RemoteUser \"abir.gharbi@st.com\"",
        "",
        "## What it does:",
        "\u2022 Step 1: Run full pipeline for all series (f4, h5, h7, u5, wl by default)",
        "\u2022 Step 2: Schema validation gate (blocks upload if fails)",
        "\u2022 Step 3: Upload each artifact type to its registered datasource ID",
        "",
        "## Built-in datasource registry:",
        "```f4: issues=28099, files=28103, resolver=28118, diagnostic=28122",
        "```h5: issues=28158, files=28163, resolver=28164, diagnostic=28165",
        "```h7: issues=19896, files=21824, resolver=20403, diagnostic=23768",
        "",
        "## Options:",
        "\u2022 -Series f4,h5 (subset) | -SkipIngestion | -SkipUpload | -ContinueOnError",
        "\u2022 Logs to: logs/auto_update_kb_<timestamp>.log",
        "\u2022 Run weekly via Task Scheduler or on-demand after firmware releases",
    ])

    add_content_slide(prs, "Batch Processing \u2014 All Series", [
        "## PowerShell batch script:",
        "",
        '```$series = @("config_c0", "config_f0", "config_f1", "config_f2",',
        '```            "config_f3", "config_f7", "config_g0", "config_h7rs")',
        "```foreach ($s in $series) {",
        '```    Write-Host "=== Processing $s ===" -ForegroundColor Cyan',
        '```    $env:STM32CUBE_CONFIG = "shared/config/$s.json"',
        "```    python -m pipeline.run_full_workflow --export-st-ready --continue-on-error",
        "```}",
        "",
        "## Key points:",
        "\u2022 Each iteration is INDEPENDENT (own config, own data/)",
        "\u2022 If one series fails, the others continue",
        "\u2022 Data files are named per repo \u2192 no collision",
        "\u2022 Duration: ~10-30 min per series (depends on issue/file count)",
        "\u2022 See also: pipeline_Automation/workflow/Run_Full_Auto_Update_KB.ps1",
    ])

    add_content_slide(prs, "Each Step Can Be Run Individually", [
        "## Ingestion:",
        "```python -m pipeline.ingestion.fetch_issues",
        "```python -m pipeline.ingestion.fetch_files",
        "",
        "## Cleaning:",
        "```python -m pipeline.cleaning.clean_issues",
        "```python -m pipeline.cleaning.clean_files",
        "",
        "## Enrichment:",
        "```python -m pipeline.enrichment.issues_to_docs_v2",
        "```python -m pipeline.enrichment.files_to_docs_v2",
        "",
        "## Delivery (by type):",
        "```python -m pipeline.delivery.export_st_ready_issues --repo STM32CubeH7",
        "```python -m pipeline.delivery.export_st_ready_files --repo STM32CubeH7",
        "```python -m pipeline.delivery.export_st_ready_diagnostic_cards --repo STM32CubeH7",
        "```python -m pipeline.delivery.export_st_ready_resolver_cases --repo STM32CubeH7",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 6 — PREPROCESSING DEEP DIVE
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "6. Preprocessing Deep Dive")

    add_content_slide(prs, "Stage 1: Ingestion \u2014 What Gets Collected", [
        "## GitHub API (token required, 5000 req/h):",
        "\u2022 Issues: title, body, labels, comments, timeline events, state.",
        "\u2022 PRs: links to commits, merge status, review status.",
        "\u2022 Commits: sha, message, files changed.",
        "\u2022 Links: issue \u2192 PR \u2192 commit chain for traceability.",
        "",
        "## Local clone (repo_sync_service):",
        "\u2022 Auto-clones missing repos from config repo_clone_urls.",
        "\u2022 Provides access to: README.md, Release_Notes.html, source code, PDFs.",
        "",
        "## File collection (file_collect_service):",
        "\u2022 README.md at root and key subdirectories.",
        "\u2022 Release Notes (HTML/MD) for changelog tracking.",
        "\u2022 PDFs from Documentation/ folder (is_documentation_pdf filter).",
        "\u2022 19 series have PDF documentation \u2192 242 figures extracted.",
    ])

    add_content_slide(prs, "Stage 2: Cleaning \u2014 Normalization", [
        "## What cleaning does:",
        "\u2022 Normalizes text (line breaks, backticks, whitespace).",
        "\u2022 Detects embedded images \u2192 marks them as [IMAGE ATTACHED].",
        "\u2022 Collects image URLs into image_urls array.",
        "\u2022 Structures content: Title + Body + Comments \u2192 clean_text field.",
        "\u2022 Preserves raw metadata (labels, dates, state).",
        "",
        "## What cleaning does NOT do:",
        "\u2022 \u2718 No classification (layer, board, component).",
        "\u2022 \u2718 No validity detection (is_valid).",
        "\u2022 \u2192 Those tasks are done by ENRICHMENT.",
        "",
        "## Output format:",
        "```{ repo, issue_number, title, state, labels, clean_text, image_urls, images_count }",
    ])

    add_content_slide(prs, "Stage 3: Enrichment V2 \u2014 Classification", [
        "## Heuristics applied by issues_to_docs_v2.py:",
        "",
        "\u2022 layer: HAL, BSP, Middleware, Application, CMSIS (labels + text patterns)",
        "\u2022 component: SPI, I2C, USB, CRYP... (regex on title + body)",
        "\u2022 board: NUCLEO-H743ZI, STM32H750B-DK... (board name patterns)",
        "\u2022 severity: critical, normal, low (labels + keywords)",
        "\u2022 issue_kind: bug, question, feature_request (labels)",
        "\u2022 is_valid: true if text > 100 chars + not bot/spam/duplicate",
        "\u2022 rescue: recovers technical false negatives from is_valid=false pool",
        "",
        "## Coverage targets:",
        "\u2022 layer \u2265 85% | component \u2265 70% | board \u2265 60% | validity \u2265 85%",
    ])

    add_content_slide(prs, "Stage 4: Similarity \u2014 Linking Related Issues", [
        "## How it works:",
        "\u2022 Build TF-IDF vectors from enriched issue documents.",
        "\u2022 Compute pairwise cosine similarity between all issues in a repo.",
        "\u2022 Threshold > 0.3 \u2192 add to related_issue_ids field.",
        "",
        "## Why it matters:",
        "\u2022 Enables retrieval system to surface connected problems.",
        "\u2022 User asks about issue A \u2192 system can propose related issues B, C.",
        "\u2022 Diagnostic cards reference related issues for context.",
        "",
        "## Output:",
        "```docs_issues_<repo>_v2_sim.json (same as _v2 + related_issue_ids field)",
    ])

    add_diagram_slide(prs, "Issue Preprocessing Chain", [
        ("RAW ISSUES", "GitHub JSON: title, body, labels, comments, timeline events"),
        ("CLEANED", "Normalized text, [IMAGE ATTACHED] tags, structured fields, image_urls"),
        ("ENRICHED", "layer, board, component, severity, is_valid, issue_kind, keywords"),
        ("SIMILARITY", "related_issue_ids added (TF-IDF cosine links)"),
        ("DELIVERY-READY", "st_ready_text, metadata, image_urls, resolver links"),
    ])

    add_diagram_slide(prs, "File Preprocessing Chain", [
        ("RAW FILES", "Collected from repo: README.md, Release_Notes.html, PDFs"),
        ("PDF EXTRACTION", "PyPDF text + PyMuPDF render + OpenCV figure detection"),
        ("CLEANED FILES", "Normalized content, figure crops stored, task files generated"),
        ("ENRICHED FILES", "file_type, board, component, category tagged + PDF descriptions injected"),
        ("DELIVERY-READY", "st_ready_text with [FIGURE_DESCRIPTIONS] blocks"),
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 7 — ALFRED VISION INTEGRATION
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "7. ALFRED Vision Integration")

    add_content_slide(prs, "\u26a0\ufe0f ALFRED Is Now INTEGRATED in the Pipeline", [
        "## Key point: ALFRED is NOT a separate manual step",
        "\u2022 --export-st-ready adds 6 steps (not just 4):",
        "  \u2192 issues, files, resolver, diag, issues_with_images, ALFRED Vision",
        "\u2022 ALFRED images is the LAST automatic step of the workflow (step 23)",
        "",
        "## Complete sequence:",
        "```Pipeline (17 steps) \u2192 Delivery (4 exports) \u2192 with_images \u2192 ALFRED Vision",
        "",
        "## What ALFRED images does automatically:",
        "\u2022 Scans by_series/*/issues_json/st_ready_issues_with_images_*.json",
        "\u2022 For each issue with images: downloads, sends to ALFRED, replaces text",
        "\u2022 [IMAGE ATTACHED] \u2192 [IMAGE DESCRIPTION] descriptive text",
        "\u2022 Modifies the file IN-PLACE (no separate output file)",
        "",
        "## \u2757 It\u2019s the with_images ENRICHED file that gets uploaded to KB",
        "\u2022 NOT the plain st_ready_issues file (that one has no image context)",
    ])

    add_content_slide(prs, "ALFRED \u2014 What It Is and Its Two Roles", [
        "## What is ALFRED?",
        "\u2022 ST\u2019s internal Vision AI API (api-ai-bridge.st.com).",
        "\u2022 Client: mdrf_stgithub_analyzer_client.",
        "\u2022 Analyzes images and generates structured textual descriptions.",
        "",
        "## Role A: PDF Figure Enrichment (Step 7 \u2014 BEFORE cleaning)",
        "\u2022 Input: Cropped figure PNGs from data/pdf_figures/<repo>/.",
        "\u2022 Process: ALFRED describes each diagram/figure in technical context.",
        "\u2022 Output: data/pdf_image_descriptions.json (242 descriptions, 19 series).",
        "\u2022 Impact: PDF figures become searchable via [FIGURE_DESCRIPTIONS] blocks.",
        "",
        "## Role B: Issue Image Enrichment (Step 23 \u2014 AFTER delivery)",
        "\u2022 Input: st_ready_issues_with_images_*.json containing image_urls.",
        "\u2022 Process: ALFRED analyzes each screenshot from GitHub issues.",
        "\u2022 Output: [IMAGE ATTACHED] \u2192 [IMAGE DESCRIPTION] <text>. In-place modification.",
        "\u2022 Impact: screenshots become searchable by the RAG system.",
    ])

    add_content_slide(prs, "ALFRED \u2014 Integration Timing (Key Insight)", [
        "## ALFRED operates at TWO different points in the pipeline:",
        "",
        "## Path A (PDF figures \u2014 Step 7, BEFORE cleaning):",
        "```[Ingestion] \u2192 [PDF render+crop] \u2192 ALFRED \u2192 pdf_image_descriptions.json",
        "```                                                   \u2193",
        "```[Cleaning \u2192 Enrichment] \u2192 files_to_docs_v2 \u2192 inject descriptions",
        "```                                                   \u2193",
        "```[Delivery] \u2192 st_ready_files_v3.json (with FIGURE_DESCRIPTIONS)",
        "",
        "## Path B (Issue images \u2014 Step 23, AFTER delivery):",
        "```[Delivery] \u2192 export_issues_with_images \u2192 download screenshots \u2192 ALFRED",
        "```                                                                   \u2193",
        "```          [IMAGE ATTACHED] \u2192 [IMAGE DESCRIPTION] (in-place modification)",
        "",
        "## Why two different timings?",
        "\u2022 Path A: descriptions needed BEFORE enrichment can inject them into docs.",
        "\u2022 Path B: operates on FINAL delivery JSON (needs structured metadata first).",
        "\u2022 Same API, same client, different integration patterns.",
    ])

    add_content_slide(prs, "ALFRED \u2014 PDF Figure Extraction Pipeline", [
        "## Step-by-step (pdf_figure_service.py):",
        "",
        "```\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510   \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510   \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510   \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510   \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510",
        "```\u2502  PDF    \u2502\u2500\u25b6\u2502 PyMuPDF \u2502\u2500\u25b6\u2502 OpenCV  \u2502\u2500\u25b6\u2502 ALFRED  \u2502\u2500\u25b6\u2502 Inject   \u2502",
        "```\u2502  docs   \u2502   \u2502 render  \u2502   \u2502 crop    \u2502   \u2502 Vision  \u2502   \u2502 into docs\u2502",
        "```\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518",
        "",
        "## Functions called:",
        "\u2022 extract_pdf_multimodal() \u2014 entry point for a repo",
        "\u2022 render_pdf_pages() \u2014 PyMuPDF converts each page to 150 DPI PNG",
        "\u2022 detect_candidate_figure_regions() \u2014 OpenCV contour + area filter",
        "\u2022 crop_figures_from_page() \u2014 isolate individual figures as PNG",
        "\u2022 build_pdf_figure_tasks() \u2014 generate JSONL task file for ALFRED",
        "\u2022 inject_figure_descriptions_into_pages() \u2014 merge into docs",
        "",
        "## Storage:",
        "\u2022 data/pdf_pages/<repo>/*.png | data/pdf_figures/<repo>/*.png",
        "\u2022 data/pdf_image_tasks_<repo>.jsonl | data/pdf_image_descriptions.json",
    ])

    add_content_slide(prs, "ALFRED \u2014 Concrete Examples (H7)", [
        "## Example 1 \u2014 Issue #335 (STM32CubeH7)",
        "\u2022 Topic: Warning observed with -Wcast-align flag during compilation.",
        "\u2022 Before: Screenshot attached but invisible to text search.",
        "\u2022 After: ALFRED describes Eclipse Tool Settings panel \u2192 flags searchable.",
        "",
        "## Example 2 \u2014 Issue #333 (STM32CubeH7)",
        "\u2022 Topic: Fix compile-time warnings without removing compiler flags.",
        "\u2022 After: ALFRED extracts \u2018About STM32CubeIDE\u2019 dialog \u2192 version traceable.",
        "",
        "## Example 3 \u2014 PDF Figure (H7 GettingStarted.pdf, page 3)",
        "\u2022 Before: Figure 1 is a raster image in a PDF, invisible to retrieval.",
        "\u2022 After: ALFRED describes the firmware component stack diagram.",
        "\u2022 st_ready_text now contains the architecture description as searchable text.",
        "",
        "## Key message: ALFRED enriches for retrieval AND for audit metadata.",
    ])

    add_content_slide(prs, "ALFRED \u2014 Manual Commands", [
        "## Issue image enrichment (automatic with --export-st-ready):",
        "```python pipeline_Automation/alfred/enrich_json_images_with_alfred.py \\",
        "```  --input <st_ready_issues_with_images_*.json> --inplace",
        "",
        "## PDF figure enrichment:",
        "```python pipeline_Automation/alfred/enrich_pdf_figures_with_alfred.py \\",
        "```  --repo STM32CubeH7",
        "",
        "## Options:",
        "\u2022 --use-proxy: route through proxy (NOT needed on ST network)",
        "\u2022 --max-records N: limit number of records processed",
        "\u2022 --strip-analyses: remove image_analyses array (smaller file)",
        "\u2022 --no-replace-text: keep [IMAGE ATTACHED] alongside description",
        "",
        "## After PDF enrichment, re-run to propagate:",
        "```python -m pipeline.enrichment.files_to_docs_v2",
        "```python -m pipeline.delivery.export_st_ready_files --repo <Repo>",
    ])

    add_table_slide(prs, "ALFRED Coverage Across Series",
        ["Series", "Issues w/ Images", "Total Images", "ALFRED Success", "PDF Figures"],
        [
            ["H7", "53", "98", "97/98", "10"],
            ["F4", "34", "62", "61/62", "11"],
            ["WL", "23", "48", "48/48", "11"],
            ["F7", "20", "26", "26/26", "11"],
            ["C0", "3", "5", "5/5", "12"],
            ["U5", "6", "\u2014", "OK", "14"],
            ["H5", "3", "\u2014", "OK", "13"],
            ["WB", "\u2014", "\u2014", "\u2014", "22"],
            ["G0", "yes", "\u2014", "OK", "13"],
            ["H7RS", "\u2014", "\u2014", "\u2014", "25"],
            ["N6", "\u2014", "\u2014", "\u2014", "15"],
            ["F0/F1/F2/F3", "few", "\u2014", "OK", "varies"],
            ["TOTAL (19 series)", "", "", ">99%", "242 figures"],
        ]
    )

    add_horizontal_flow_slide(prs, "ALFRED Vision \u2014 Two Paths (Visual Diagram)", [
        ("PATH A\nPDF Figures\n(Step 7)", [
            ("PDF docs\nin GitHub_repos/", ST_LIGHT_BLUE),
            ("PyMuPDF\nrender pages", ST_GREEN),
            ("OpenCV\ncrop figures", ST_GREEN),
            ("ALFRED API\ndescribe", ST_RED),
            ("Inject into\nfiles_to_docs", ST_PURPLE),
        ]),
        ("PATH B\nIssue Images\n(Step 23)", [
            ("with_images\nJSON", ST_LIGHT_BLUE),
            ("Download\nscreenshots", ST_GREEN),
            ("ALFRED API\ndescribe", ST_RED),
            ("In-place\nreplace text", ST_PURPLE),
        ]),
        ("SHARED\nINFRA", [
            ("api-ai-bridge\n.st.com", ST_ORANGE),
            ("Client:\nmdrf_stgithub", ST_ORANGE),
            ("Rate: ~20 req\nbefore throttle", ST_ORANGE),
            ("Retry: 5s\nBackoff: 30s", ST_ORANGE),
        ]),
        ("OUTPUT", [
            ("pdf_image\n_descriptions.json", ST_BLUE),
            ("st_ready_files\n_v3.json", ST_BLUE),
            ("st_ready_issues\n_with_images.json", ST_BLUE),
        ]),
    ])

    add_horizontal_flow_slide(prs, "Full Pipeline Flow \u2014 23 Steps (Visual Diagram)", [
        ("INGESTION\nSteps 1-6", [
            ("fetch\nissues", ST_LIGHT_BLUE),
            ("fetch\nPRs", ST_LIGHT_BLUE),
            ("fetch\ncommits", ST_LIGHT_BLUE),
            ("fetch\nlinks", ST_LIGHT_BLUE),
            ("repo\nsync", ST_LIGHT_BLUE),
            ("fetch\nfiles", ST_LIGHT_BLUE),
        ]),
        ("ALFRED PDF\nStep 7", [
            ("render\npages", ST_RED),
            ("crop\nfigures", ST_RED),
            ("ALFRED\ndescribe", ST_RED),
        ]),
        ("CLEANING\nSteps 8-10", [
            ("clean\nissues", ST_GREEN),
            ("clean\nfiles", ST_GREEN),
            ("clean\nfiles v3", ST_GREEN),
        ]),
        ("ENRICHMENT\nSteps 11-13", [
            ("issues_to\n_docs_v2", ST_ORANGE),
            ("files_to\n_docs_v2", ST_ORANGE),
            ("similarity\nTF-IDF", ST_ORANGE),
        ]),
        ("EVAL\nSteps 14-18", [
            ("chunk\nissues", ST_PURPLE),
            ("chunk\nfiles", ST_PURPLE),
            ("stats\nissues", ST_PURPLE),
            ("stats\nfiles", ST_PURPLE),
            ("validate\nschemas", ST_PURPLE),
        ]),
        ("DELIVERY\nSteps 19-23", [
            ("issues", ST_BLUE),
            ("files", ST_BLUE),
            ("resolver", ST_BLUE),
            ("diag", ST_BLUE),
            ("with_imgs\n+ALFRED", ST_BLUE),
        ]),
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 8 — DELIVERY & UPLOAD
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "8. Delivery & Upload to KB")

    add_content_slide(prs, "Four Artifact Types \u2014 ST-Ready JSON", [
        "## 1. Issues (st_ready_issues_*.json)",
        "\u2022 Structured support cards: title, body, context, layer, severity, related issues.",
        "",
        "## 2. Files (st_ready_files_*_v3.json)",
        "\u2022 Documentation cards: README, Release Notes, PDFs with [FIGURE_DESCRIPTIONS].",
        "",
        "## 3. Resolver Cases (st_ready_resolver_cases_*.json)",
        "\u2022 Cause \u2192 Action pairs from closed issues with CONFIRMED fixes.",
        "\u2022 Links: Issue \u2192 PR \u2192 Commit chain for full traceability.",
        "\u2022 \u26a0\ufe0f May be empty ([]) for series with no documented fix \u2014 this is NORMAL.",
        "",
        "## 4. Diagnostic Cards (st_ready_diagnostic_cards_*.json)",
        "\u2022 Structured troubleshooting: symptoms, root cause, resolution.",
        "\u2022 Includes query_aliases, keywords, and evidence_refs for retrieval.",
        "\u2022 \u2260 Resolver Cases: diag describes the PROBLEM, resolver describes the FIX.",
    ])

    add_content_slide(prs, "Delivery Output Structure", [
        "```datasets/07_delivery/st_ready/by_series/",
        "```\u251c\u2500\u2500 stm32cubeh7/",
        "```\u2502   \u251c\u2500\u2500 issues_json/",
        "```\u2502   \u2502   \u251c\u2500\u2500 st_ready_issues_stm32cubeh7.json",
        "```\u2502   \u2502   \u2514\u2500\u2500 st_ready_issues_with_images_stm32cubeh7.json  (+ALFRED)",
        "```\u2502   \u251c\u2500\u2500 files_json/",
        "```\u2502   \u2502   \u2514\u2500\u2500 st_ready_files_stm32cubeh7_v3.json  (with PDF figures)",
        "```\u2502   \u251c\u2500\u2500 resolver_cases_json/",
        "```\u2502   \u2502   \u2514\u2500\u2500 st_ready_resolver_cases_stm32cubeh7.json",
        "```\u2502   \u251c\u2500\u2500 diagnostic_cards_json/",
        "```\u2502   \u2502   \u2514\u2500\u2500 st_ready_diagnostic_cards_stm32cubeh7.json",
        "```\u2502   \u251c\u2500\u2500 drivers/  (10+ sub-repo artifacts)",
        "```\u2502   \u2514\u2500\u2500 upload_datasource_ids_stm32cubeh7.json",
    ])

    add_content_slide(prs, "Upload to KB #793 \u2014 Commands", [
        "## Script: pipeline_Automation/upload/Add_Data_Source_Files.py",
        "",
        "## Create new datasource:",
        "```python Add_Data_Source_Files.py --kb 793 --operation new \\",
        '```  --datasource-name "STM32H7 Issues" --remote-user "x@st.com" \\',
        "```  --processor JSON --processor-params \"base64:$b64\" --json-split-size 1000 \\",
        "```  --files <path.json>",
        "",
        "## Add to existing datasource:",
        "```python Add_Data_Source_Files.py --kb 793 --operation add \\",
        "```  --datasource-id 24406 --json-split-size 1000 --files <path.json>",
        "",
        "## Upload all drivers (batch):",
        "```.\\pipeline_Automation\\upload\\Upload_All_Drivers.ps1",
        "  \u2192 Traverses by_series/*/drivers/, uploads each artifact, throttle 5s",
        "",
        "## Verify KB:",
        "```python pipeline_Automation/upload/Get_Persona_KBs.py",
    ])

    add_content_slide(prs, "\u2757 Workshop Recommended Command", [
        "## One-liner for a full series (pipeline + upload):",
        "```.\\pipeline_Automation\\workflow\\Run_Single_Series_Full_Pipeline_And_Upload.ps1 -Series H7",
        "",
        "## What it orchestrates:",
        "\u2022 Prepares parent + drivers artifacts (full pipeline)",
        "\u2022 Local schema validation before upload",
        "\u2022 Upload ALL artifact types (issues, files, drivers, diag, resolver)",
        "\u2022 Automatic datasource ID saving for idempotent reruns",
        "",
        "## Key output file:",
        "```datasets/07_delivery/st_ready/by_series/stm32cubeh7/upload_datasource_ids_stm32cubeh7.json",
        "",
        "## \u26a0\ufe0f CRITICAL: upload the with_images ALFRED-ENRICHED file, NOT plain issues!",
        "\u2022 The enriched file is what gives the KB image context for retrieval",
        "\u2022 Upload script already does this automatically \u2014 do NOT override manually",
    ])

    add_content_slide(prs, "KB Organization \u2014 1 Datasource per Series \u00d7 Type", [
        "## Structure in KB #793:",
        "\u2022 STM32H7 Issues (#24406) \u2014 8 files, 359 docs",
        "\u2022 STM32H7 Files (#29041) \u2014 16 files, 5327 docs",
        "\u2022 STM32H7 Diagnostic Cards (#24408)",
        "\u2022 STM32H7 Resolver Cases (#24410)",
        "\u2022 STM32F4 Issues (#28099) \u2014 7 files, 1917 docs",
        "\u2022 STM32F4 Files (#29042) \u2014 21 files, 5948 docs",
        "\u2022 ... (same pattern for each series)",
        "",
        "## Rule: drivers go into the SAME datasource as parent",
        "\u2022 st_ready_issues_stm32h7xx-hal-driver.json \u2192 DS \"STM32H7 Issues\"",
        "\u2022 st_ready_files_cmsis_device_h7.json \u2192 DS \"STM32H7 Files\"",
        "",
        "## Saved for idempotent uploads:",
        "```upload_datasource_ids_<serie>.json",
    ])

    add_table_slide(prs, "Processor Params \u2014 Upload Configuration",
        ["Artifact Type", "rootTagPath", "Label Template", "ExternalURL Pattern"],
        [
            ["Issues", "issues", "{{repo}} issue #{{issue_number}} - {{issue_title}}", "github.com/.../issues/{{issue_number}}"],
            ["Files", "files", "{{repo}} {{file_type}} - {{path}}", "github.com/.../{{root_ref}}/{{path_url}}"],
            ["Resolver Cases", "resolver_cases", "{{label}}", "github.com/.../issues/{{issue_number}}"],
            ["Diagnostic Cards", "\u2014", "{{label}}", "github.com/.../issues/{{evidence_refs[0].id}}"],
        ]
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 9 — QUALITY GATES & VALIDATION
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "9. Quality Gates & Validation")

    add_content_slide(prs, "Quality Gates \u2014 Before Upload", [
        "## Gate 1: Schema Validation",
        "\u2022 python -m pipeline.evaluation.validate_schemas",
        "\u2022 Verifies all JSON outputs conform to shared/schemas/*.json contracts.",
        "",
        "## Gate 2: Placeholder Check",
        "\u2022 Scans for unresolved [IMAGE ATTACHED] or [FIGURE... markers.",
        "\u2022 PlaceholderPolicy=Fail blocks upload; =Warn allows with report.",
        "",
        "## Gate 3: Summary Coherence",
        "\u2022 summary_*.json files report counts; must match payload size.",
        "",
        "## Gate 4: Smoke Test (post-upload)",
        "\u2022 Ask 3 representative questions \u2192 verify answers cite correct sources.",
        "\u2022 KB-first behavior validated (ALFRED fallback only when KB has no match).",
    ])

    add_content_slide(prs, "Evaluation Commands", [
        "## Stats issues:",
        "```python -m pipeline.evaluation.test_stats_issues_v2",
        "  \u2192 Issue count, layer/board/component coverage, distribution",
        "",
        "## Stats files:",
        "```python -m pipeline.evaluation.test_stats_files_v2",
        "  \u2192 File count, types, sizes, coverage",
        "",
        "## Schema validation:",
        "```python -m pipeline.evaluation.validate_schemas",
        "  \u2192 Checks JSON against shared/schemas/ contracts",
        "",
        "## Full evaluation report (charts + Excel):",
        "```python -m pipeline.evaluation.generate_evaluation_report --all",
        "  \u2192 PNG + XLSX in evaluation_report/",
        "",
        "## TF-IDF retrieval test:",
        "```python -m pipeline.evaluation.test_tfidf_search_issues_v2",
    ])

    add_table_slide(prs, "Go / No-Go Decision Matrix",
        ["Gate", "Go Criterion", "Action if No-Go"],
        [
            ["Schema validation", "100% JSON valid", "Fix export or schema definition"],
            ["Placeholder gate", "0 unresolved in strict mode", "Re-run ALFRED or targeted patch"],
            ["Upload", "No blocking errors", "Retry with reused datasource IDs"],
            ["Smoke test", "3 coherent, sourced answers", "Fix KB or tool description"],
            ["Fallback behavior", "KB-first, then ALFRED", "Make tool description more restrictive"],
        ]
    )

    add_table_slide(prs, "KPIs to Monitor",
        ["KPI", "Measurement", "Decision"],
        [
            ["Ingestion completeness", "% non-empty issues/files", "Is input material sufficient?"],
            ["Enrichment coverage", "% docs with layer/component/board", "Does preprocessing add signal?"],
            ["ALFRED success rate", "described / detected images", "Is visual content exploitable?"],
            ["Placeholder rate", "unresolved / total figures", "Can we upload in strict mode?"],
            ["Quality Index", "Score on test questions", "Is final answer quality acceptable?"],
        ]
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 10 — VALUE PROPOSITION
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "10. Value Proposition & Impact")

    add_table_slide(prs, "Before vs. After \u2014 Tangible Value",
        ["Before (without pipeline)", "After (with pipeline)", "Impact"],
        [
            ["Raw long issue text", "Structured st_ready_text", "More targeted answers"],
            ["Image attached, not interpreted", "[IMAGE DESCRIPTION] indexed", "Screenshots exploitable by RAG"],
            ["Isolated source file", "Context: repo/path/type enriched", "Technical traceability"],
            ["Scattered comments", "Diagnostic card + resolver case", "Cause/action extractable"],
            ["Data organized per repo", "by_series/ + drivers/ routed", "Maintainable KB uploads"],
        ]
    )

    add_table_slide(prs, "Value Dimensions",
        ["Dimension", "Description", "Evidence"],
        [
            ["Efficiency", "One-command processing for entire series", "23 steps automated, batch multi-series"],
            ["Traceability", "Every answer links to a source", "github_url, evidence_refs in cards"],
            ["Robustness", "Quality gates prevent bad data reaching KB", "Schema validation + placeholder gate"],
            ["Scalability", "Config-driven, no code changes", "25 series configured, 200+ sub-repos"],
            ["Maintainability", "Modular stages, clear interfaces", "Each stage independently testable"],
            ["Explainability", "Diagnostic cards explain cause+resolution", "QI = 94/100 on H7"],
        ]
    )

    add_content_slide(prs, "Why This Matters for STMicroelectronics", [
        "## Business Impact",
        "\u2022 Reduces time-to-answer for technical support queries.",
        "\u2022 Enables non-expert users to get expert-level guidance from AI.",
        "\u2022 Makes visual information (screenshots, PDF figures) exploitable.",
        "",
        "## Competitive Advantages",
        "\u2022 End-to-end automation: no manual curation bottleneck.",
        "\u2022 Multi-modal: text + images + PDF figures all enriched and indexed.",
        "\u2022 Production-hardened: gates, retry logic, idempotent uploads.",
        "\u2022 Open architecture: modular Python, PowerShell, standard JSON.",
        "",
        "## Measured Results",
        "\u2022 +39% relevance improvement over generic LLM.",
        "\u2022 Quality Index: 94/100 on pilot H7 with Diagnostic Cards.",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 11 — OPERATIONAL GUIDE
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "11. Operational Guide")

    add_content_slide(prs, "Best Practices", [
        "## Execution",
        "\u2022 Always use --continue-on-error (one empty sub-repo shouldn\u2019t block).",
        "\u2022 Use --skip-ingestion to reprocess without re-downloading.",
        "\u2022 Verify summary_*.json before upload (coherence of counts).",
        "",
        "## Upload",
        "\u2022 Do NOT upload empty files (resolver_cases = [] is normal).",
        "\u2022 1 datasource = 1 series + 1 artifact type.",
        "\u2022 Drivers go into the same datasource as the parent repo.",
        "",
        "## Git",
        "\u2022 NEVER commit data/*.json (> 100 MB \u2192 push rejected).",
        "\u2022 datasets/07_delivery/ IS committed (< 50 MB, the deliverable).",
        "",
        "## ALFRED",
        "\u2022 No --use-proxy needed (direct access from ST network).",
        "\u2022 Verify 0 [IMAGE DESCRIPTION UNAVAILABLE] after enrichment.",
    ])

    add_table_slide(prs, "Troubleshooting \u2014 Common Errors",
        ["Error", "Cause", "Solution"],
        [
            ["FileNotFoundError: with_images", "Series has no images", "Normal \u2014 skip Alfred"],
            ["empty JSON arrays", "Resolver cases empty", "Normal \u2014 no confirmed fixes"],
            ["skipped_existing_files", "File already in DS", "Delete old or --operation new"],
            ["GitHub file size > 100MB", "data/*.json in git", "Check .gitignore"],
            ["rate limit GitHub", "Too many API calls", "Wait 1h or --skip-ingestion"],
            ["Enrichment 0% for BSP", "Sub-repo has few issues", "Normal \u2014 aggregated in parent"],
            ["Auth precheck 404", "API rate-limited", "throttle 5s + retry 2\u00d730s"],
        ]
    )

    add_content_slide(prs, "Troubleshooting \u2014 Detailed (1/2)", [
        '## "FileNotFoundError: st_ready_issues_with_images_*.json"',
        "\u2022 The with_images file is ONLY generated if issues have [IMAGE ATTACHED].",
        "\u2022 Sub-repos BSP/CMSIS often have ZERO images.",
        "\u2022 \u2192 The workflow automatically skips series without images. This is NORMAL.",
        "",
        '## "All selected files are empty JSON arrays"',
        "\u2022 resolver_cases.json contains [] because no issue has a documented fix.",
        "\u2022 Diagnostic cards \u2260 Resolver cases: diag = problem, resolver = fix.",
        "\u2022 \u2192 Normal. Do NOT force upload of empty arrays.",
        "",
        '## "skipped_existing_files: [file.json]"',
        "\u2022 File already uploaded to this datasource (API refuses duplicates by name).",
        "\u2022 Fix 1: Delete old file in KB Management, then re-upload.",
        "\u2022 Fix 2: Rename with suffix _pdf_enriched before upload.",
        "```Copy-Item st_ready_files_*.json st_ready_files_*_pdf_enriched.json",
    ])

    add_content_slide(prs, "Troubleshooting \u2014 Detailed (2/2)", [
        '## "File exceeds GitHub file size limit of 100.00 MB"',
        "\u2022 data/ files are VERY large (chunks_files_stm32cubec0_v2.json = 114 MB!).",
        "\u2022 Fix: .gitignore must contain: data/raw_*, data/clean_*, data/docs_*, data/chunks_*",
        "\u2022 If already committed: git rm --cached data/<file>.json + amend commit.",
        "",
        '## "rate limit" GitHub API',
        "\u2022 GitHub: 5000 req/h WITH token, only 60/h WITHOUT.",
        "\u2022 Pipeline makes many calls (issues + all comments + PRs per repo).",
        "\u2022 Fix: Verify $env:GITHUB_TOKEN is set.",
        "\u2022 Fix: Increase issues_sleep in config (0.2 \u2192 0.5).",
        "\u2022 Fix: Use --skip-ingestion if raw files already exist.",
        "",
        '## "Auth precheck failed. HTTP status=404" (nginx 404)',
        "\u2022 api-ai-bridge.st.com rate-limits after ~20 fast requests.",
        "\u2022 Fix already in Upload_All_Drivers.ps1:",
        "  $uploadDelaySec=5, $retryCount=2, $retryDelaySec=30.",
        "",
        '## "Proxy 502 Bad Gateway"',
        "\u2022 The proxy 185.46.212.88 is sometimes down.",
        "\u2022 Fix: Run WITHOUT --use-proxy (direct access from ST network).",
        "",
        '## "Enrichment 0% for a BSP sub-repo"',
        "\u2022 BSP/CMSIS sub-repos have very few issues (often 0-5). Normal.",
        "\u2022 Content is aggregated in the parent series repo.",
        "",
        '## "argparse error / sys.argv pollution"',
        "\u2022 When calling individual modules from PowerShell, sys.argv may carry stale args.",
        "\u2022 Fix: pipeline modules use parse_known_args() not parse_args().",
    ])

    add_table_slide(prs, "Incidents \u2192 Systematic Improvements",
        ["Incident", "Root Cause", "Fix", "Generalized"],
        [
            ["ALFRED placeholders", "Truncated figure IDs", "PlaceholderPolicy gate", "Gate before every upload"],
            ["PDF figures not resolved", "Timing: after delivery", "Patch + re-injection", "Step 7 + patch script"],
            ["Chart crash (pie=0)", "Zero values in plot", "_safe_pie() wrapper", "All reports handle empty"],
            ["Upload blocked", "API rejects duplicates", "Reuse saved DS IDs", "Idempotent batch workflows"],
            ["API timeouts", "Rate limiting", "Warning + separate validation", "Demo-safe"],
        ]
    )

    add_content_slide(prs, "Risks & Mitigations", [
        "\u2022 API timeout \u2192 Retries + targeted re-run (--skip-ingestion).",
        "\u2022 Image/PDF not described \u2192 ALFRED re-run + PlaceholderPolicy gate.",
        "\u2022 Datasource exists \u2192 Reuse saved IDs or targeted deletion.",
        "\u2022 Series with few issues \u2192 Restrictive ALFRED fallback in persona.",
        "\u2022 Retrieval noise \u2192 Calibrate Hybrid threshold/doc count.",
        "",
        "## Design philosophy: Fail Forward",
        "\u2022 Every incident becomes a permanent, generalized improvement.",
        "\u2022 New series automatically benefits from all historical fixes.",
        "\u2022 PlaceholderPolicy (Fail/Warn/Off) available in every workflow script.",
        "\u2022 --continue-on-error ensures one failure doesn\u2019t block the series.",
    ])

    add_content_slide(prs, "Checklist \u2014 Adding a New Series", [
        "\u25a1 1. Create shared/config/config_<serie>.json (repos + clone_urls)",
        "\u25a1 2. Add mapping in pipeline/delivery/delivery_paths.py",
        "\u25a1 3. Run full pipeline:",
        '```   $env:STM32CUBE_CONFIG = "shared/config/config_xx.json"',
        "```   python -m pipeline.run_full_workflow --export-st-ready --continue-on-error",
        "\u25a1 4. Verify by_series/<serie>/: issues, files, diag, resolver, drivers/",
        "\u25a1 5. ALFRED PDF figures (if pdf_image_tasks non-empty):",
        "```   python pipeline_Automation/alfred/enrich_pdf_figures_with_alfred.py --repo <Repo>",
        "\u25a1 6. Upload parent repo (new datasource \u00d7 4 types)",
        "\u25a1 7. Upload issues with_images enriched by ALFRED",
        "\u25a1 8. Upload PDF-enriched files (suffix _pdf_enriched if needed)",
        "\u25a1 9. Update Upload_All_Drivers.ps1 + upload_alfred_issues_all_series.py",
        "\u25a1 10. Run Upload_All_Drivers.ps1 for driver sub-repos",
        "\u25a1 11. Verify: python pipeline_Automation/upload/Get_Persona_KBs.py",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 12 — LIVE DEMO
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "12. Live Demo & Hands-On")

    add_content_slide(prs, "Demo Script \u2014 5 Minutes", [
        "## Step 1: Prepare a series",
        "```.\\pipeline_Automation\\workflow\\Run_Single_Series_Full_Pipeline_And_Upload.ps1 -Series WB -Mode Prepare -PlaceholderPolicy Warn",
        "",
        "## Step 2: Show generated artifacts",
        "\u2022 by_series/stm32cubewb/issues_json/, files_json/, diagnostic_cards_json/",
        "",
        "## Step 3: Show a quality gate",
        "\u2022 validate_schemas output, placeholder report, summary_*.json counts",
        "",
        "## Step 4: Upload (or show saved datasource IDs)",
        "\u2022 upload_datasource_ids_stm32cubewb.json",
        "",
        "## Step 5: Ask a technical question in ST ChatGPT",
        "\u2022 Show the answer + source citation from the Knowledge Base",
    ])

    add_content_slide(prs, "High-Stakes Presentation Checklist", [
        "## Preparation (day before):",
        "\u2022 Run full Prepare on the target series \u2014 artifacts must be ready.",
        "\u2022 Generate summary_*.json and validate schemas.",
        "\u2022 Prepare 3 before/after examples (raw issue \u2192 st_ready card).",
        "\u2022 Prepare 1 failure case with mitigation (shows transparency).",
        "",
        "## During the demo:",
        "\u2022 Start with the single-command workflow.",
        "\u2022 Show file structure and explain what each artifact contains.",
        "\u2022 Ask a real question in ST ChatGPT and show the sourced answer.",
        "\u2022 Show a quality gate catching a problem (placeholder report).",
        "",
        "## Safety net:",
        "\u2022 Use -PlaceholderPolicy Warn for known non-critical series.",
        "\u2022 Have upload_datasource_ids pre-saved to avoid live API dependency.",
    ])

    add_content_slide(prs, "Automation Scripts Summary", [
        "## Full pipeline (single series):",
        "```python -m pipeline.run_full_workflow --export-st-ready --continue-on-error",
        "",
        "## Full pipeline + upload (orchestrated):",
        "```.\\pipeline_Automation\\workflow\\Run_Single_Series_Full_Pipeline_And_Upload.ps1 -Series H7",
        "",
        "## Upload drivers (all series):",
        "```.\\pipeline_Automation\\upload\\Upload_All_Drivers.ps1",
        "",
        "## Upload ALFRED-enriched issues (all series):",
        "```python pipeline_Automation/upload/upload_alfred_issues_all_series.py",
        "",
        "## Batch all series:",
        "```.\\pipeline_Automation\\workflow\\Run_Full_Auto_Update_KB.ps1",
        "",
        "## Verify KB:",
        "```python pipeline_Automation/upload/Get_Persona_KBs.py",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 13 — CONCLUSION
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "13. Conclusion")

    add_content_slide(prs, "Key Takeaways", [
        "## Technical Value",
        "\u2022 Industrialized transformation of heterogeneous GitHub data into structured KB artifacts.",
        "\u2022 Multi-modal: text, images, and PDF figures all made searchable.",
        "",
        "## Quality Value",
        "\u2022 Every artifact passes through validation, gates, and reports.",
        "\u2022 Production-grade: strict mode ensures no garbage reaches the KB.",
        "",
        "## Operational Value",
        "\u2022 Incidents were not patched ad-hoc \u2014 they became permanent controls.",
        "\u2022 Adding a new series = 1 config + 1 command. No code changes.",
        "",
        "## Business Value",
        "\u2022 +39% relevance improvement over generic LLM.",
        "\u2022 Quality Index: 94/100 on pilot H7 with Diagnostic Cards.",
    ])

    add_content_slide(prs, "Closing Message", [
        "",
        "",
        "## This pipeline makes STM32 knowledge:",
        "",
        "\u2022   MORE SEARCHABLE \u2014 text, images, and figures all indexed",
        "",
        "\u2022   MORE TRACEABLE \u2014 every answer links to a verified source",
        "",
        "\u2022   MORE MAINTAINABLE \u2014 config-driven, modular, self-hardening",
        "",
        "",
        "## For ST ChatGPT and the engineers who depend on it.",
        "",
        "## Config \u2192 Pipeline (23 steps) \u2192 ALFRED \u2192 Upload \u2192 Verification",
    ])

    add_title_slide(
        prs,
        "Thank You",
        "Questions?"
    )

    # ══════════════════════════════════════════════════════════════════════
    # SAVE
    # ══════════════════════════════════════════════════════════════════════

    output_path = Path(__file__).parent / "Atelier_Pratique_Pipeline_STM32Cube.pptx"
    try:
        prs.save(str(output_path))
    except PermissionError:
        output_path = output_path.with_name("Atelier_Pratique_Pipeline_STM32Cube_updated.pptx")
        prs.save(str(output_path))
        print("Warning: original PPTX is locked; saved an updated copy instead.")
    print(f"\u2713 Presentation saved: {output_path}")


if __name__ == "__main__":
    main()
