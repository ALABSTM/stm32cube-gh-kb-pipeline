"""
Generate Atelier Pratique presentation slides (PPTX).
Run: python docs/generate_atelier_slides.py
Output: docs/Atelier_Pratique_Pipeline_STM32Cube_updated.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pathlib import Path

OUTPUT = Path(__file__).parent / "Atelier_Pratique_Pipeline_STM32Cube_updated.pptx"

# ST colors
ST_BLUE = RGBColor(0x1A, 0x23, 0x7E)
ST_LIGHT_BLUE = RGBColor(0xC8, 0xDC, 0xFF)
ST_ORANGE = RGBColor(0xFF, 0x98, 0x00)
ST_GREEN = RGBColor(0x4C, 0xAF, 0x50)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
GRAY = RGBColor(0x60, 0x60, 0x60)


def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title_slide(prs, title, subtitle):
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank
    set_slide_bg(slide, WHITE)
    # Title
    txBox = slide.shapes.add_textbox(Cm(1.5), Cm(3), Cm(22), Cm(3))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = ST_BLUE
    p.alignment = PP_ALIGN.CENTER
    # Subtitle
    p2 = tf.add_paragraph()
    p2.text = subtitle
    p2.font.size = Pt(18)
    p2.font.color.rgb = GRAY
    p2.alignment = PP_ALIGN.CENTER
    return slide


def add_content_slide(prs, title, bullets, notes=""):
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank
    set_slide_bg(slide, WHITE)
    # Title bar
    txBox = slide.shapes.add_textbox(Cm(1), Cm(0.5), Cm(23), Cm(1.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = ST_BLUE
    # Body
    txBox2 = slide.shapes.add_textbox(Cm(1.5), Cm(2.8), Cm(22), Cm(14))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True
    for i, bullet in enumerate(bullets):
        if i == 0:
            p = tf2.paragraphs[0]
        else:
            p = tf2.add_paragraph()
        p.text = bullet
        p.font.size = Pt(14)
        p.font.color.rgb = BLACK
        p.space_after = Pt(6)
    # Speaker notes
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def add_diagram_slide(prs, title, diagram_text, notes=""):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    set_slide_bg(slide, WHITE)
    # Title
    txBox = slide.shapes.add_textbox(Cm(1), Cm(0.5), Cm(23), Cm(1.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = ST_BLUE
    # Diagram (monospace)
    txBox2 = slide.shapes.add_textbox(Cm(0.8), Cm(2.5), Cm(23.5), Cm(14.5))
    tf2 = txBox2.text_frame
    tf2.word_wrap = False
    for i, line in enumerate(diagram_text.split("\n")):
        if i == 0:
            p = tf2.paragraphs[0]
        else:
            p = tf2.add_paragraph()
        p.text = line
        p.font.size = Pt(10)
        p.font.name = "Consolas"
        p.font.color.rgb = BLACK
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def add_table_slide(prs, title, headers, rows, notes=""):
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    set_slide_bg(slide, WHITE)
    # Title
    txBox = slide.shapes.add_textbox(Cm(1), Cm(0.5), Cm(23), Cm(1.8))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = ST_BLUE
    # Table
    n_rows = len(rows) + 1
    n_cols = len(headers)
    left = Cm(1.5)
    top = Cm(3)
    width = Cm(22)
    height = Cm(0.8 * n_rows)
    table = slide.shapes.add_table(n_rows, n_cols, left, top, width, height).table
    # Header
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = ST_BLUE
        for para in cell.text_frame.paragraphs:
            para.font.color.rgb = WHITE
            para.font.bold = True
            para.font.size = Pt(12)
    # Rows
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = str(val)
            for para in cell.text_frame.paragraphs:
                para.font.size = Pt(11)
    if notes:
        slide.notes_slide.notes_text_frame.text = notes
    return slide


def main():
    prs = Presentation()
    prs.slide_width = Cm(25.4)
    prs.slide_height = Cm(19.05)

    # ===== SLIDE 0: Title =====
    add_title_slide(
        prs,
        "Atelier Pratique — Pipeline STM32Cube",
        "Vue d'ensemble • Images & Alfred • Architecture KB • Cleaning → Enrichment"
    )

    # ===== SLIDE 1: Vue d'ensemble =====
    pipeline_diagram = """\
┌─────────────┐    ┌───────────┐    ┌──────────────┐    ┌────────────┐    ┌──────────┐    ┌────────────┐    ┌──────────┐
│ 1. Ingestion│───▶│2. Cleaning│───▶│3. Enrichment │───▶│4. Similarité│───▶│5. Chunking│───▶│6. Validation│───▶│7. Delivery│
│ fetch_*     │    │ V1 + V3   │    │ NLP + Alfred │    │ TF-IDF     │    │ 512 tok   │    │ JSON Schema│    │ 4 types  │
└─────────────┘    └───────────┘    └──────────────┘    └────────────┘    └──────────┘    └────────────┘    └──────────┘
      ▲                                                                                                          │
      │                                                                                                          ▼
 GitHub API                                                                                                 KB #793
 25 séries                                                                                             ST ChatGPT
 200+ repos                                                                                            GPT-5.1"""

    add_diagram_slide(
        prs,
        "1. Vue d'Ensemble — Pipeline 7 Stages",
        pipeline_diagram,
        notes="Le pipeline transforme les données brutes de 25 séries STM32 GitHub en 4 types d'artefacts "
              "structurés pour un chatbot IA spécialisé. Chaque stage est rejouable indépendamment."
    )

    add_table_slide(
        prs,
        "1. Chiffres Clés du Pipeline",
        ["Donnée", "Valeur"],
        [
            ["Séries couvertes", "25 (13 prod, 12 config)"],
            ["Repos GitHub", "200+"],
            ["Issues traitées", "~3 350"],
            ["Files documentés", "~14 000"],
            ["Diagnostic Cards", "~157"],
            ["Resolver Cases", "~390"],
            ["KB Datasources", "38"],
        ],
        notes="Points à souligner : 4 types d'artefacts complémentaires, pipeline modulaire et traçable."
    )

    # ===== SLIDE 2: Problème images + Alfred =====
    before_after = """\
AVANT (opaque pour le RAG) :
─────────────────────────────
Issue #42: "HAL_SPI fails on H743"
Body: "See screenshot below"
[IMAGE ATTACHED: screenshot_debugger.png]    ← INVISIBLE pour la recherche !


APRÈS enrichissement Alfred Vision :
─────────────────────────────
Issue #42: "HAL_SPI fails on H743"
Body: "See screenshot below"
[IMAGE DESCRIPTION] The screenshot shows STM32CubeIDE debugger with a hard fault
at address 0x08001234 in HAL_SPI_TxRxCpltCallback. The call stack shows DMA IRQ
handler triggered from SPI1 peripheral. D-cache is enabled in MPU config panel.

→ La capture d'écran est maintenant CHERCHABLE par le RAG !"""

    add_diagram_slide(
        prs,
        "2. Le Problème des Images — Avant / Après Alfred",
        before_after,
        notes="Alfred Vision (Azure OpenAI interne ST) analyse les captures d'écran et produit une description "
              "textuelle orientée diagnostic. Les screenshots deviennent exploitables par la recherche hybride."
    )

    add_table_slide(
        prs,
        "2. Résultats Alfred — Confiance Contextuelle",
        ["Source", "Évalués", "Score moyen", "Confiance"],
        [
            ["Images d'issues GitHub", "200", "0.5021", "98.5%"],
            ["Figures PDF", "242", "0.1825", "41.7%"],
            ["Total Alfred", "442", "0.3270", "67.4%"],
        ],
        notes="La confiance contextuelle mesure si la description Alfred est cohérente avec le texte de l'issue. "
              "98.5% pour les images d'issues = très fiable. 41.7% pour les PDF = contexte de page insuffisant."
    )

    add_content_slide(
        prs,
        "2. Fiabilité Opérationnelle Alfred",
        [
            "• Séries stabilisées (H7, F4, WL, F7) : 99.1% de succès",
            "• 234 images soumises → 232 descriptions produites → 2 échecs (URL 404)",
            "",
            "• 242 figures PDF détectées (OpenCV) sur 19 séries",
            "• 242/242 décrites par Alfred (100% succès opérationnel)",
            "• 0 placeholder résiduel après patch",
            "",
            "• Score de cohérence : S_coh = (0.4×L + 0.6×S) × (1 - 0.8×P_contrad)",
            "  - L = ancrage lexical (mots communs Alfred ↔ contexte)",
            "  - S = similarité sémantique (Jaccard + cosinus trigrammes)",
            "  - P_contrad = pénalité contradiction (polarité opposée)",
            "• Seuil d'alerte : S_coh < 0.12 → description suspecte",
        ],
        notes="La confiance n'est pas juste un taux de succès API. On vérifie que la description est ancrée "
              "dans le contexte textuel de l'image."
    )

    # ===== SLIDE 3: Architecture multi-agents =====
    agents_diagram = """\
                    ┌─────────────────────────────────┐
                    │  Persona: ST GitHub Analyzer     │
     Question      │  (GPT-5.1 via Azure OpenAI)      │
  ──────────────▶  │                                   │
  Ingénieur STM32  └─────────┬───────────────┬─────────┘
                             │               │
                    ALWAYS   │               │  ONLY if KB empty
                    FIRST    ▼               ▼
              ┌──────────────────┐    ┌──────────────────┐
              │ Tool KB #793     │    │ Tool NovaX       │
              │ Unstructured     │    │ Fallback         │
              │ Hybrid Search    │    │ Bugzilla +       │
              │ (Sem 0.55 + FT)  │    │ STCommunity      │
              │ 25 docs + 12 FT  │    │                  │
              └──────────────────┘    └──────────────────┘
                       ▲
                       │ Upload JSON (pipeline automatisé)
              ┌──────────────────┐
              │ Pipeline 7 stages│
              │ 25 séries STM32  │
              └──────────────────┘"""

    add_diagram_slide(
        prs,
        "3. Architecture Multi-Agents — KB-First",
        agents_diagram,
        notes="L'architecture force la priorité KB. NovaX n'est appelé que si la KB ne retourne rien. "
              "Sans cette restriction, le QI chute de 10 points car la persona court-circuite la KB."
    )

    add_table_slide(
        prs,
        "3. Paramètres KB Retenus",
        ["Paramètre", "Valeur", "Alternative testée"],
        [
            ["Search Type", "Hybrid", "Semantic seul (QI=41), Full-text seul (QI=47)"],
            ["Semantic Threshold", "0.55 (S0) / 0.45 (S1)", "0.65 (QI=63, trop restrictif)"],
            ["Semantic Max Docs", "25 (S0) / 35 (S1)", "15 (QI=47, trop peu)"],
            ["Full-text Max Docs", "12", "20 (surcharge contexte)"],
            ["Fallback", "NovaX restrictif", "Alfred permissif (QI -10)"],
            ["Modèle", "GPT-5.1", "GPT-4o (précédent)"],
        ],
        notes="S1 (threshold=0.45, 35+15 docs) obtient le meilleur score QI=66 sur 96 questions."
    )

    # ===== SLIDE 4: Cleaning → Enrichment =====
    v3_tree = """\
raw_files_*.json
       │
       ▼
┌──────────────────────┐
│   detect_file_type() │
└────────┬─────────────┘
         │
    ┌────┼─────────────────┬───────────────────┬─────────────────────┐
    ▼    ▼                 ▼                   ▼                     ▼
Release  README           Source              CMSIS > 100Ko         Autre
Notes    (.md)            (.c/.h)             (stm32*xx.h)
    │    │                 │                   │                     │
    ▼    ▼                 ▼                   ▼                     ▼
strip_   clean_           strip_              filter_cmsis()        passthrough
html()   markdown()       license()           (IRQ + base addr      (inchangé)
                                              + TypeDef seulement)
 -33%    -15%             -10%                -96% !!!              0%

Exemple CMSIS :  stm32h743xx.h  1 458 301 → 52 140 caractères  (-96.4%)
Résultat :       clean_files_<repo>_v3.json   (+31% densité signal/chunk)"""

    add_diagram_slide(
        prs,
        "4a. Cleaning V3 — Nettoyage Type-Aware",
        v3_tree,
        notes="Le V3 adapte la stratégie de nettoyage au type de fichier. Le gain majeur est sur les CMSIS "
              "headers qui passent de 1.7 Mo à 52 Ko en ne gardant que IRQ, base addresses et TypeDef."
    )

    enrichment_issues = """\
clean_issues_<repo>.json
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  issues_to_docs_v2.py — Heuristiques NLP regex STM32    │
│                                                          │
│  Champs ajoutés :                                        │
│  ├── layer      → HAL / BSP / CMSIS / MW / APP          │
│  ├── component  → SPI / I2C / UART / DMA / USB / ETH    │
│  ├── severity   → high / medium / low                   │
│  ├── board      → NUCLEO-H743ZI / STM32H750B-DK / ...   │
│  ├── issue_kind → bug_report / question / feature        │
│  └── is_valid   → true/false (filtre spam/vide)          │
│                                                          │
│  Pas de ML supervisé → regex domain-specific STM32       │
│  Déterministe, explicable, sans données d'entraînement   │
└─────────────────────────────────────────────────────────┘
         │
         ▼
docs_issues_<repo>_v2.json"""

    add_diagram_slide(
        prs,
        "4b. Enrichissement Issues — Heuristiques NLP",
        enrichment_issues,
        notes="L'enrichissement ajoute des métadonnées structurées par heuristiques regex. "
              "Pas de ML = déterministe et explicable. Couverture : layer 88%, severity 100%, component 73%."
    )

    enrichment_files = """\
clean_files_<repo>_v3.json
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  files_to_docs_v2.py — Classification + Métadonnées     │
│                                                          │
│  Champs ajoutés :                                        │
│  ├── file_type  → source_code / release_notes / readme  │
│  │               / cmsis_device_header / documentation_pdf│
│  ├── board      → détecté depuis le path BSP            │
│  ├── component  → détecté depuis le nom du fichier      │
│  ├── example_name → nom du projet exemple               │
│  └── is_valid   → true si clean_text > 100 caractères   │
└─────────────────────────────────────────────────────────┘
         │
         ▼
docs_files_<repo>_v3.json
         │
         ▼  (puis Similarité TF-IDF pour les issues)
         │
docs_issues_<repo>_v2_sim.json  (avec related_issue_ids)
         │
         ▼  (puis Delivery → 4 artefacts ST-ready)
         │
st_ready_issues_*.json / st_ready_files_*.json / resolver / diagnostic"""

    add_diagram_slide(
        prs,
        "4c. Enrichissement Files + Flux vers Delivery",
        enrichment_files,
        notes="Les fichiers sont classifiés par type, puis les métadonnées board/component sont extraites. "
              "Le tout alimente la delivery qui produit les 4 types d'artefacts uploadés vers la KB."
    )

    add_table_slide(
        prs,
        "4d. Couverture Enrichissement (H7, 296 docs)",
        ["Champ", "Score", "Seuil", "Verdict"],
        [
            ["Validité", "86.4%", "≥85%", "BON"],
            ["Layer", "88.2%", "≥85%", "BON"],
            ["Severity", "100%", "≥90%", "EXCELLENT"],
            ["Component", "72.6%", "≥70%", "ACCEPTABLE"],
            ["Board", "45.3%", "≥60%", "INSUFFISANT*"],
        ],
        notes="*Board insuffisant car le signal est absent des données : 92% des issues sans board détectée "
              "ne mentionnent effectivement aucune carte. L'heuristique fonctionne, le signal manque."
    )

    # ===== SLIDE 5: Score global =====
    add_table_slide(
        prs,
        "5. Score Global du Pipeline — 87.1%",
        ["Stage", "Score", "Poids", "Verdict"],
        [
            ["1. Ingestion", "99.7%", "1.0", "EXCELLENT"],
            ["2. Cleaning", "100.0%", "1.5", "EXCELLENT"],
            ["3a. Enrichissement NLP", "72.2%", "1.4", "ACCEPTABLE"],
            ["3b. Alfred images issues", "98.5%", "0.4", "EXCELLENT"],
            ["3c. Alfred figures PDF", "41.7%", "0.2", "INSUFFISANT"],
            ["4. Similarité TF-IDF", "22.0%", "0.5", "INSUFFISANT"],
            ["5. Delivery", "100.0%", "2.0", "EXCELLENT"],
            ["GLOBAL", "87.1%", "Σ=7.0", "BON"],
        ],
        notes="Score global = moyenne pondérée. Delivery a le poids max (2.0) car c'est l'étape critique "
              "qui produit les Diagnostic Cards (+33 pts QI). Similarité a un poids réduit (0.5) car un "
              "score bas n'impacte pas la qualité perçue."
    )

    # ===== Save =====
    prs.save(str(OUTPUT))
    print(f"✅ Présentation générée : {OUTPUT}")
    print(f"   {len(prs.slides)} slides créées")


if __name__ == "__main__":
    main()
