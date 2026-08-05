"""
Patch PDF figure descriptions into existing delivery files.

Instead of re-running the full pipeline (40+ min), this script directly replaces
placeholder text in st_ready_files_*.json with actual Alfred descriptions from
data/pdf_image_descriptions.json.

Usage:
    python pipeline_Automation/patch_pdf_descriptions_in_delivery.py
    python pipeline_Automation/patch_pdf_descriptions_in_delivery.py --dry-run
"""

import argparse
import json
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DELIVERY_DIR = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "by_series"
DESCRIPTIONS_FILE = DATA_DIR / "pdf_image_descriptions.json"

PLACEHOLDER_PATTERN = re.compile(
    r"Figure detected on page \d+, but no technical description is available yet for ([^\s]+:p\d+:f\d+)\."
)


def load_descriptions() -> dict[str, str]:
    """Load the Alfred-generated figure_id -> description mapping from disk.

    Returns an empty dict (with an error message) if the descriptions file is
    missing or not a JSON object.
    """
    if not DESCRIPTIONS_FILE.exists():
        level = "INFO" if os.environ.get("GITHUB_ACTIONS") == "true" else "WARN"
        print(f"[{level}] Descriptions file not found: {DESCRIPTIONS_FILE}")
        print("[INFO] PDF patch step is optional; continuing without Alfred PDF descriptions.")
        return {}
    try:
        data = json.loads(DESCRIPTIONS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[WARN] Failed to parse descriptions JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        print("[WARN] Descriptions JSON is not an object; skipping PDF patch.")
        return {}
    return {str(k): str(v) for k, v in data.items() if isinstance(v, str)}


def patch_file(file_path: Path, descriptions: dict[str, str], dry_run: bool = False) -> int:
    """Patch a single delivery JSON file. Returns number of replacements made."""
    content = file_path.read_text(encoding="utf-8")

    replacements = 0

    def replace_placeholder(match: re.Match) -> str:
        """Replace one "no technical description available yet" placeholder with its real description, if known."""
        nonlocal replacements
        figure_id = match.group(1)
        desc = descriptions.get(figure_id, "").strip()
        if desc:
            replacements += 1
            # Escape for JSON string context: newlines, tabs, backslashes, quotes
            desc = desc.replace("\\", "\\\\")
            desc = desc.replace('"', '\\"')
            desc = desc.replace("\n", "\\n")
            desc = desc.replace("\r", "\\r")
            desc = desc.replace("\t", "\\t")
            return desc
        return match.group(0)  # Keep original if no description found

    patched = PLACEHOLDER_PATTERN.sub(replace_placeholder, content)

    if replacements > 0 and not dry_run:
        file_path.write_text(patched, encoding="utf-8")

    return replacements


def main():
    """CLI entry point: patch placeholder figure descriptions across all delivery files in place."""
    parser = argparse.ArgumentParser(description="Patch PDF descriptions into delivery files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without writing")
    args = parser.parse_args()

    descriptions = load_descriptions()
    if not descriptions:
        print("[INFO] No descriptions loaded. Skipping PDF patch step.")
        return

    print(f"Loaded {len(descriptions)} PDF figure descriptions from {DESCRIPTIONS_FILE.name}")
    print(f"Scanning delivery files in: {DELIVERY_DIR}")
    print(f"{'DRY RUN - no files will be modified' if args.dry_run else 'LIVE - files will be patched'}")
    print("=" * 60)

    total_replacements = 0
    files_patched = 0

    # Find all file delivery JSONs, including driver/subrepo exports under drivers/*/files_json/.
    patterns = ("st_ready_files_*.json", "*_pdf_enriched*.json")
    candidates = []
    for pattern in patterns:
        candidates.extend(DELIVERY_DIR.rglob(pattern))

    for json_file in sorted(set(candidates)):
        if "summary" in json_file.name:
            continue
        if json_file.parent.name != "files_json":
            continue

        count = patch_file(json_file, descriptions, dry_run=args.dry_run)
        if count > 0:
            print(f"  {json_file.relative_to(PROJECT_ROOT)}: {count} descriptions injected")
            total_replacements += count
            files_patched += 1

    print("=" * 60)
    print(f"Total: {total_replacements} placeholders replaced in {files_patched} files")
    if args.dry_run:
        print("(dry run — re-run without --dry-run to apply)")


if __name__ == "__main__":
    main()
