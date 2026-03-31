from typing import Any


def mcu_series_from_repo(repo: str | None) -> str | None:
    if not repo:
        return None
    repo = repo.upper()
    if "H7" in repo:
        return "H7"
    if "F4" in repo:
        return "F4"
    if "H5" in repo:
        return "H5"
    # Add other series as needed
    return None


def split_by_paragraphs(text: str, max_chars: int = 1200) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for p in paragraphs:
        # 1) If a paragraph is too long, split it into sub-blocks
        while len(p) > max_chars:
            chunks.append(p[:max_chars])
            p = p[max_chars:]

        # 2) Concatenate multiple paragraphs as long as we stay under max_chars
        if len(current) + len(p) + 2 <= max_chars:
            current = (current + "\n\n" + p).strip() if current else p.strip()
        else:
            if current:
                chunks.append(current)
            current = p.strip()

    if current:
        chunks.append(current)

    return chunks


def doc_issue_to_chunks(doc: dict[str, Any], max_chars: int = 1200) -> list[dict[str, Any]]:
    """
    Transform an enriched "issue" document into a list of chunks ready for ingestion.
    """
    text = doc.get("clean_text") or ""
    parts = split_by_paragraphs(text, max_chars=max_chars)

    chunks: list[dict[str, Any]] = []

    if not parts:
        parts = [text]

    chunk_count = len(parts)
    base_id = doc.get("id") or "unknown-doc"

    for idx, part in enumerate(parts):
        metadata = dict(doc) 
        metadata.pop("clean_text", None)

        metadata["chunk_index"] = idx
        metadata["chunk_count"] = chunk_count

        chunk = {
            "id": f"{base_id}-{idx}",
            "text": part,
            "metadata": metadata,
        }
        chunks.append(chunk)

    return chunks

def doc_file_to_chunks(doc: dict[str, Any], max_chars: int = 1200) -> list[dict[str, Any]]:
    """
    Transform an enriched "file" document (docs_files_v2) into a list of chunks ready for ingestion.
    """
    text = doc.get("clean_text") or ""
    parts = split_by_paragraphs(text, max_chars=max_chars)

    chunks: list[dict[str, Any]] = []

    if not parts:
        parts = [text]

    chunk_count = len(parts)
    base_id = doc.get("id") or "unknown-file"

    for idx, part in enumerate(parts):
        metadata = dict(doc)
        metadata.pop("clean_text", None)

        metadata["chunk_index"] = idx
        metadata["chunk_count"] = chunk_count

        chunk = {
            "id": f"{base_id}-{idx}",
            "text": part,
            "metadata": metadata,
        }
        chunks.append(chunk)

    return chunks



def clean_issue_to_chunk(issue: dict, ingest_version: str = "v1.0") -> dict:
    """
    Old version: enrichment + chunking in a single chunk.
    Do not use in the new pipeline (docs_issues -> chunks_issues),
    kept here only for temporary compatibility.
    """
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