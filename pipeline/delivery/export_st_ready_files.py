import argparse
import json
import re
from pathlib import Path
from typing import Any

from shared.utils.paths import DATA_DIR, PROJECT_ROOT, get_config_path


def load_config() -> dict[str, Any]:
    return json.loads(get_config_path().read_text(encoding="utf-8"))


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def first_sentence(text: str, max_chars: int = 320) -> str:
    s = normalize_whitespace(text)
    if not s:
        return ""
    match = re.search(r"[.!?]", s)
    if match and match.end() <= max_chars:
        return s[: match.end()].strip()
    return s[:max_chars].strip()


def compose_st_ready_text(doc: dict[str, Any]) -> str:
    clean = normalize_whitespace(doc.get("clean_text") or "")
    snippet = first_sentence(clean, max_chars=360)

    context_line = ", ".join(
        [
            f"repo={doc.get('repo')}",
            f"mcu_series={doc.get('mcu_series')}",
            f"file_type={doc.get('file_type')}",
            f"path={doc.get('path')}",
            f"board={doc.get('board')}",
            f"component={doc.get('component')}",
            f"category={doc.get('category')}",
            f"example_name={doc.get('example_name')}",
        ]
    )

    lines = [
        f"Document: {doc.get('path') or 'unknown'}",
        f"Context: {context_line}",
        f"Summary: {snippet or 'Technical reference document extracted from STM32Cube repository.'}",
        "Constraints: Validate against exact STM32 series/board and firmware package before applying.",
        "",
        "Technical details:",
        clean,
    ]
    return "\n".join(lines).strip()


def export_repo_json(repo: str, include_invalid: bool) -> tuple[int, int, Path]:
    in_path = DATA_DIR / f"docs_files_{repo.lower()}_v2.json"
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    out_root = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "files_json"
    out_root.mkdir(parents=True, exist_ok=True)

    docs = json.loads(in_path.read_text(encoding="utf-8"))
    total = len(docs)

    payload_docs: list[dict[str, Any]] = []
    for doc in docs:
        if not include_invalid and not doc.get("is_valid", True):
            continue

        payload_docs.append(
            {
                "id": doc.get("id"),
                "repo": doc.get("repo"),
                "mcu_series": doc.get("mcu_series"),
                "path": doc.get("path"),
                "file_type": doc.get("file_type"),
                "board": doc.get("board"),
                "category": doc.get("category"),
                "component": doc.get("component"),
                "example_name": doc.get("example_name"),
                "github_url": doc.get("github_url"),
                "is_valid": doc.get("is_valid"),
                "delivery_template": "st_v2_structured_file_card",
                "st_ready_text": compose_st_ready_text(doc),
            }
        )

    out_file = out_root / f"st_ready_files_{repo.lower()}.json"
    out_file.write_text(json.dumps(payload_docs, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "repo": repo,
        "input_file": str(in_path),
        "output_file": str(out_file),
        "total_docs": total,
        "exported_docs": len(payload_docs),
        "include_invalid": include_invalid,
        "format": "json",
    }
    (out_root / f"summary_files_{repo.lower()}.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    return total, len(payload_docs), out_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Export docs_files_v2 into ST-ready JSON file cards.")
    parser.add_argument("--repo", action="append", help="Repo name, e.g., STM32CubeH7. Can be repeated.")
    parser.add_argument("--include-invalid", action="store_true", help="Include is_valid=false docs.")
    args = parser.parse_args()

    cfg = load_config()
    repos = args.repo or cfg.get("repos", [])

    if not repos:
        raise ValueError("No repos provided and no repos found in config.")

    for repo in repos:
        total, exported, out_root = export_repo_json(repo=repo, include_invalid=args.include_invalid)
        print(f"[ST-READY:json:files] {repo}: exported {exported}/{total} -> {out_root}")


if __name__ == "__main__":
    main()
