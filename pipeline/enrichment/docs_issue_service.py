from typing import Any

from pipeline.chunking.chunk_service import mcu_series_from_repo


def clean_issue_to_doc(issue: dict[str, Any], ingest_version: str = "v1.0") -> dict[str, Any]:
    repo = issue.get("repo")
    issue_number = issue.get("issue_number")
    labels = issue.get("labels") or []
    labels_lower = [lbl.lower() for lbl in labels]
    is_confirmed_bug = any(lbl in ("bug", "internal bug tracker") for lbl in labels_lower)

    doc_id = f"{(repo or '').lower()}-issue-{issue_number}"

    clean_text = issue.get("clean_text") or ""
    image_urls = issue.get("image_urls") or []
    images_count = issue.get("images_count") or 0

    return {
        "id": doc_id,
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
        "ingest_version": ingest_version,
        "clean_text": clean_text,
        "image_urls": image_urls,
        "images_count": images_count,
    }
