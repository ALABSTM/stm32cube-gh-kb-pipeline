"""
Generate a PowerPoint presentation for the STM32Cube Pipeline Workshop.
Run: python docs/generate_workshop_pptx.py
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

    # ========== SLIDE 1: Title ==========
    add_title_slide(
        prs,
        "Pipeline de Prétraitement\nSTM32Cube → Knowledge Base",
        "Atelier Pratique — Guide d'exécution complet"
    )

    # ========== SLIDE 2: Agenda ==========
    add_content_slide(prs, "Agenda", [
        "## 1. Vue d'ensemble du pipeline",
        "## 2. Architecture du projet",
        "## 3. Configuration d'une série",
        "## 4. Étapes du pipeline (détail)",
        "## 5. Enrichissement Alfred (images + PDF)",
        "## 6. Upload vers la Knowledge Base",
        "## 7. Scripts d'automatisation",
        "## 8. Bonnes pratiques & dépannage",
    ])

    # ========== SLIDE 3: Pipeline Overview Diagram ==========
    add_diagram_slide(prs, "Vue d'ensemble — Pipeline end-to-end", [
        ("1. INGESTION", "GitHub API → raw_issues, raw_files, raw_prs, raw_commits"),
        ("2. CLEANING", "Normalisation texte, extraction images [IMAGE ATTACHED], structuration"),
        ("3. ENRICHMENT", "Classification: layer, board, component, severity, is_valid"),
        ("4. SIMILARITY", "TF-IDF cosine → related_issue_ids entre issues similaires"),
        ("5. DELIVERY", "Export JSON ST-ready: issues, files, resolver_cases, diagnostic_cards"),
        ("6. ALFRED (post-delivery)", "Vision API sur st_ready_issues_with_images → descriptions textuelles"),
        ("7. UPLOAD KB", "Push JSON enrichis vers Knowledge Base #793 (ST ChatGPT)"),
    ])

    # ========== SLIDE 3b: Alfred dans le workflow ==========
    add_content_slide(prs, "Alfred — Intégré dans le workflow", [
        "## Alfred est maintenant INTÉGRÉ dans run_full_workflow.py :",
        "• --export-st-ready ajoute 6 steps (au lieu de 4) :",
        "  → export issues, files, resolver, diag, issues_with_images, Alfred images",
        "• Alfred images est la DERNIÈRE étape automatique du workflow",
        "",
        "## Séquence complète :",
        "```Pipeline (17 steps) → Delivery (4 exports) → with_images → Alfred Vision",
        "",
        "## Ce que fait Alfred images automatiquement :",
        "• Parcourt by_series/*/issues_json/st_ready_issues_with_images_*.json",
        "• Pour chaque issue avec images : télécharge, envoie à Alfred, remplace le texte",
        "• [IMAGE ATTACHED] → [IMAGE DESCRIPTION] texte descriptif",
        "• Modifie le fichier in-place (pas de fichier séparé)",
        "",
        "## Alfred PDF figures (étape 7, dans STEPS) :",
        "• Enrichit les figures des PDFs AVANT le cleaning",
        "• Descriptions stockées dans data/pdf_image_descriptions.json",
        "• Injectées dans les docs_files lors du files_to_docs_v2",
    ])

    # ========== SLIDE 4: Project Architecture ==========
    add_content_slide(prs, "Architecture du Projet", [
        "```PFE_Chatbot_STM32Cube/",
        "```├── shared/config/         → Configs par série (config_h7.json...)",
        "```├── pipeline/              → Code pipeline Python",
        "```│   ├── ingestion/         → fetch_issues, fetch_files...",
        "```│   ├── cleaning/          → clean_issues, clean_files",
        "```│   ├── enrichment/        → issues_to_docs_v2, files_to_docs_v2",
        "```│   ├── similarity/        → compute_issue_similarity_v2",
        "```│   ├── chunking/          → docs_to_chunks (local)",
        "```│   ├── delivery/          → export_st_ready_*",
        "```│   └── evaluation/        → stats, TF-IDF tests, schemas",
        "```├── pipeline_Automation/",
        "```│   ├── alfred/            → enrich_json_images, enrich_pdf_figures",
        "```│   ├── upload/            → Add_Data_Source_Files.py, Get_Persona_KBs.py",
        "```│   └── workflow/          → Scripts PS1 automatisation",
        "```├── data/                  → Fichiers intermédiaires (NON commités)",
        "```├── datasets/07_delivery/  → Outputs finaux ST-ready",
        "```└── GitHub_repos/          → Clones locaux (auto)",
    ])

    # ========== SLIDE 5: Configuration ==========
    add_content_slide(prs, "Configuration d'une Série", [
        "## Fichier: shared/config/config_<serie>.json",
        "",
        "```{",
        '```  "owner": "STMicroelectronics",',
        '```  "repos": ["STM32CubeH7", "stm32h7xx-hal-driver", "cmsis_device_h7", ...],',
        '```  "auto_clone_missing_repos": true,',
        '```  "repo_clone_urls": { "stm32h7xx-hal-driver": "https://github.com/..." },',
        '```  "github_token_env": "GITHUB_TOKEN"',
        "```}",
        "",
        "## Variable d'environnement",
        "```$env:STM32CUBE_CONFIG = \"shared/config/config_h7.json\"",
        "",
        "## Mapping sous-repos → drivers/ (delivery_paths.py)",
        "• Chaque sous-repo est routé sous by_series/<serie>/drivers/<sous-repo>/",
    ])

    # ========== SLIDE 6: Commande principale ==========
    add_content_slide(prs, "Commande Principale — Pipeline Complet", [
        "## Lancer le pipeline complet pour une série:",
        "",
        "```$env:STM32CUBE_CONFIG = \"shared/config/config_f7.json\"",
        "```python -m pipeline.run_full_workflow --export-st-ready --continue-on-error",
        "",
        "## Ce que ça exécute (dans l'ordre) :",
        "• [1-6] Ingestion (issues, PRs, commits, links, sync repos, files)",
        "• [7] Alfred PDF figure descriptions",
        "• [8-9] Cleaning (issues + files)",
        "• [10-11] Enrichment (issues + files → layer, board, component...)",
        "• [12] Similarity (TF-IDF cosine entre issues)",
        "• [13-14] Chunking (découpage en chunks pour recherche)",
        "• [15-17] Évaluation (stats + validation schémas)",
        "• [18-21] Delivery (export JSON ST-ready: issues, files, resolver, diag)",
        "• [22] Export issues_with_images (variante avec image_urls)",
        "• [23] Alfred Vision — descriptions automatiques des images",
    ])

    # ========== SLIDE 6b: Flags ==========
    add_content_slide(prs, "Flags du Workflow — Contrôle fin", [
        "## Tous les flags disponibles :",
        "",
        "```--export-st-ready",
        "  → Active les 6 steps de delivery + Alfred images",
        "  → issues, files, resolver, diag, with_images, Alfred Vision",
        "  → Sans ce flag, le pipeline s'arrête après la validation",
        "",
        "```--continue-on-error",
        "  → Si un step échoue, passe au suivant au lieu de tout arrêter",
        "  → Indispensable quand un sous-repo n'a pas d'issues",
        "",
        "```--skip-ingestion",
        "  → Saute les 6 étapes d'ingestion GitHub",
        "  → Utilise les fichiers raw_* déjà présents dans data/",
        "  → Utile pour re-processer sans re-télécharger (économise le rate limit)",
        "",
        "```--skip-chunking",
        "  → Saute le chunking local (étapes 13-14)",
        "  → La plateforme ST fait son propre chunking à l'upload",
        "",
        "```--no-enrich-pdf",
        "  → Saute l'appel Alfred Vision sur les figures PDF (étape 7)",
        "  → Utile si pas de proxy ou si les PDFs sont déjà enrichis",
    ])

    # ========== SLIDE 6c: run_full_workflow internals ==========
    add_content_slide(prs, "run_full_workflow.py — Fait TOUT (issues + files)", [
        "## ⚠️ Ce n'est PAS un pipeline 'issues only'",
        "• Il traite issues ET files (cleaning, enrichment, delivery des deux)",
        "• 17 étapes de base + 4 optionnelles (delivery)",
        "",
        "## Liste STEPS (code réel) :",
        "```STEPS = [",
        '```  ("Ingestion issues",     fetch_issues_main),      # 1',
        '```  ("Ingestion PRs",        fetch_prs_main),         # 2',
        '```  ("Ingestion commits",    fetch_commits_main),     # 3',
        '```  ("Ingestion links",      fetch_links_main),       # 4',
        '```  ("Ingestion sync repos", sync_local_repos_main),  # 5',
        '```  ("Ingestion files",      fetch_files_main),       # 6',
        '```  ("Alfred PDF figures",   _enrich_pdf_main),       # 7',
        '```  ("Cleaning issues",      clean_issues_main),      # 8',
        '```  ("Cleaning files",       clean_files_main),       # 9',
        '```  ("Enrichment issues V2", issues_to_docs_v2_main), # 10',
        '```  ("Enrichment files V2",  files_to_docs_v2_main),  # 11',
        '```  ("Similarity issues V2", similarity_main),        # 12',
        '```  ("Chunking issues V2",   chunks_issues_main),     # 13',
        '```  ("Chunking files V2",    chunks_files_main),      # 14',
        '```  ("Stats issues V2",      stats_issues_main),      # 15',
        '```  ("Stats files V2",       stats_files_main),       # 16',
        '```  ("Schema validation",    validate_schemas_main),  # 17',
        "```]",
    ])

    # ========== SLIDE 6c2: Fonctionnement interne ==========
    add_content_slide(prs, "run_full_workflow.py — Fonctionnement interne", [
        "## Chaque step = un tuple (label, fonction Python)",
        '• ("Cleaning issues", clean_issues_main) → appelle clean_issues_main()',
        "• Le label sert pour le print [1/17] et le filtrage par flag",
        "",
        "## Les flags FILTRENT la liste avant exécution :",
        '• --skip-ingestion  → retire tout step dont label.startswith("Ingestion")',
        '• --skip-chunking   → retire tout step dont label.startswith("Chunking")',
        '• --no-enrich-pdf   → retire tout step dont label.startswith("Alfred")',
        "",
        "## --export-st-ready AJOUTE 6 steps à la fin :",
        '• ("Delivery ST-ready issues",           export_issues_all)',
        '• ("Delivery ST-ready files",            export_files_all)',
        '• ("Delivery ST-ready resolver",         export_resolver_all)',
        '• ("Delivery ST-ready diag cards",       export_diag_all)',
        '• ("Delivery ST-ready issues with imgs", export_with_images_all)',
        '• ("Alfred image descriptions",          _enrich_alfred_images_main)',
        "",
        "## Gestion d'erreurs :",
        "• Sans --continue-on-error → exception = STOP immédiat",
        "• Avec --continue-on-error → print [WARN] + passe au step suivant",
        "",
        "## Config : $env:STM32CUBE_CONFIG → shared/utils/paths.py → get_config_path()",
    ])

    # ========== SLIDE 6c3: Différence avec Run_Issues_Pipeline ==========
    add_content_slide(prs, "run_full_workflow vs Run_Issues_Pipeline_For_All_Repos", [
        "## run_full_workflow.py (Python) :",
        "• Fait TOUT : issues + files + similarity + chunking + eval + delivery",
        "• 17-21 étapes complètes",
        "• Utilisé pour un traitement complet d'une série",
        "",
        "## Run_Issues_Pipeline_For_All_Repos.ps1 (PowerShell) :",
        "• Raccourci ISSUES-ONLY : clean → enrich → [similarity] → [chunking] → delivery",
        "• Seulement 3-5 étapes (pas de files, pas d'ingestion)",
        "• Suppose que les raw_issues sont DÉJÀ téléchargés",
        "• Utilisé pour re-processer rapidement les issues après un fix",
        "",
        "## Quand utiliser lequel ?",
        "• Nouvelle série de zéro → run_full_workflow (complet)",
        "• Fix dans l'enrichissement issues → Run_Issues_Pipeline (rapide)",
        "• Mise à jour des files seulement → lancer les étapes files individuellement",
    ])

    # ========== SLIDE 6d: Batch ==========
    add_content_slide(prs, "Batch — Lancer toutes les séries", [
        "## Script PowerShell batch :",
        "",
        '```$series = @("config_c0", "config_f0", "config_f1", "config_f2",',
        '```            "config_f3", "config_f7", "config_g0", "config_h7rs")',
        "```",
        "```foreach ($s in $series) {",
        '```    Write-Host "=== Processing $s ===" -ForegroundColor Cyan',
        '```    $env:STM32CUBE_CONFIG = "shared/config/$s.json"',
        "```    python -m pipeline.run_full_workflow --export-st-ready --continue-on-error",
        "```}",
        "",
        "## Points importants :",
        "• Chaque itération est INDÉPENDANTE (son propre config, ses propres data/)",
        "• Si une série échoue, les autres continuent grâce à --continue-on-error",
        "• Les fichiers data/ sont nommés par repo → pas de collision",
        "• Durée totale : ~10-30 min/série (dépend du nombre d'issues)",
        "",
        "## Voir aussi : pipeline_Automation/workflow/Run_Issues_Pipeline_For_All_Repos.ps1",
    ])

    # ========== SLIDE 7: Pipeline Steps Detail ==========
    add_table_slide(prs, "Étapes du Pipeline — Détail", 
        ["#", "Étape", "Script", "Output"],
        [
            ["1", "Fetch Issues", "pipeline/ingestion/fetch_issues.py", "data/raw_issues_<repo>.json"],
            ["2", "Fetch PRs", "pipeline/ingestion/fetch_prs.py", "data/raw_prs_<repo>.json"],
            ["3", "Fetch Commits", "pipeline/ingestion/fetch_commits.py", "data/raw_commits_<repo>.json"],
            ["4", "Links", "fetch_issue_pr_commit_links.py", "data/links_<repo>.json"],
            ["5", "Sync Repos", "repo_sync_service.py", "GitHub_repos/<repo>/"],
            ["6", "Fetch Files", "pipeline/ingestion/fetch_files.py", "data/raw_files_<repo>.json"],
            ["7", "Clean Issues", "pipeline/cleaning/clean_issues.py", "data/clean_issues_<repo>.json"],
            ["8", "Clean Files", "pipeline/cleaning/clean_files.py", "data/clean_files_<repo>.json"],
            ["9", "Enrich Issues", "pipeline/enrichment/issues_to_docs_v2.py", "data/docs_issues_<repo>_v2.json"],
            ["10", "Enrich Files", "pipeline/enrichment/files_to_docs_v2.py", "data/docs_files_<repo>_v2.json"],
            ["11", "Similarity", "compute_issue_similarity_v2.py", "docs_issues_<repo>_v2_sim.json"],
            ["12", "Delivery", "export_st_ready_*.py", "datasets/07_delivery/st_ready/"],
        ]
    )

    # ========== SLIDE 7b: Étapes individuelles ==========
    add_content_slide(prs, "Chaque étape peut être lancée SEULE", [
        "## Ingestion seule (une étape) :",
        "```python -m pipeline.ingestion.fetch_issues",
        "```python -m pipeline.ingestion.fetch_files",
        "",
        "## Cleaning seul :",
        "```python -m pipeline.cleaning.clean_issues",
        "```python -m pipeline.cleaning.clean_files",
        "",
        "## Enrichissement seul :",
        "```python -m pipeline.enrichment.issues_to_docs_v2",
        "```python -m pipeline.enrichment.files_to_docs_v2",
        "",
        "## Similarity seule :",
        "```python -m pipeline.similarity.compute_issue_similarity_v2",
        "",
        "## Delivery seul (par type) :",
        "```python -m pipeline.delivery.export_st_ready_issues --repo STM32CubeH7",
        "```python -m pipeline.delivery.export_st_ready_files --repo STM32CubeH7",
        "```python -m pipeline.delivery.export_st_ready_diagnostic_cards --repo STM32CubeH7",
        "```python -m pipeline.delivery.export_st_ready_resolver_cases --repo STM32CubeH7",
    ])

    # ========== SLIDE 7c: Évaluation individuelle ==========
    add_content_slide(prs, "Évaluation & Validation — Commandes individuelles", [
        "## Stats issues :",
        "```python -m pipeline.evaluation.test_stats_issues_v2",
        "  → Affiche : nb issues, couverture layer/board/component, distribution",
        "",
        "## Stats files :",
        "```python -m pipeline.evaluation.test_stats_files_v2",
        "  → Affiche : nb fichiers, types, tailles, couverture",
        "",
        "## Validation schémas :",
        "```python -m pipeline.evaluation.validate_schemas",
        "  → Vérifie que les JSON respectent les schémas shared/schemas/",
        "",
        "## Rapport d'évaluation complet (graphiques + Excel) :",
        "```python -m pipeline.evaluation.generate_evaluation_report --all",
        "  → Génère PNG + XLSX dans datasets/07_delivery/st_ready/evaluation_report/",
        "",
        "## Test TF-IDF (recherche) :",
        "```python -m pipeline.evaluation.test_tfidf_search_issues_v2",
        "  → Teste la qualité de retrieval sur des queries prédéfinies",
    ])

    # ========== SLIDE 8: Cleaning Detail ==========
    add_content_slide(prs, "Stage 2 — Cleaning (Détail)", [
        "## Ce que fait le cleaning :",
        "• Normalise le texte (retours chariot, backticks, espaces)",
        "• Extrait les images → markers [IMAGE ATTACHED] + collecte URLs",
        "• Structure: Title + Body + Comments → champ clean_text",
        "• Conserve les métadonnées brutes (labels, dates, état)",
        "",
        "## Ce que le cleaning NE fait PAS :",
        "• ❌ Pas de classification (layer, board, component)",
        "• ❌ Pas de détection de validité (is_valid)",
        "• → Ces tâches sont faites par l'ENRICHISSEMENT",
        "",
        "## Output: data/clean_issues_<repo>.json",
        "```{ repo, issue_number, title, state, labels, clean_text, image_urls, images_count }",
    ])

    # ========== SLIDE 9: Enrichment Detail ==========
    add_content_slide(prs, "Stage 3 — Enrichissement (Détail)", [
        "## Heuristiques NLP ajoutées par issues_to_docs_v2.py :",
        "",
        "• layer: HAL, BSP, Middleware, Application, CMSIS (détecté via labels + texte)",
        "• component: SPI, I2C, USB, CRYP... (regex sur titre + body)",
        "• board: NUCLEO-H743ZI, STM32H750B-DK... (patterns de noms de cartes)",
        "• severity: critical, normal, low (labels + mots-clés)",
        "• issue_kind: bug, question, feature_request (labels)",
        "• is_valid: true si texte > 100 chars + pas bot/spam",
        "",
        "## Métriques cibles :",
        "• Couverture layer ≥ 85%",
        "• Couverture component ≥ 70%",
        "• Couverture board ≥ 60%",
        "• Taux validité ≥ 85%",
    ])

    # ========== SLIDE 10: Delivery Output ==========
    add_content_slide(prs, "Stage 5 — Delivery (Structure Output)", [
        "## Sortie sous datasets/07_delivery/st_ready/by_series/",
        "",
        "```stm32cubeh7/",
        "```├── issues_json/",
        "```│   ├── st_ready_issues_stm32cubeh7.json",
        "```│   └── st_ready_issues_with_images_stm32cubeh7.json",
        "```├── files_json/",
        "```│   └── st_ready_files_stm32cubeh7.json",
        "```├── diagnostic_cards_json/",
        "```│   └── st_ready_diagnostic_cards_stm32cubeh7.json",
        "```├── resolver_cases_json/",
        "```│   └── st_ready_resolver_cases_stm32cubeh7.json",
        "```└── drivers/",
        "```    ├── stm32h7xx-hal-driver/",
        "```    │   ├── issues_json/ files_json/ diagnostic_cards_json/",
        "```    ├── cmsis_device_h7/",
        "```    └── stm32h7xx-nucleo-bsp/",
    ])

    # ========== SLIDE 11: Alfred ==========
    add_content_slide(prs, "Alfred Vision — Enrichissement Images", [
        "## 1. Images issues (AUTOMATIQUE via --export-st-ready)",
        "• run_full_workflow parcourt tous les with_images et appelle Alfred",
        "• Modifie le JSON in-place: [IMAGE ATTACHED] → [IMAGE DESCRIPTION]",
        "• C'est le fichier with_images enrichi qu'on uploade vers la KB",
        "",
        "## Lancement manuel (si besoin) :",
        "```python pipeline_Automation/alfred/enrich_json_images_with_alfred.py \\",
        "```  --input <st_ready_issues_with_images_*.json> --inplace",
        "",
        "## 2. Figures des PDFs techniques",
        "```python pipeline_Automation/alfred/enrich_pdf_figures_with_alfred.py \\",
        "```  --repo STM32CubeH7",
        "",
        "• Stocke dans data/pdf_image_descriptions.json (126 descriptions)",
        "• Re-run files_to_docs_v2 pour injecter les descriptions dans les docs",
        "• Re-run export_st_ready_files pour régénérer le JSON livrable",
        "",
        "## ⚠️ Pas besoin de --use-proxy (accès direct depuis réseau ST)",
    ])

    # ========== SLIDE 11b: Séries avec images ==========
    add_table_slide(prs, "Séries avec images issues (Alfred Vision)",
        ["Série", "Issues avec images", "Images total", "Alfred OK"],
        [
            ["H7", "53", "98", "97/98"],
            ["F4", "34", "62", "61/62"],
            ["WL", "23", "48", "48/48"],
            ["F7", "20", "26", "26/26"],
            ["G0", "images", "—", "OK"],
            ["C0", "3", "5", "5/5"],
            ["U5", "6", "—", "OK"],
            ["H5", "3", "—", "OK"],
            ["F0/F1/F2/F3/H7RS", "quelques", "—", "OK"],
        ]
    )

    # ========== SLIDE 12: Upload KB ==========
    add_content_slide(prs, "Upload vers la Knowledge Base #793", [
        "## Script: pipeline_Automation/upload/Add_Data_Source_Files.py",
        "",
        "## Créer une nouvelle datasource :",
        "```python Add_Data_Source_Files.py --kb 793 --operation new \\",
        '```  --datasource-name "STM32F7 Issues" --remote-user "x@st.com" \\',
        "```  --processor JSON --processor-params \"base64:$b64\" --json-split-size 1000 \\",
        "```  --files <chemin.json>",
        "",
        "## Ajouter à une datasource existante :",
        "```python Add_Data_Source_Files.py --kb 793 --operation add \\",
        "```  --datasource-id 29276 ... --files <chemin.json>",
        "",
        "## Upload drivers automatisé :",
        "```.\\pipeline_Automation\\upload\\Upload_All_Drivers.ps1",
        "",
        "## Vérifier la KB :",
        "```python pipeline_Automation/upload/Get_Persona_KBs.py",
    ])

    # ========== SLIDE 13: Processor Params ==========
    add_table_slide(prs, "Processor Params — 4 types de JSON",
        ["Type", "rootTagPath", "Label Template", "ExternalURL"],
        [
            ["Issues", "issues", "{{repo}} issue #{{issue_number}} - {{issue_title}}", "github.com/.../issues/{{issue_number}}"],
            ["Files", "files", "{{repo}} {{file_type}} - {{path}}", "github.com/.../{{root_ref}}/{{path_url}}"],
            ["Resolver", "resolver_cases", "{{label}}", "github.com/.../issues/{{issue_number}}"],
            ["Diag Cards", "—", "{{label}}", "github.com/.../issues/{{evidence_refs[0].id}}"],
        ]
    )

    # ========== SLIDE 14: KB Structure ==========
    add_content_slide(prs, "Structure de la KB — 1 datasource par série × type", [
        "## Organisation dans KB #793 :",
        "",
        "• STM32H7 Issues (#24406) — 8 fichiers, 359 docs",
        "• STM32H7 Files (#29041) — 16 fichiers, 5327 docs",
        "• STM32H7 Diagnostic Cards (#24408)",
        "• STM32H7 Resolver Cases (#24410)",
        "• STM32F4 Issues (#28099) — 7 fichiers, 1917 docs",
        "• STM32F4 Files (#29042) — 21 fichiers, 5948 docs",
        "• ... (même pattern pour chaque série)",
        "",
        "## Règle : les drivers vont dans la MÊME datasource",
        "• st_ready_issues_stm32h7xx-hal-driver.json → DS \"STM32H7 Issues\"",
        "• st_ready_files_cmsis_device_h7.json → DS \"STM32H7 Files\"",
    ])

    # ========== SLIDE 15: Checklist Nouvelle Série ==========
    add_content_slide(prs, "Checklist — Ajouter une Nouvelle Série", [
        "□ 1. Créer shared/config/config_<serie>.json (repos + clone_urls)",
        "□ 2. Ajouter mapping dans pipeline/delivery/delivery_paths.py",
        "□ 3. Lancer le pipeline complet :",
        "```   $env:STM32CUBE_CONFIG = \"shared/config/config_xx.json\"",
        "```   python -m pipeline.run_full_workflow --export-st-ready --continue-on-error",
        "  → Inclut automatiquement: delivery + export with_images + Alfred images",
        "□ 4. Vérifier by_series/<serie>/ : issues, files, diag, resolver, drivers/",
        "□ 5. Alfred PDF figures (si pdf_image_tasks non vide) :",
        "```   python pipeline_Automation/alfred/enrich_pdf_figures_with_alfred.py --repo <Repo>",
        "  → Puis re-run: files_to_docs_v2 + export_st_ready_files",
        "□ 6. Upload repo principal (new datasource × 4 types)",
        "□ 7. Upload issues with_images enrichies Alfred",
        "□ 8. Upload files PDF-enrichies (suffixe _pdf_enriched si déjà uploadé)",
        "□ 9. Mettre à jour Upload_All_Drivers.ps1 + upload_alfred_issues_all_series.py",
        "□ 10. Lancer Upload_All_Drivers.ps1",
        "□ 11. Vérifier: Get_Persona_KBs.py",
    ])

    # ========== SLIDE 16: Bonnes Pratiques ==========
    add_content_slide(prs, "Bonnes Pratiques", [
        "## Exécution",
        "• Toujours --continue-on-error (un sous-repo vide ne bloque pas)",
        "• --skip-ingestion pour re-processer sans re-télécharger",
        "• Vérifier summary_*.json avant upload (cohérence counts)",
        "",
        "## Upload",
        "• Ne pas uploader les fichiers vides (resolver_cases = [])",
        "• 1 datasource = 1 série + 1 type d'artifact",
        "• Les drivers vont dans la même datasource que le repo principal",
        "",
        "## Git",
        "• JAMAIS commit data/*.json (> 100 MB → push rejeté)",
        "• .gitignore exclut data/raw_*, data/clean_*, data/docs_*, data/chunks_*",
        "• datasets/07_delivery/ EST commité (< 50 MB, c'est le livrable)",
        "",
        "## Alfred",
        "• PAS besoin de --use-proxy (accès direct depuis réseau ST)",
        "• Vérifier 0 [IMAGE DESCRIPTION UNAVAILABLE] après enrichissement",
        "• Upload_All_Drivers.ps1 a un throttle de 5s + retry auto (rate limit API)",
    ])

    # ========== SLIDE 17: Dépannage ==========
    add_table_slide(prs, "Dépannage — Erreurs Courantes",
        ["Erreur", "Cause", "Solution"],
        [
            ["FileNotFoundError: with_images", "Série sans images", "Normal — skip Alfred"],
            ["empty JSON arrays", "Resolver vide", "Normal — série sans fix"],
            ["skipped_existing_files", "Fichier déjà dans DS", "Supprimer dans KB Mgmt ou --operation new"],
            ["GitHub file size > 100MB", "data/*.json dans git", "Vérifier .gitignore"],
            ["rate limit GitHub", "Trop d'appels API", "Attendre 1h ou ↑ issues_sleep"],
            ["Enrichment 0% sous-repo", "Pas de docs_issues_v2", "Normal pour BSP/CMSIS"],
            ["argparse error in workflow", "sys.argv pollution", "Fix: sys.argv isolé (déjà fait)"],
        ]
    )

    # ========== SLIDE 17b: Dépannage détaillé ==========
    add_content_slide(prs, "Dépannage — Explications détaillées", [
        '## "FileNotFoundError: st_ready_issues_with_images_*.json"',
        "• Le fichier with_images n'est généré QUE si des issues ont des [IMAGE ATTACHED]",
        "• Les sous-repos BSP/CMSIS n'ont souvent aucune image",
        "• → Le workflow skip automatiquement les séries sans images",
        "",
        '## "All selected files are empty JSON arrays"',
        "• Le resolver_cases.json contient [] car aucune issue n'a un fix documenté",
        "• Diagnostic cards ≠ resolver cases : diag décrit le problème, resolver le fix",
        "• → Normal, ne pas forcer l'upload (--empty-json-policy upload)",
        "",
        '## "skipped_existing_files: [fichier.json]"',
        "• Le fichier a déjà été uploadé dans ce datasource",
        "• L'API refuse les doublons par nom de fichier",
        "• → Supprimer l'ancien dans KB Management, puis re-uploader",
        "• → Ou créer un nouveau datasource (--operation new)",
    ])

    # ========== SLIDE 17c: Dépannage détaillé suite ==========
    add_content_slide(prs, "Dépannage — Explications (suite)", [
        '## "error: File exceeds GitHub file size limit of 100.00 MB"',
        "• Les fichiers data/ (raw, clean, docs, chunks) sont TRÈS gros",
        "• chunks_files_stm32cubec0_v2.json = 114 MB !",
        "• → Vérifier que .gitignore contient : data/raw_*, data/clean_*, data/docs_*, data/chunks_*",
        "• → Si déjà commité : git rm --cached data/<fichier>.json + amend commit",
        "",
        '## "rate limit" GitHub API',
        "• GitHub: 5000 req/h avec token, 60/h sans",
        "• Le pipeline fait beaucoup d'appels (issues + comments + PRs)",
        "• → Vérifier que $env:GITHUB_TOKEN est défini",
        "• → Augmenter issues_sleep dans config (0.2 → 0.5)",
        "• → Ou utiliser --skip-ingestion si les raw sont déjà là",
        "",
        '## "Enrichment 0% pour un sous-repo BSP"',
        "• Les sous-repos BSP/CMSIS ont très peu d'issues (souvent 0-5)",
        "• Le script d'évaluation ne trouve pas de docs_issues_*_v2.json dédié",
        "• → Normal, le contenu est agrégé dans le repo principal de la série",
    ])

    # ========== SLIDE 17d: Dépannage API rate limit ==========
    add_content_slide(prs, "Dépannage — Rate Limit API upload", [
        '## "Auth precheck failed. HTTP status=404" (nginx 404)',
        "• L'API api-ai-bridge.st.com rate-limite après ~20 requêtes rapides",
        "• Le reverse proxy nginx retourne 404 au lieu de 429",
        "",
        "## Fix déjà appliqué dans Upload_All_Drivers.ps1 :",
        "• $uploadDelaySec = 5 (pause entre chaque upload)",
        "• $retryCount = 2 (2 tentatives si échec)",
        "• $retryDelaySec = 30 (attente avant retry)",
        "",
        '## "skipped_existing_files" — fichier déjà dans la datasource',
        "• L'API refuse les fichiers ayant le même nom",
        "• Solution 1 : Supprimer l'ancien dans KB Management",
        "• Solution 2 : Renommer avec suffixe _pdf_enriched avant upload",
        "```Copy-Item st_ready_files_*.json st_ready_files_*_pdf_enriched.json",
        "",
        '## Proxy "502 Bad Gateway"',
        "• Le proxy 185.46.212.88 est parfois down",
        "• → Lancer SANS --use-proxy (accès direct depuis réseau ST)",
    ])

    # ========== SLIDE 18: Scripts d'automatisation ==========
    add_content_slide(prs, "Scripts d'Automatisation — Résumé", [
        "## Pipeline complet :",
        "```python -m pipeline.run_full_workflow --export-st-ready --continue-on-error",
        "",
        "## Upload drivers (toutes séries) :",
        "```.\\pipeline_Automation\\upload\\Upload_All_Drivers.ps1",
        "  → Parcourt by_series/*/drivers/, uploade chaque artifact, throttle 5s",
        "",
        "## Upload issues Alfred (toutes séries) :",
        "```python pipeline_Automation/upload/upload_alfred_issues_all_series.py",
        "  → Upload les with_images enrichis vers les datasources Issues",
        "",
        "## Batch toutes séries :",
        "```.\\pipeline_Automation\\workflow\\Run_Full_Auto_Update_KB.ps1",
        "",
        "## Vérification KB :",
        "```python pipeline_Automation/upload/Get_Persona_KBs.py",
    ])

    # ========== SLIDE 19: Résumé Final ==========
    add_title_slide(
        prs,
        "Résumé",
        "Config → Pipeline (23 steps) → Alfred → Upload → Vérification"
    )

    # Save
    output_path = Path(__file__).parent / "Atelier_Pratique_Pipeline_STM32Cube.pptx"
    prs.save(str(output_path))
    print(f"✓ Presentation saved: {output_path}")


if __name__ == "__main__":
    main()
