"""
Generate a PowerPoint presentation for the STM32Cube Pipeline Workshop.
Run: python docs/generate_workshop_pptx_v2.py
Output: docs/Atelier_Pratique_Pipeline_STM32Cube.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Cm, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path

# Colors
ST_BLUE = RGBColor(0x03, 0x23, 0x4B)
ST_LIGHT_BLUE = RGBColor(0x3C, 0xB4, 0xE6)
ST_GREEN = RGBColor(0x4C, 0xAF, 0x50)
ST_ORANGE = RGBColor(0xFF, 0x98, 0x00)
ST_RED = RGBColor(0xF4, 0x43, 0x36)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF5, 0xF5, 0xF5)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)


def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title_slide(prs, title, subtitle=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
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
    """Add a slide with colored boxes representing pipeline stages."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)

    # Title
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

    # Draw boxes
    colors = [ST_LIGHT_BLUE, ST_GREEN, ST_ORANGE, RGBColor(0x9C, 0x27, 0xB0), ST_RED, RGBColor(0x00, 0x96, 0x88), ST_BLUE]
    start_y = 1.2
    box_h = 0.7
    gap = 0.15

    for i, (label, desc) in enumerate(boxes):
        y = start_y + i * (box_h + gap)
        color = colors[i % len(colors)]

        # Box
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

        # Description
        txBox = slide.shapes.add_textbox(Inches(3.2), Inches(y), Inches(6.5), Inches(box_h))
        tf2 = txBox.text_frame
        tf2.vertical_anchor = MSO_ANCHOR.MIDDLE
        p2 = tf2.paragraphs[0]
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = DARK_GRAY

        # Arrow between boxes
        if i < len(boxes) - 1:
            arrow_y = y + box_h
            shape_arrow = slide.shapes.add_shape(
                MSO_SHAPE.DOWN_ARROW, Inches(1.6), Inches(arrow_y), Inches(0.3), Inches(gap)
            )
            shape_arrow.fill.solid()
            shape_arrow.fill.fore_color.rgb = LIGHT_GRAY
            shape_arrow.line.fill.background()

    return slide


def add_table_slide(prs, title, headers, rows):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, WHITE)

    # Title
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

    # Table
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(0.3), Inches(1.1), Inches(9.4), Inches(0.4 * num_rows))
    table = table_shape.table

    # Headers
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = ST_BLUE
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = WHITE

    # Data
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = str(val)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.color.rgb = DARK_GRAY

    return slide


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
        "Practical Workshop — Full End-to-End Workflow"
    )

    add_content_slide(prs, "Agenda", [
        "## 1. Executive Summary",
        "## 2. Context & Business Need",
        "## 3. Architecture Overview",
        "## 4. End-to-End Pipeline Workflow",
        "## 5. Preprocessing Deep Dive",
        "## 6. ALFRED Vision Integration",
        "## 7. Delivery & Upload to Knowledge Base",
        "## 8. Quality Gates & Validation",
        "## 9. Value Proposition & Impact",
        "## 10. Live Demo & Hands-On",
        "## 11. Conclusion & Next Steps",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1 — EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "1. Executive Summary")

    add_content_slide(prs, "What This Workshop Is About", [
        "## Problem",
        "• STM32 technical knowledge is fragmented across 25+ GitHub repos, 10k+ issues, PDFs, and images.",
        "• Without structured preprocessing, AI assistants produce generic, unsourced, or inaccurate answers.",
        "",
        "## Solution",
        "• A 7-stage automated pipeline that transforms raw GitHub signals into structured,",
        "  traceable, upload-ready Knowledge Base artifacts for ST ChatGPT.",
        "",
        "## What You Will Learn",
        "• How to configure, run, validate, and deploy the full pipeline for any STM32 series.",
        "• How ALFRED Vision enriches images and PDF figures into searchable descriptions.",
        "• How quality gates ensure production-grade reliability before each KB upload.",
    ])

    add_content_slide(prs, "Key Message — 30 Seconds", [
        "## One sentence",
        "• This pipeline turns scattered, heterogeneous GitHub data into AI-ready knowledge",
        "  that makes STM32 support answers more relevant, traceable, and actionable.",
        "",
        "## By the numbers",
        "• 25 MCU series configured | 19 fully processed with PDF enrichment",
        "• 242 PDF figure descriptions generated via ALFRED Vision",
        "• 4 artifact types per series: Issues, Files, Resolver Cases, Diagnostic Cards",
        "• Quality Index: 94/100 on pilot series H7 with Diagnostic Cards",
        "",
        "## Impact",
        "• KB-first answers are +39% more relevant than generic LLM on STM32 technical questions.",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 2 — CONTEXT & BUSINESS NEED
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "2. Context & Business Need")

    add_content_slide(prs, "The Problem Space", [
        "## Current Challenges",
        "• Customer support engineers spend significant time searching fragmented sources.",
        "• Raw GitHub issues contain noise: off-topic, duplicates, short questions, images without text.",
        "• PDF documentation contains critical figures that are invisible to text-based search.",
        "• No automated link between issues, root causes, and resolutions.",
        "",
        "## Business Need",
        "• A single AI-powered support interface (ST ChatGPT) that answers from verified, structured data.",
        "• Traceability: every answer must link back to a source (issue, file, commit, figure).",
        "• Scalability: the solution must work for all 25 STM32 series, not just one.",
        "• Maintainability: adding a new series must be a simple configuration step.",
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

    add_content_slide(prs, "High-Level System Architecture", [
        "## Three Layers",
        "• DATA SOURCES: GitHub API (issues, PRs, commits, files), local repo clones, PDF documents.",
        "• PROCESSING ENGINE: Python pipeline (ingestion \u2192 cleaning \u2192 enrichment \u2192 delivery).",
        "• CONSUMPTION: ST ChatGPT persona backed by KB #793 with Hybrid search.",
        "",
        "## Key Design Principles",
        "• Modular: each stage is independently runnable and testable.",
        "• Idempotent: re-running any stage produces the same output.",
        "• Config-driven: one JSON config per series, no code changes to add a new MCU family.",
        "• Observable: summary files, stats scripts, and evaluation reports at every stage.",
    ])

    add_diagram_slide(prs, "Architecture \u2014 Data Flow", [
        ("GITHUB API", "Issues, PRs, Commits, Links \u2192 raw JSON per repo"),
        ("LOCAL CLONES", "Repository files: READMEs, Release Notes, PDFs, source code"),
        ("PIPELINE ENGINE", "7 stages: Ingest \u2192 Clean \u2192 Enrich \u2192 Similarity \u2192 Chunk \u2192 Evaluate \u2192 Deliver"),
        ("ALFRED VISION", "Image descriptions (issue screenshots) + PDF figure descriptions"),
        ("ST-READY ARTIFACTS", "Structured JSON: issues, files, resolver_cases, diagnostic_cards"),
        ("KB #793", "ST ChatGPT Knowledge Base \u2014 Hybrid semantic + full-text search"),
        ("END USER", "Support engineer asks question \u2192 AI answers with source traceability"),
    ])

    add_content_slide(prs, "Project File Structure", [
        "```PFE_Chatbot_STM32Cube/",
        "```\u251c\u2500\u2500 shared/config/             Config per series (config_h7.json, config_f4.json...)",
        "```\u251c\u2500\u2500 pipeline/",
        "```\u2502   \u251c\u2500\u2500 ingestion/             fetch_issues, fetch_files, fetch_prs, repo_sync",
        "```\u2502   \u251c\u2500\u2500 cleaning/              clean_issues, clean_files (normalize, extract images)",
        "```\u2502   \u251c\u2500\u2500 enrichment/            issues_to_docs_v2, files_to_docs_v2 (classify, tag)",
        "```\u2502   \u251c\u2500\u2500 similarity/            TF-IDF cosine \u2192 related_issue_ids",
        "```\u2502   \u251c\u2500\u2500 chunking/              docs_to_chunks (paragraph-based splitting)",
        "```\u2502   \u251c\u2500\u2500 delivery/              export_st_ready_* (4 artifact types)",
        "```\u2502   \u2514\u2500\u2500 evaluation/            stats, TF-IDF search, schema validation",
        "```\u251c\u2500\u2500 pipeline_Automation/",
        "```\u2502   \u251c\u2500\u2500 alfred/                enrich_json_images, enrich_pdf_figures",
        "```\u2502   \u251c\u2500\u2500 upload/                Add_Data_Source_Files.py, datasource management",
        "```\u2502   \u2514\u2500\u2500 workflow/              PowerShell orchestration scripts",
        "```\u251c\u2500\u2500 datasets/07_delivery/      Final ST-ready outputs organized by_series/",
        "```\u2514\u2500\u2500 data/                      Intermediate artifacts (not committed)",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4 — END-TO-END PIPELINE WORKFLOW
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "4. End-to-End Pipeline Workflow")

    add_diagram_slide(prs, "Pipeline \u2014 23 Steps in Sequence", [
        ("1-6. INGESTION", "GitHub API calls + local repo sync + file collection (incl. PDFs)"),
        ("7. ALFRED PDF", "Extract PDF figures, render pages, crop regions, generate tasks"),
        ("8-9. CLEANING", "Normalize text, detect [IMAGE ATTACHED], structure content"),
        ("10-11. ENRICHMENT", "Classify: layer, board, component, severity, is_valid, issue_kind"),
        ("12. SIMILARITY", "TF-IDF cosine between issues \u2192 related_issue_ids field"),
        ("13-17. EVAL", "Chunking + stats + TF-IDF search tests + schema validation"),
        ("18-23. DELIVERY", "Export 4 artifact types + issues_with_images + ALFRED Vision"),
    ])

    add_content_slide(prs, "Running the Full Pipeline \u2014 One Command", [
        "## Set the target series configuration",
        '```$env:STM32CUBE_CONFIG = "shared/config/config_h7.json"',
        "",
        "## Launch the complete workflow with delivery",
        "```python -m pipeline.run_full_workflow --export-st-ready --continue-on-error",
        "",
        "## What this executes (in order):",
        "• Steps 1-6: Ingestion (issues, PRs, commits, links, repo sync, files)",
        "• Step 7: ALFRED PDF figure extraction and task generation",
        "• Steps 8-9: Cleaning (issues + files)",
        "• Steps 10-11: Enrichment V2 (classification + tagging)",
        "• Step 12: Similarity computation",
        "• Steps 13-17: Chunking + evaluation + schema validation",
        "• Steps 18-23: Delivery exports + ALFRED Vision on issue images",
    ])

    add_content_slide(prs, "Pipeline Control Flags", [
        "## --export-st-ready",
        "• Activates delivery steps (18-23): issues, files, resolver, diag, with_images, ALFRED",
        "• Without this flag, pipeline stops after evaluation",
        "",
        "## --continue-on-error",
        "• If one step fails (e.g., a sub-repo has no issues), continues to the next",
        "• Essential for multi-repo series configurations",
        "",
        "## --skip-ingestion",
        "• Skips GitHub API calls; uses existing raw_* files in data/",
        "• Saves API rate limit when reprocessing",
        "",
        "## --no-enrich-pdf",
        "• Skips ALFRED Vision on PDF figures (step 7)",
        "• Use when PDFs are already enriched or proxy is unavailable",
    ])

    add_content_slide(prs, "Single-Series Full Workflow Script", [
        "## Recommended command for workshop / production:",
        "```.\\\\pipeline_Automation\\\\workflow\\\\Run_Single_Series_Full_Pipeline_And_Upload.ps1 -Series H7",
        "",
        "## What it orchestrates:",
        "• 1. Configures environment for the target series",
        "• 2. Runs full preprocessing pipeline with ALFRED PDF enrichment",
        "• 3. Exports all ST-ready artifacts (parent + drivers)",
        "• 4. Validates schemas and checks for unresolved placeholders",
        "• 5. Patches ALFRED PDF descriptions into delivery files",
        "• 6. Uploads to KB #793 with correct datasource routing",
        "",
        "## Placeholder safety modes:",
        "• -PlaceholderPolicy Fail  \u2192 blocks upload if placeholders remain (production)",
        "• -PlaceholderPolicy Warn  \u2192 warns but continues (demo / development)",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 5 — PREPROCESSING DEEP DIVE
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "5. Preprocessing Deep Dive")

    add_content_slide(prs, "Preprocessing \u2014 What Happens Before Delivery", [
        "## Stage 1: Ingestion",
        "• GitHub API: fetch issues (with labels, comments, timelines), PRs, commits, links.",
        "• Local clone: sync repos to access files, PDFs, and source code.",
        "• File collection: README, Release Notes, PDFs from Documentation/ folder.",
        "",
        "## Stage 2: Cleaning",
        "• Normalize Markdown/HTML to clean text.",
        "• Detect and tag embedded images: body images \u2192 [IMAGE ATTACHED].",
        "• Extract structured fields from issues: title, body, comments, labels.",
        "",
        "## Stage 3: Enrichment V2",
        "• Heuristic + rule-based classification:",
        "  \u2192 layer (HAL/LL/Middleware/BSP/CubeMX), board, component, severity, issue_kind.",
        "• Validity filtering: short/duplicate/wontfix \u2192 is_valid=false (with rescue mechanism).",
    ])

    add_content_slide(prs, "Preprocessing \u2014 Similarity & Chunking", [
        "## Stage 4: Similarity",
        "• Build TF-IDF vectors from enriched issue documents.",
        "• Compute pairwise cosine similarity (threshold > 0.3).",
        "• Add related_issue_ids field \u2192 helps retrieval of connected problems.",
        "",
        "## Stage 5: Chunking (local evaluation only)",
        "• Paragraph-based splitting with token-limit awareness.",
        "• Used for local TF-IDF search tests \u2014 the ST platform does its own chunking at upload.",
        "",
        "## Stage 6: Evaluation & Validation",
        "• test_stats_issues_v2.py / test_stats_files_v2.py \u2192 distribution analysis.",
        "• test_tfidf_search_*.py \u2192 retrieval quality on representative queries.",
        "• validate_schemas.py \u2192 JSON contract compliance gate.",
    ])

    add_diagram_slide(prs, "Preprocessing Chain \u2014 Transformations", [
        ("RAW ISSUES", "GitHub JSON: title, body, labels, comments, timeline events"),
        ("CLEANED", "Normalized text, [IMAGE ATTACHED] tags, structured fields"),
        ("ENRICHED", "layer, board, component, severity, is_valid, issue_kind, keywords"),
        ("SIMILARITY", "related_issue_ids added (TF-IDF cosine links)"),
        ("DELIVERY-READY", "st_ready_text, metadata, image_urls, resolver links"),
    ])

    add_diagram_slide(prs, "File Preprocessing Chain", [
        ("RAW FILES", "Collected from repo: README.md, Release_Notes.html, PDF documents"),
        ("PDF EXTRACTION", "PyPDF text + PyMuPDF page render + OpenCV figure detection"),
        ("CLEANED FILES", "Normalized content, figure crops stored, task files generated"),
        ("ENRICHED FILES", "file_type, board, component, category, content_extractor tagged"),
        ("DELIVERY-READY", "st_ready_text with [FIGURE_DESCRIPTIONS] blocks injected"),
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 6 — ALFRED VISION INTEGRATION
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "6. ALFRED Vision Integration")

    add_content_slide(prs, "ALFRED \u2014 Role in the Pipeline", [
        "## What is ALFRED?",
        "• ST's internal Vision AI API (api-ai-bridge.st.com).",
        "• Analyzes images and generates structured textual descriptions.",
        "",
        "## Two distinct roles in the pipeline:",
        "",
        "## Role A: Issue Image Enrichment (Step 23)",
        "• Input: st_ready_issues_with_images_*.json containing image_urls.",
        "• Process: ALFRED analyzes each screenshot and writes a text description.",
        "• Output: [IMAGE ATTACHED] \u2192 [IMAGE DESCRIPTION] <technical text>.",
        "• Impact: screenshots become searchable by the RAG system.",
        "",
        "## Role B: PDF Figure Enrichment (Step 7)",
        "• Input: Cropped figure PNGs from data/pdf_figures/<repo>/.",
        "• Process: ALFRED describes each diagram/figure in technical context.",
        "• Output: Descriptions stored in data/pdf_image_descriptions.json.",
        "• Impact: PDF figures become searchable via [FIGURE_DESCRIPTIONS] blocks.",
    ])

    add_content_slide(prs, "ALFRED \u2014 Where It Fits in the Workflow", [
        "## Integration Points:",
        "",
        "```[Ingestion] \u2192 [PDF figure crop + render] \u2192 ALFRED PDF (step 7)",
        "```                                            \u2193",
        "```                                  pdf_image_descriptions.json",
        "```                                            \u2193",
        "```[Cleaning \u2192 Enrichment] \u2192 files_to_docs_v2 \u2192 inject descriptions",
        "```                                            \u2193",
        "```[Delivery] \u2192 export_st_ready_files_v3.json (with FIGURE_DESCRIPTIONS)",
        "",
        "```[Delivery] \u2192 export_issues_with_images \u2192 ALFRED Images (step 23)",
        "```                                            \u2193",
        "```             [IMAGE ATTACHED] \u2192 [IMAGE DESCRIPTION] in-place",
        "",
        "## Key Implementation Detail:",
        "• ALFRED operates in-place (modifies the JSON directly, no separate output file).",
        "• PlaceholderPolicy gate checks for unresolved markers before upload.",
    ])

    add_content_slide(prs, "ALFRED \u2014 Concrete Examples (H7)", [
        "## Example 1 \u2014 Issue #335 (STM32CubeH7)",
        "• Topic: Warning observed with -Wcast-align flag during compilation.",
        "• Before: Screenshot attached but invisible to text search.",
        "• After: ALFRED describes Eclipse Tool Settings panel \u2192 flags become searchable.",
        "",
        "## Example 2 \u2014 Issue #333 (STM32CubeH7)",
        "• Topic: Fix compile-time warnings without removing compiler flags.",
        "• After: ALFRED extracts 'About STM32CubeIDE' dialog \u2192 version info traceable.",
        "",
        "## Example 3 \u2014 PDF Figure (H7 GettingStarted.pdf, page 3)",
        "• Before: Figure 1 is a raster image in a PDF, invisible to retrieval.",
        "• After: ALFRED describes the firmware component stack diagram.",
        "• st_ready_text now contains the architecture description as searchable text.",
    ])

    add_table_slide(prs, "ALFRED Coverage Across Series",
        ["Series", "Issues w/ Images", "Total Images", "ALFRED Success", "PDF Figures"],
        [
            ["H7", "53", "98", "97/98", "10"],
            ["F4", "34", "62", "61/62", "11"],
            ["WL", "23", "48", "48/48", "11"],
            ["F7", "20", "26", "26/26", "11"],
            ["WB", "\u2014", "\u2014", "\u2014", "22"],
            ["G0", "yes", "\u2014", "OK", "13"],
            ["H7RS", "\u2014", "\u2014", "\u2014", "25"],
            ["N6", "\u2014", "\u2014", "\u2014", "15"],
            ["... 19 series total", "", "", "", "242 total"],
        ]
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 7 — DELIVERY & UPLOAD
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "7. Delivery & Upload to KB")

    add_content_slide(prs, "Four Artifact Types \u2014 ST-Ready JSON", [
        "## 1. Issues (st_ready_issues_*.json)",
        "• Structured support cards: title, body, context, layer, severity, related issues.",
        "",
        "## 2. Files (st_ready_files_*_v3.json)",
        "• Documentation cards: README, Release Notes, PDFs with figure descriptions.",
        "",
        "## 3. Resolver Cases (st_ready_resolver_cases_*.json)",
        "• Cause \u2192 Action pairs extracted from closed issues with confirmed fixes.",
        "",
        "## 4. Diagnostic Cards (st_ready_diagnostic_cards_*.json)",
        "• Structured troubleshooting: symptoms, root cause, resolution, query aliases.",
        "• Designed for high-precision retrieval on specific technical problems.",
    ])

    add_content_slide(prs, "Delivery Output Structure", [
        "```datasets/07_delivery/st_ready/by_series/",
        "```\u251c\u2500\u2500 stm32cubeh7/",
        "```\u2502   \u251c\u2500\u2500 issues_json/",
        "```\u2502   \u2502   \u251c\u2500\u2500 st_ready_issues_stm32cubeh7.json",
        "```\u2502   \u2502   \u2514\u2500\u2500 st_ready_issues_with_images_stm32cubeh7.json  (+ ALFRED)",
        "```\u2502   \u251c\u2500\u2500 files_json/",
        "```\u2502   \u2502   \u2514\u2500\u2500 st_ready_files_stm32cubeh7_v3.json  (with PDF figures)",
        "```\u2502   \u251c\u2500\u2500 resolver_cases_json/",
        "```\u2502   \u2502   \u2514\u2500\u2500 st_ready_resolver_cases_stm32cubeh7.json",
        "```\u2502   \u251c\u2500\u2500 diagnostic_cards_json/",
        "```\u2502   \u2502   \u2514\u2500\u2500 st_ready_diagnostic_cards_stm32cubeh7.json",
        "```\u2502   \u251c\u2500\u2500 drivers/  (10+ sub-repo artifacts)",
        "```\u2502   \u2514\u2500\u2500 upload_datasource_ids_stm32cubeh7.json",
    ])

    add_table_slide(prs, "KB #793 \u2014 Datasource Organization",
        ["Series", "Issues DS", "Files DS", "Resolver DS", "Diag Cards DS"],
        [
            ["STM32H7", "#24406", "#29041", "#24410", "#24408"],
            ["STM32F4", "#28099", "#29042", "#28118", "#28122"],
            ["STM32H5", "\u2014", "#29043", "\u2014", "\u2014"],
            ["STM32U5", "\u2014", "#29044", "\u2014", "\u2014"],
            ["STM32WL", "\u2014", "#29045", "\u2014", "\u2014"],
            ["... 13 series", "1 DS each", "1 DS each", "1 DS each", "1 DS each"],
        ]
    )

    add_table_slide(prs, "Processor Params \u2014 JSON Upload Configuration",
        ["Artifact Type", "rootTagPath", "Label Template", "ExternalURL Pattern"],
        [
            ["Issues", "issues", "{{repo}} issue #{{issue_number}} - {{issue_title}}", "github.com/.../issues/{{issue_number}}"],
            ["Files", "files", "{{repo}} {{file_type}} - {{path}}", "github.com/.../{{root_ref}}/{{path_url}}"],
            ["Resolver Cases", "resolver_cases", "{{label}}", "github.com/.../issues/{{issue_number}}"],
            ["Diagnostic Cards", "\u2014", "{{label}}", "github.com/.../issues/{{evidence_refs[0].id}}"],
        ]
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 8 — QUALITY GATES & VALIDATION
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "8. Quality Gates & Validation")

    add_content_slide(prs, "Quality Gates \u2014 Before Upload", [
        "## Gate 1: Schema Validation",
        "• python -m pipeline.evaluation.validate_schemas",
        "• Verifies all JSON outputs conform to shared/schemas/*.json contracts.",
        "",
        "## Gate 2: Placeholder Check",
        "• Scans for unresolved [IMAGE ATTACHED] or [FIGURE... markers in delivery files.",
        "• PlaceholderPolicy=Fail blocks upload; =Warn allows with explicit report.",
        "",
        "## Gate 3: Summary Coherence",
        "• summary_*.json files report counts; must match payload size.",
        "",
        "## Gate 4: Smoke Test (post-upload)",
        "• Ask 3 representative questions \u2192 verify answers cite correct sources.",
        "• KB-first behavior validated (ALFRED fallback only when KB has no match).",
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
        ["KPI", "Measurement", "Decision It Supports"],
        [
            ["Ingestion completeness", "% non-empty issues/files", "Is the input material sufficient?"],
            ["Enrichment coverage", "% docs with layer/component/board", "Does preprocessing add useful signal?"],
            ["ALFRED success rate", "described / detected images", "Is visual content exploitable?"],
            ["Placeholder rate", "unresolved / total figures", "Can we upload in strict mode?"],
            ["Quality Index", "Score on test questions", "Is the final answer quality acceptable?"],
        ]
    )

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 9 — VALUE PROPOSITION & IMPACT
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "9. Value Proposition & Impact")

    add_content_slide(prs, "Before vs. After \u2014 Tangible Value", [
        "## Without the Pipeline",
        "• Raw issues: unstructured, noisy, images invisible, no links between problems.",
        "• AI answers: generic, unsourced, sometimes incorrect.",
        "• Maintenance: manual per-series curation, no repeatability.",
        "",
        "## With the Pipeline",
        "• Structured cards: each issue has layer, board, component, severity, related issues.",
        "• AI answers: sourced, traceable, with diagnostic logic and resolver actions.",
        "• Maintenance: add a config, run one command, upload. Repeatable for 25+ series.",
    ])

    add_table_slide(prs, "Value Dimensions",
        ["Dimension", "Description", "Evidence"],
        [
            ["Efficiency", "One-command processing for entire series", "23 steps automated, batch multi-series"],
            ["Traceability", "Every answer links to a source", "github_url, evidence_refs in cards"],
            ["Robustness", "Quality gates prevent bad data reaching KB", "Schema validation + placeholder gate"],
            ["Scalability", "Config-driven, no code changes", "25 series configured, 200+ sub-repos"],
            ["Maintainability", "Modular stages, clear interfaces", "Each stage independently testable"],
            ["Explainability", "Diagnostic cards explain cause + resolution", "QI = 94/100 on H7"],
        ]
    )

    add_content_slide(prs, "Strengths Relative to Business Context", [
        "## Why this matters for STMicroelectronics",
        "• Reduces time-to-answer for technical support queries on STM32 platform.",
        "• Enables non-expert users to get expert-level technical guidance from AI.",
        "• Makes visual information (screenshots, PDF figures) exploitable by RAG.",
        "",
        "## Competitive Advantages of This Approach",
        "• End-to-end automation: no manual curation bottleneck.",
        "• Multi-modal: text + images + PDF figures all enriched and indexed.",
        "• Production-hardened: placeholder gates, retry logic, idempotent uploads.",
        "• Open architecture: modular Python, PowerShell orchestration, standard JSON contracts.",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 10 — INCIDENTS & GENERALIZED FIXES
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "10. Incidents Encountered & Generalized Fixes")

    add_table_slide(prs, "From Incident to Systematic Improvement",
        ["Incident", "Root Cause", "Fix Applied", "Generalized For All Series"],
        [
            ["Unresolved ALFRED placeholders", "Truncated figure IDs in WB", "PlaceholderPolicy gate + report", "Same gate before every upload"],
            ["PDF figures not resolved", "Timing: descriptions after delivery", "Patch script + re-injection", "Pipeline step 7 + patch script"],
            ["Evaluation chart crash", "Zero values in pie chart", "_safe_pie() wrapper", "All reports handle empty data"],
            ["Upload blocked by existing DS", "API rejects duplicate names", "Reuse saved datasource IDs", "Idempotent batch workflows"],
            ["API timeouts during eval", "Rate limiting on ai-bridge", "Warning mode + separate validation", "Demo-safe without weakening prod"],
        ]
    )

    add_content_slide(prs, "Design Philosophy \u2014 Fail Forward", [
        "## Every incident became a permanent improvement:",
        "• Not patched for one series then forgotten.",
        "• Turned into a reusable control, gate, or workflow improvement.",
        "",
        "## Examples of generalized mechanisms:",
        "• PlaceholderPolicy parameter (Fail/Warn/Off) \u2014 available in every workflow script.",
        "• _safe_pie() in evaluation reports \u2014 protects against zero-data series.",
        "• upload_datasource_ids_<serie>.json \u2014 makes uploads idempotent and retryable.",
        "• --continue-on-error \u2014 ensures one failed sub-repo doesn't block the series.",
        "",
        "## Lesson for new series:",
        "• Any new series benefits from all historical fixes automatically.",
        "• No special handling required \u2014 the pipeline is self-hardening.",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 11 — LIVE DEMO
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "11. Live Demo & Hands-On")

    add_content_slide(prs, "Demo Script \u2014 5 Minutes", [
        "## Step 1: Prepare a series",
        "```.\\\\pipeline_Automation\\\\workflow\\\\Run_Single_Series_Full_Pipeline_And_Upload.ps1 -Series WB -Mode Prepare -PlaceholderPolicy Warn",
        "",
        "## Step 2: Show generated artifacts",
        "• by_series/stm32cubewb/issues_json/, files_json/, diagnostic_cards_json/",
        "",
        "## Step 3: Show a quality gate",
        "• validate_schemas output, placeholder report, summary_*.json counts",
        "",
        "## Step 4: Upload (or show saved datasource IDs)",
        "• upload_datasource_ids_stm32cubewb.json",
        "",
        "## Step 5: Ask a technical question",
        "• Show the answer + source citation from the Knowledge Base",
    ])

    add_content_slide(prs, "High-Stakes Presentation Checklist", [
        "## Preparation (day before):",
        "• Run a full Prepare on the target series \u2014 artifacts must be ready.",
        "• Generate summary_*.json and validate schemas.",
        "• Prepare 3 before/after examples (raw issue \u2192 structured st_ready card).",
        "• Prepare 1 failure case with mitigation (shows transparency).",
        "",
        "## During the demo:",
        "• Start with the single-command workflow.",
        "• Show the file structure and explain what each artifact contains.",
        "• Ask a real question in ST ChatGPT and show the sourced answer.",
        "• Show a quality gate catching a problem (placeholder report).",
        "",
        "## Safety net:",
        "• Use -PlaceholderPolicy Warn for known non-critical series.",
        "• Have upload_datasource_ids pre-saved to avoid live API dependency.",
    ])

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 12 — CONCLUSION
    # ══════════════════════════════════════════════════════════════════════

    add_section_slide(prs, "12. Conclusion")

    add_content_slide(prs, "Key Takeaways", [
        "## Technical Value",
        "• Industrialized transformation of heterogeneous GitHub data into structured KB artifacts.",
        "• Multi-modal: text, images, and PDF figures all made searchable.",
        "",
        "## Quality Value",
        "• Every artifact passes through validation, gates, and reports that make errors visible.",
        "• Production-grade: strict mode ensures no garbage reaches the Knowledge Base.",
        "",
        "## Operational Value",
        "• Incidents encountered were not patched ad-hoc \u2014 they became permanent controls.",
        "• Adding a new series = 1 config file + 1 command. No code changes.",
        "",
        "## Business Value",
        "• +39% relevance improvement over generic LLM on STM32 technical questions.",
        "• Quality Index: 94/100 on pilot H7 series with Diagnostic Cards.",
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
