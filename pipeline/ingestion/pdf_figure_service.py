import json
import re
from pathlib import Path
from typing import Any

import cv2
import fitz

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None



def slugify(path_text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._/-]+", "_", path_text).strip("/")


def make_figure_id(repo_name: str, rel_path: str, page_number: int, figure_index: int) -> str:
    return f"{repo_name}:{rel_path}:p{page_number}:f{figure_index}"


# PDF text extraction


def extract_pdf_text_by_page(pdf_path: Path) -> list[str]:
    if PdfReader is None:
        print(f"[WARN] pypdf unavailable for {pdf_path}")
        return []

    try:
        reader = PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            pages.append((page.extract_text() or "").strip())
        return pages
    except Exception as exc:
        print(f"[WARN] Cannot extract PDF text by page from {pdf_path}: {exc}")
        return []


def extract_pdf_text_blocks(pdf_path: Path, zoom: float = 2.0) -> dict[int, list[dict[str, Any]]]:
    """
    Extrait les blocs texte avec leurs bounding boxes,
    remis à l’échelle du rendu utilisé pour les pages PNG.
    Retour:
    {
      1: [{"bbox": [x0,y0,x1,y1], "text": "..."}],
      2: [...],
      ...
    }
    """
    page_blocks: dict[int, list[dict[str, Any]]] = {}

    try:
        doc = fitz.open(str(pdf_path))
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            blocks = page.get_text("blocks")  # tuples
            items: list[dict[str, Any]] = []

            for blk in blocks:
                x0, y0, x1, y1, text, *_ = blk
                txt = (text or "").strip()
                if not txt:
                    continue

                items.append(
                    {
                        "bbox": [
                            int(x0 * zoom),
                            int(y0 * zoom),
                            int(x1 * zoom),
                            int(y1 * zoom),
                        ],
                        "text": txt,
                    }
                )

            page_blocks[page_idx + 1] = items

    except Exception as exc:
        print(f"[WARN] Cannot extract text blocks from {pdf_path}: {exc}")

    return page_blocks


# =========================
# PDF rendering
# =========================

def render_pdf_pages(pdf_path: Path, out_dir: Path, zoom: float = 2.0) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)

    rendered_pages: list[dict[str, Any]] = []

    doc = fitz.open(str(pdf_path))
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        page_number = page_idx + 1
        page_file = out_dir / f"page_{page_number:03d}.png"
        pix.save(str(page_file))

        rendered_pages.append(
            {
                "page_number": page_number,
                "image_path": str(page_file),
                "width": pix.width,
                "height": pix.height,
            }
        )

    return rendered_pages


# =========================
# Geometry helpers
# =========================

def rect_area_xywh(r: tuple[int, int, int, int]) -> int:
    return max(r[2], 0) * max(r[3], 0)


def rect_to_xyxy(r: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x, y, w, h = r
    return x, y, x + w, y + h


def xyxy_to_xywh(r: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = r
    return x0, y0, x1 - x0, y1 - y0


def intersection_area_xywh(a: tuple[int, int, int, int], b_xyxy: tuple[int, int, int, int]) -> int:
    ax0, ay0, ax1, ay1 = rect_to_xyxy(a)
    bx0, by0, bx1, by1 = b_xyxy

    ix0 = max(ax0, bx0)
    iy0 = max(ay0, by0)
    ix1 = min(ax1, bx1)
    iy1 = min(ay1, by1)

    if ix1 <= ix0 or iy1 <= iy0:
        return 0
    return (ix1 - ix0) * (iy1 - iy0)


def close_or_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int], gap: int = 30) -> bool:
    ax0, ay0, ax1, ay1 = rect_to_xyxy(a)
    bx0, by0, bx1, by1 = rect_to_xyxy(b)

    # overlap or near overlap
    return not (
        ax1 < bx0 - gap or
        bx1 < ax0 - gap or
        ay1 < by0 - gap or
        by1 < ay0 - gap
    )


def union_xywh(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    ax0, ay0, ax1, ay1 = rect_to_xyxy(a)
    bx0, by0, bx1, by1 = rect_to_xyxy(b)

    x0 = min(ax0, bx0)
    y0 = min(ay0, by0)
    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)

    return xyxy_to_xywh((x0, y0, x1, y1))


# =========================
# Figure detection (improved)
# =========================

def merge_close_regions(
    regions: list[tuple[int, int, int, int]],
    gap: int = 30,
) -> list[tuple[int, int, int, int]]:
    """
    Fusionne les régions chevauchantes ou proches.
    Meilleur que le merge overlap strict.
    """
    if not regions:
        return []

    pending = regions[:]
    merged: list[tuple[int, int, int, int]] = []

    while pending:
        current = pending.pop(0)
        changed = True

        while changed:
            changed = False
            remaining = []
            for r in pending:
                if close_or_overlap(current, r, gap=gap):
                    current = union_xywh(current, r)
                    changed = True
                else:
                    remaining.append(r)
            pending = remaining

        merged.append(current)

    merged.sort(key=lambda r: (r[1], r[0]))
    return merged


def text_overlap_ratio(
    region: tuple[int, int, int, int],
    text_blocks: list[dict[str, Any]],
) -> float:
    area = rect_area_xywh(region)
    if area <= 0:
        return 0.0

    overlap_sum = 0
    for blk in text_blocks:
        bbox = blk.get("bbox")
        if not bbox or len(bbox) != 4:
            continue
        overlap_sum += intersection_area_xywh(region, tuple(bbox))

    return min(overlap_sum / area, 1.0)


def looks_like_caption(text: str) -> bool:
    t = (text or "").strip().lower()
    caption_keywords = [
        "figure",
        "fig.",
        "diagram",
        "overview",
        "architecture",
        "workflow",
        "block diagram",
        "illustration",
    ]
    return any(k in t for k in caption_keywords)


def detect_candidate_figure_regions(
    page_image_path: Path,
    text_blocks: list[dict[str, Any]] | None = None,
) -> list[tuple[int, int, int, int]]:
    """
    Détection plus robuste :
    - On détecte des blobs graphiques
    - On fusionne mieux
    - On élimine les régions trop textuelles
    """
    img = cv2.imread(str(page_image_path))
    if img is None:
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h_img, w_img = gray.shape

    # Inversion threshold : texte/traits deviennent blancs
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # Morphologie pour grouper les éléments visuels
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    merged = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = 0.03 * (w_img * h_img)   # un peu plus strict qu'avant
    max_area = 0.92 * (w_img * h_img)

    regions: list[tuple[int, int, int, int]] = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h

        if area < min_area or area > max_area:
            continue

        if w < 180 or h < 140:
            continue

        ratio = w / max(h, 1)
        if ratio > 15 or ratio < 0.12:
            continue

        regions.append((x, y, w, h))

    # fusion plus aggressive
    regions = merge_close_regions(regions, gap=40)

    # filtre anti-texte
    filtered: list[tuple[int, int, int, int]] = []
    blocks = text_blocks or []

    for r in regions:
        overlap = text_overlap_ratio(r, blocks)

        # Si la région est couverte à >65% par des blocs texte,
        # elle ressemble trop à un paragraphe / screenshot de texte
        if overlap > 0.65:
            continue

        filtered.append(r)

    # si on a une légende "Figure..." à proximité, on peut garder la région associée
    # (pour le moment, le filtrage overlap suffit déjà bien)
    filtered.sort(key=lambda r: (r[1], r[0]))
    return filtered


# =========================
# Cropping
# =========================

def crop_figures_from_page(
    page_image_path: Path,
    regions: list[tuple[int, int, int, int]],
    out_dir: Path,
    repo_name: str,
    rel_path: str,
    page_number: int,
) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(page_image_path))
    if img is None:
        return []

    records: list[dict[str, Any]] = []

    for idx, (x, y, w, h) in enumerate(regions, start=1):
        crop = img[y:y + h, x:x + w]
        figure_id = make_figure_id(repo_name, rel_path, page_number, idx)
        file_name = f"page_{page_number:03d}_fig_{idx:03d}.png"
        file_path = out_dir / file_name

        cv2.imwrite(str(file_path), crop)

        records.append(
            {
                "figure_id": figure_id,
                "page_number": page_number,
                "figure_index": idx,
                "bbox": [int(x), int(y), int(w), int(h)],
                "path": str(file_path),
            }
        )

    return records


# =========================
# Tasks
# =========================

def build_pdf_figure_tasks(
    repo_name: str,
    rel_path: str,
    source_pdf_url: str,
    page_texts: list[str],
    figure_records: list[dict[str, Any]],
    descriptions_map: dict[str, str],
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []

    for rec in figure_records:
        figure_id = str(rec["figure_id"])
        if descriptions_map.get(figure_id):
            continue

        page_number = int(rec["page_number"])
        page_text = page_texts[page_number - 1] if 0 < page_number <= len(page_texts) else ""

        tasks.append(
            {
                "image_id": figure_id,  # compatibilité agent
                "repo": repo_name,
                "pdf_path": rel_path,
                "source_pdf_url": source_pdf_url,
                "page_number": page_number,
                "image_index": rec["figure_index"],
                "image_path": rec["path"],
                "bbox": rec["bbox"],
                "page_context_text": page_text[:3000],
                "prompt": (
                    "Describe this technical figure or diagram from the STM32Cube PDF. "
                    "Explain the visible blocks, labels, arrows, modules, interfaces, "
                    "and its role relative to the surrounding section. "
                    "If the crop is mostly plain text and not a real figure, say explicitly that it is not a useful diagram."
                ),
            }
        )

    return tasks


def write_pdf_figure_tasks(task_file: Path, tasks: list[dict[str, Any]]) -> None:
    lines = [json.dumps(t, ensure_ascii=False) for t in tasks]
    task_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def load_descriptions_map(desc_file: Path) -> dict[str, str]:
    if not desc_file.exists():
        return {}

    try:
        data = json.loads(desc_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[WARN] Cannot load descriptions file {desc_file}: {exc}")
        return {}

    if not isinstance(data, dict):
        return {}

    return {str(k): str(v) for k, v in data.items() if isinstance(v, str)}


# =========================
# Reinjection
# =========================

def inject_figure_descriptions_into_pages(
    page_texts: list[str],
    figure_records: list[dict[str, Any]],
    descriptions_map: dict[str, str],
) -> list[str]:
    page_to_figs: dict[int, list[dict[str, Any]]] = {}
    for rec in figure_records:
        page_to_figs.setdefault(int(rec["page_number"]), []).append(rec)

    enriched_pages: list[str] = []

    for idx, page_text in enumerate(page_texts, start=1):
        figs = page_to_figs.get(idx, [])
        figs.sort(key=lambda r: (r["bbox"][1], r["bbox"][0]))

        blocks = [page_text.strip()] if page_text.strip() else []

        if figs:
            blocks.append("")
            blocks.append("[FIGURE_DESCRIPTIONS]")
            for rec in figs:
                figure_id = str(rec["figure_id"])
                desc = descriptions_map.get(figure_id, "").strip()
                if not desc:
                    desc = (
                        f"Figure detected on page {idx}, but no technical description "
                        f"is available yet for {figure_id}."
                    )
                blocks.append(f"- {figure_id}: {desc}")
            blocks.append("[/FIGURE_DESCRIPTIONS]")

        enriched_pages.append("\n".join(blocks).strip())

    return enriched_pages


# =========================
# Main multimodal pipeline
# =========================

def extract_pdf_multimodal(
    pdf_path: Path,
    repo_name: str,
    rel_path: str,
    source_pdf_url: str,
    data_dir: Path,
) -> dict[str, Any]:
    """
    Pipeline complet :
    - texte page par page
    - blocs texte
    - rendu des pages
    - détection des figures
    - crops
    - génération des tâches
    - chargement descriptions existantes
    - réinjection dans le texte
    """
    zoom = 2.0

    page_texts = extract_pdf_text_by_page(pdf_path)
    page_text_blocks = extract_pdf_text_blocks(pdf_path, zoom=zoom)

    render_dir = data_dir / "pdf_pages" / repo_name.lower() / slugify(rel_path).replace("/", "_")
    rendered_pages = render_pdf_pages(pdf_path, render_dir, zoom=zoom)

    figure_dir = data_dir / "pdf_figures" / repo_name.lower() / slugify(rel_path).replace("/", "_")
    all_figure_records: list[dict[str, Any]] = []

    for page_info in rendered_pages:
        page_number = int(page_info["page_number"])
        page_image_path = Path(page_info["image_path"])

        text_blocks = page_text_blocks.get(page_number, [])
        regions = detect_candidate_figure_regions(
            page_image_path=page_image_path,
            text_blocks=text_blocks,
        )

        figure_records = crop_figures_from_page(
            page_image_path=page_image_path,
            regions=regions,
            out_dir=figure_dir,
            repo_name=repo_name,
            rel_path=rel_path,
            page_number=page_number,
        )
        all_figure_records.extend(figure_records)

    desc_file = data_dir / "pdf_image_descriptions.json"
    descriptions_map = load_descriptions_map(desc_file)

    tasks = build_pdf_figure_tasks(
        repo_name=repo_name,
        rel_path=rel_path,
        source_pdf_url=source_pdf_url,
        page_texts=page_texts,
        figure_records=all_figure_records,
        descriptions_map=descriptions_map,
    )

    task_file = data_dir / f"pdf_image_tasks_{repo_name.lower()}.jsonl"
    write_pdf_figure_tasks(task_file, tasks)

    enriched_pages = inject_figure_descriptions_into_pages(
        page_texts=page_texts,
        figure_records=all_figure_records,
        descriptions_map=descriptions_map,
    )

    content = "\n\n".join([p for p in enriched_pages if p.strip()]).strip()

    return {
        "content": content,
        "figure_records": all_figure_records,
        "figures_count": len(all_figure_records),
        "task_file": str(task_file),
        "rendered_pages_count": len(rendered_pages),
        "content_extractor": "pypdf+render+opencv+text-filter",
    }