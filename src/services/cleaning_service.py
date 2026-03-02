import re

IMG_TAG_RE = re.compile(r"<img\b[^>]*src=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def clean_body_or_comment(text: str) -> tuple[str, list[str]]:
    """
    - Normalise les \n
    - Remplace chaque <img ...> par [IMAGE ATTACHED]
    - Récupère toutes les URLs d'images
    Retourne --> clean_text, image_urls
    """
    if not text:
        return "", []

    text = normalize_newlines(text)

    image_urls: list[str] = []

    def repl(match: re.Match) -> str:
        url = match.group(1)
        image_urls.append(url)
        return "[IMAGE ATTACHED]"

    text = IMG_TAG_RE.sub(repl, text)

    # Évite que les backticks perturbent les traitements suivants
    text = text.replace("`", "")

    text = text.strip()
    return text, image_urls


def build_clean_issue(issue: dict) -> dict:
    lines: list[str] = []

    title = issue.get("title") or ""
    lines.append(f"Title: {title}")
    lines.append("")

    body_raw = issue.get("body") or ""
    body_clean, body_images = clean_body_or_comment(body_raw)

    lines.append("Body:")
    if body_clean:
        lines.append(body_clean)
    else:
        lines.append("(no body)")
    lines.append("")

    all_image_urls: list[str] = []
    all_image_urls.extend(body_images)

    comments = issue.get("comments") or []
    if comments:
        lines.append("Comments:")
        for c in comments:
            author = (c.get("author") or "unknown").strip()
            created = c.get("created_at") or ""
            comment_raw = c.get("body") or ""
            comment_clean, comment_images = clean_body_or_comment(comment_raw)
            all_image_urls.extend(comment_images)

            lines.append(f"[{author} - {created}]")
            if comment_clean:
                lines.append(comment_clean)
            else:
                lines.append("(empty comment)")
            lines.append("")

    clean_text = "\n".join(lines).strip()

    clean_issue = {
        "repo": issue.get("repo"),
        "issue_number": issue.get("issue_number"),
        "title": issue.get("title") or "",
        "state": issue.get("state"),
        "labels": issue.get("labels") or [],
        "created_at": issue.get("created_at"),
        "closed_at": issue.get("closed_at"),
        "github_url": issue.get("github_url"),
        "clean_text": clean_text,
        "image_urls": all_image_urls,
        "images_count": len(all_image_urls),
    }
    return clean_issue