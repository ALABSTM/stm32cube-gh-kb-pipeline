import json
from pathlib import Path

IN_FILE = Path("data/clean_issues_stm32cubeh7.json")
OUT_FILE = Path("data/chunks_issues_stm32cubeh7.json")

def mcu_series_from_repo(repo: str | None) -> str | None:
    if not repo:
        return None
    repo = repo.upper()
    if "H7" in repo:
        return "H7"
    if "F4" in repo:
        return "F4"
    # à compléter 
    return None

def clean_issue_to_chunk(issue: dict, ingest_version: str = "v1.0") -> dict:
    repo = issue.get("repo")
    issue_number = issue.get("issue_number")

    text = issue.get("clean_text") or ""
    labels = issue.get("labels") or []
    labels_lower = [lbl.lower() for lbl in labels]
    is_confirmed_bug = any(lbl in ("bug", "internal bug tracker") for lbl in labels_lower)

    image_urls = issue.get("image_urls") or []
    images_count = issue.get("images_count") or 0

    chunk_index = 0
    chunk_count = 1

    metadata = {
        "source_kind": "issue",
        "repo": repo,
        "mcu_package": repo,
        "mcu_series": mcu_series_from_repo(repo),
        "type": "issue",
        "path": None,
        "github_url": issue.get("github_url"),
        "board": None,
        "category": None,
        "component": None,
        "example_name": None,
        "issue_number": issue_number,
        "issue_title": issue.get("title") or "",
        "state": issue.get("state"),
        "labels": labels,
        "is_confirmed_bug": is_confirmed_bug,
        "created_at": issue.get("created_at"),
        "closed_at": issue.get("closed_at"),
        "chunk_index": chunk_index,
        "chunk_count": chunk_count,
        "ingest_version": ingest_version,
        "image_urls": image_urls,
        "images_count": images_count,
    }

    chunk = {
        "id": f"{(repo or '').lower()}-issue-{issue_number}-{chunk_index}",
        "text": text,
        "metadata": metadata,
    }
    return chunk

def main():
    clean_issues = json.loads(IN_FILE.read_text(encoding="utf-8"))
    chunks = [clean_issue_to_chunk(issue, ingest_version="v1.0") for issue in clean_issues]

    OUT_FILE.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{len(chunks)} chunks écrits → {OUT_FILE}")

if __name__ == "__main__":
    main()