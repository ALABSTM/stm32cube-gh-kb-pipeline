"""Export enriched STM32Cube issue docs into ST-ready issue cards WITH image URLs.

This is the image-aware variant of `export_st_ready_issues.py`: it produces
the same structured issue cards but additionally extracts and carries the raw
image attachment URLs (`image_urls`) found in each issue. This variant is the
required input for the Alfred Vision enrichment step
(`pipeline_Automation/alfred/enrich_json_images_with_alfred.py`), which later
replaces `[IMAGE ATTACHED]` markers in the text with real image descriptions.

Inputs:
- `data/docs_issues_<repo>_v2.json`, produced by
  `pipeline/enrichment/issues_to_docs_v2.py`.
- `shared/config/config_all_series.json` (or `STM32CUBE_CONFIG`-selected
  config) for the list of repos and the `owner` used to build GitHub URLs.

Outputs (per repo), depending on `--output-format`:
- `json` (default), under `delivery_paths.get_repo_artifact_dir(repo, "issues_json")`:
  - `st_ready_issues_with_images_<repo>.json`: `{"issues": [...]}` array of
    issue cards, each with `image_urls`/`image_urls_count`/`images_count` and
    a composed `st_ready_text` retrieval document.
  - `summary_with_images_<repo>.json`: counts and export parameters.
  - A backward-compatible mirror under the legacy flat `st_ready/issues_json/`.
- `md`, under `delivery_paths.get_repo_artifact_dir(repo, "issues")`:
  - One Markdown knowledge card per issue, plus `manifest.csv`/`summary.json`.

After Alfred enrichment (run separately, not by this script), the file is
typically saved as
`issues_json/st_ready_issues_with_images_<repo>_with_alfred_image_text.json`.

Run:
    python -m pipeline.delivery.export_st_ready_issues_with_images --repo STM32CubeH7
"""

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from pipeline.delivery.delivery_paths import (
    get_legacy_artifact_file,
    get_repo_artifact_dir,
)
from shared.utils.paths import DATA_DIR, PROJECT_ROOT, get_config_path


def load_config() -> dict[str, Any]:
    """Load the active series config resolved via `get_config_path()`."""
    return json.loads(get_config_path().read_text(encoding="utf-8"))


def slugify(value: str, max_len: int = 80) -> str:
    """Convert `value` to a lowercase, hyphenated filename-safe slug."""
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if not text:
        return "untitled"
    return text[:max_len].strip("-")


def strip_title_and_body_prefix(clean_text: str) -> str:
    """Remove the leading `"Title: ...\\n\\nBody:\\n"` header the enrichment
    stage prepends to issue text, since the title is rendered separately.
    """
    text = clean_text or ""
    text = re.sub(r"^Title:\s*.*?\n\nBody:\n", "", text, flags=re.DOTALL)
    return text.strip()


def remove_noisy_comment_lines(text: str) -> str:
    """Strip bot/quote-header lines and sign-offs ("Best regards,", ...) from
    issue comment text so they don't dilute the retrieval-relevant content.
    """
    cleaned: list[str] = []
    for line in text.splitlines():
        ln = line.strip()
        if re.match(r"^\[[A-Za-z0-9_-]+\s-\s\d{4}-\d{2}-\d{2}T", ln):
            continue
        if ln.lower() in {
            "with regards,",
            "best regards,",
            "regards,",
            "thanks,",
        }:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def split_main_and_comments(clean_text: str) -> tuple[str, str]:
    """Split cleaned issue text into (main_body, comments) using the
    `"Comments:"` marker inserted by the enrichment stage.
    """
    text = strip_title_and_body_prefix(clean_text)
    marker = "\n\nComments:\n"
    if marker in text:
        main, comments = text.split(marker, 1)
        return main.strip(), comments.strip()
    return text, ""


def compact_comments(comments: str, max_chars: int) -> str:
    """Clean noisy lines from `comments`, collapse blank-line runs, and cap length."""
    if not comments:
        return ""
    text = remove_noisy_comment_lines(comments)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:max_chars].strip()


def normalize_whitespace(text: str) -> str:
    """Collapse any run of whitespace into a single space and strip ends."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    return cleaned


def first_sentence(text: str, max_chars: int = 280) -> str:
    """Return the first sentence of `text` (up to `max_chars`), or a hard cut."""
    s = normalize_whitespace(text)
    if not s:
        return ""
    # Strip image markers — root_cause_hint is a textual summary, images
    # will be described in the full Key comments section by Alfred.
    s = re.sub(r"\[IMAGE ATTACHED\]\s*", "", s).strip()
    if not s:
        return ""
    # Keep a short lead for retrieval while preserving technical tokens.
    match = re.search(r"[.!?]", s)
    if match and match.end() <= max_chars:
        return s[: match.end()].strip()
    return s[:max_chars].strip()


def dedupe_keep_order(values: list[str]) -> list[str]:
    """Remove duplicate strings while preserving first-seen order."""
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def extract_issue_image_urls(doc: dict[str, Any]) -> list[str]:
    """Extract valid http(s) image URLs from a doc's `image_urls` field.

    Accepts either a list or a single string for robustness against upstream
    schema variations, and silently drops any non-URL/malformed entries so
    the Alfred enrichment step only receives fetchable URLs.
    """
    raw = doc.get("image_urls")
    if isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, str):
        candidates = [raw]
    else:
        candidates = []

    image_urls: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        value = candidate.strip()
        if not value:
            continue
        if value.startswith("http://") or value.startswith("https://"):
            image_urls.append(value)

    return dedupe_keep_order(image_urls)


def build_keywords(doc: dict[str, Any], main_text: str) -> list[str]:
    """Build a deduped keyword list from structured metadata, labels, and
    technical anchor tokens (API-like identifiers) found in the issue text.
    """
    words: list[str] = []
    for key in ["mcu_series", "board", "layer", "component", "issue_kind", "severity"]:
        val = (doc.get(key) or "").strip()
        if val and val.lower() not in {"unknown", "other", "n/a"}:
            words.append(val)

    for lbl in doc.get("labels") or []:
        lbl_s = (lbl or "").strip()
        if lbl_s:
            words.append(lbl_s)

    # Preserve common technical anchors often used in support queries.
    anchor_re = re.compile(r"\b([A-Z]{2,}[A-Z0-9_\-]{1,}|[A-Za-z]+_[A-Za-z0-9_]+)\b")
    anchors = anchor_re.findall(main_text or "")
    words.extend(anchors[:20])

    deduped: list[str] = []
    seen: set[str] = set()
    for w in words:
        key = w.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(w)
        if len(deduped) >= 12:
            break
    return deduped


def compose_st_ready_text(doc: dict[str, Any], comments_chars: int) -> str:
    """Compose the retrieval-ready structured text body for one issue card.

    Renders a `Problem/Context/Root cause/Fix/Constraints/Keywords` header
    followed by the full technical body and (if present) compacted key
    comments. Image markers remain as `[IMAGE ATTACHED]` here; Alfred
    enrichment replaces them downstream with real descriptions.
    """
    main, comments = split_main_and_comments(doc.get("clean_text") or "")
    compact = compact_comments(comments, max_chars=comments_chars)

    issue_title = normalize_whitespace(doc.get("issue_title") or "")
    main_norm = normalize_whitespace(main)
    comments_norm = normalize_whitespace(compact)

    context_line = ", ".join(
        [
            f"repo={doc.get('repo')}",
            f"mcu_series={doc.get('mcu_series')}",
            f"board={doc.get('board')}",
            f"component={doc.get('component')}",
            f"layer={doc.get('layer')}",
            f"issue_kind={doc.get('issue_kind')}",
            f"severity={doc.get('severity')}",
            f"evidence_strength={doc.get('evidence_strength')}",
            f"rescue_applied={doc.get('rescue_applied')}",
            f"state={doc.get('state')}",
            f"issue_number={doc.get('issue_number')}",
        ]
    )

    keywords = build_keywords(doc, main_norm)
    keywords_str = ", ".join(keywords)

    root_cause_hint = first_sentence(comments_norm or main_norm, max_chars=260)
    fix_hint = first_sentence(main_norm, max_chars=320)

    lines = [
        f"Problem: {issue_title}",
        f"Context: {context_line}",
        f"Root cause: {root_cause_hint or 'Not explicitly stated in issue thread.'}",
        f"Fix: {fix_hint or 'Inspect issue details and follow accepted workaround.'}",
        "Constraints: Validate against exact MCU/board configuration and CubeMX/CubeH7 version before applying.",
        f"Keywords: {keywords_str}",
        "",
        "Technical details:",
        main_norm,
    ]
    if comments_norm:
        lines.extend(["", "Key comments:", comments_norm])
    return "\n".join(lines).strip()


def compose_st_ready_issue(doc: dict[str, Any], comments_chars: int) -> str:
    """Render one issue as a standalone Markdown knowledge card (`md` format).

    Reuses `compose_st_ready_text` for the content, then splits it into a
    `## Metadata` bullet list (first 12 header lines) followed by the body.
    """
    st_ready_text = compose_st_ready_text(doc, comments_chars=comments_chars)
    metadata_lines = st_ready_text.splitlines()[:12]
    body_text = "\n".join(st_ready_text.splitlines()[12:]).strip()

    sections = [
        "# STM32Cube Issue Knowledge Card",
        "",
        "## Metadata",
        *[f"- {line}" for line in metadata_lines],
        "",
        body_text,
    ]

    return "\n".join(sections).strip() + "\n"


def export_repo(repo: str, include_invalid: bool, comments_chars: int) -> tuple[int, int, Path]:
    """Export one repo's issues as individual Markdown cards (`--output-format md`).

    Writes one `.md` file per issue plus a `manifest.csv` (one row per issue)
    and a `summary.json`. Returns
    (total_docs_in_input, exported_docs_count, output_directory).
    """
    in_path = DATA_DIR / f"docs_issues_{repo.lower()}_v2.json"
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    out_root = get_repo_artifact_dir(repo, "issues")
    out_root.mkdir(parents=True, exist_ok=True)

    docs = json.loads(in_path.read_text(encoding="utf-8"))
    total = len(docs)
    exported = 0

    manifest_rows: list[dict[str, Any]] = []

    for doc in docs:
        if not include_invalid and not doc.get("is_valid", True):
            continue

        issue_number = doc.get("issue_number")
        title_slug = slugify(doc.get("issue_title") or "issue")
        file_name = f"issue_{issue_number}_{title_slug}.md"
        out_file = out_root / file_name

        payload = compose_st_ready_issue(doc, comments_chars=comments_chars)
        out_file.write_text(payload, encoding="utf-8")

        manifest_rows.append(
            {
                "id": doc.get("id"),
                "issue_number": issue_number,
                "issue_title": doc.get("issue_title"),
                "state": doc.get("state"),
                "layer": doc.get("layer"),
                "component": doc.get("component"),
                "issue_kind": doc.get("issue_kind"),
                "severity": doc.get("severity"),
                "is_valid": doc.get("is_valid"),
                "evidence_strength": doc.get("evidence_strength"),
                "rescue_applied": doc.get("rescue_applied"),
                "output_file": file_name,
                "output_chars": len(payload),
            }
        )
        exported += 1

    manifest_csv = out_root / "manifest.csv"
    with manifest_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()) if manifest_rows else [
            "id",
            "issue_number",
            "issue_title",
            "state",
            "layer",
            "component",
            "issue_kind",
            "severity",
            "is_valid",
            "evidence_strength",
            "rescue_applied",
            "output_file",
            "output_chars",
        ])
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow(row)

    summary = {
        "repo": repo,
        "input_file": str(in_path),
        "output_dir": str(out_root),
        "total_docs": total,
        "exported_docs": exported,
        "include_invalid": include_invalid,
        "comments_chars": comments_chars,
    }
    (out_root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return total, exported, out_root


def export_repo_json(repo: str, include_invalid: bool, comments_chars: int) -> tuple[int, int, Path]:
    """Export one repo's issues into `st_ready_issues_with_images_<repo>.json`
    (`--output-format json`, the default and the required input for Alfred
    image enrichment).

    Extracts `image_urls` per issue, writes the per-series output plus a
    legacy-flat mirror and a `summary_with_images_<repo>.json`. Returns
    (total_docs_in_input, exported_docs_count, output_directory).
    """
    in_path = DATA_DIR / f"docs_issues_{repo.lower()}_v2.json"
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    out_root = get_repo_artifact_dir(repo, "issues_json")
    out_root.mkdir(parents=True, exist_ok=True)

    cfg = load_config()
    owner = cfg.get("owner", "STMicroelectronics")
    url_base = f"https://github.com/{owner}/"

    docs = json.loads(in_path.read_text(encoding="utf-8"))
    total = len(docs)

    payload_docs: list[dict[str, Any]] = []
    for doc in docs:
        if not include_invalid and not doc.get("is_valid", True):
            continue

        image_urls = extract_issue_image_urls(doc)
        images_count = max(int(doc.get("images_count") or 0), len(image_urls))

        payload_docs.append(
            {
                "id": doc.get("id"),
                "url_base": url_base,
                "repo": doc.get("repo"),
                "root_path": "issues",
                "mcu_series": doc.get("mcu_series"),
                "issue_number": doc.get("issue_number"),
                "issue_title": doc.get("issue_title"),
                "state": doc.get("state"),
                "layer": doc.get("layer"),
                "component": doc.get("component"),
                "issue_kind": doc.get("issue_kind"),
                "severity": doc.get("severity"),
                "board": doc.get("board"),
                "labels": doc.get("labels") or [],
                "github_url": doc.get("github_url"),
                "image_urls": image_urls,
                "image_urls_count": len(image_urls),
                "images_count": images_count,
                "is_valid": doc.get("is_valid"),
                "evidence_strength": doc.get("evidence_strength"),
                "rescue_applied": doc.get("rescue_applied"),
                "delivery_template": "st_v2_structured_issue_card",
                "st_ready_text": compose_st_ready_text(doc, comments_chars=comments_chars),
            }
        )

    export_payload = {
        "issues": payload_docs,
    }

    out_file_name = f"st_ready_issues_with_images_{repo.lower()}.json"
    out_file = out_root / out_file_name
    out_file.write_text(json.dumps(export_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Backward-compatible mirror in legacy flat folder.
    legacy_out_file = get_legacy_artifact_file("issues_json", out_file_name)
    legacy_out_file.parent.mkdir(parents=True, exist_ok=True)
    legacy_out_file.write_text(json.dumps(export_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "repo": repo,
        "input_file": str(in_path),
        "output_file": str(out_file),
        "total_docs": total,
        "exported_docs": len(payload_docs),
        "include_invalid": include_invalid,
        "comments_chars": comments_chars,
        "format": "json",
        "root_tag_path": "issues",
    }
    summary_file_name = f"summary_with_images_{repo.lower()}.json"
    (out_root / summary_file_name).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    legacy_summary_file = get_legacy_artifact_file("issues_json", summary_file_name)
    legacy_summary_file.parent.mkdir(parents=True, exist_ok=True)
    legacy_summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return total, len(payload_docs), out_root


def main() -> None:
    """CLI entry point: export ST-ready issue cards with image URLs for each configured repo."""
    parser = argparse.ArgumentParser(description="Export docs_issues_v2 into ST-ready issue cards with image URLs.")
    parser.add_argument("--repo", action="append", help="Repo name, e.g., STM32CubeH7. Can be repeated.")
    parser.add_argument("--include-invalid", action="store_true", help="Include is_valid=false issues.")
    parser.add_argument(
        "--output-format",
        choices=["md", "json"],
        default="json",
        help="Export format. 'json' generates one file per repo; 'md' generates one file per issue.",
    )
    parser.add_argument(
        "--comments-chars",
        type=int,
        default=1200,
        help="Maximum number of comment characters to keep in each issue card.",
    )
    args = parser.parse_args()

    cfg = load_config()
    repos = args.repo or cfg.get("repos", [])

    if not repos:
        raise ValueError("No repos provided and no repos found in config.")

    for repo in repos:
        if args.output_format == "json":
            total, exported, out_root = export_repo_json(
                repo=repo,
                include_invalid=args.include_invalid,
                comments_chars=args.comments_chars,
            )
        else:
            total, exported, out_root = export_repo(
                repo=repo,
                include_invalid=args.include_invalid,
                comments_chars=args.comments_chars,
            )
        print(f"[ST-READY-WITH-IMAGES:{args.output_format}] {repo}: exported {exported}/{total} -> {out_root}")


if __name__ == "__main__":
    main()
