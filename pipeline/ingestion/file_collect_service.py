import json
from pathlib import Path
from typing import Dict, Iterable, List


DOC_EXTENSIONS = {".md", ".txt", ".htm", ".html"}


def is_projects_readme(rel_path: Path) -> bool:
    parts = rel_path.parts
    if len(parts) < 2:
        return False
    if parts[0] != "Projects":
        return False

    filename = parts[-1].lower()
    if not filename.startswith("readme"):
        return False

    ext = rel_path.suffix.lower()
    return ext in DOC_EXTENSIONS


def is_release_notes(rel_path: Path) -> bool:
    filename = rel_path.parts[-1]
    if not filename.lower().startswith("release_notes"):
        return False
    return rel_path.suffix.lower() in DOC_EXTENSIONS


def is_top_level_readme(rel_path: Path) -> bool:
    filename = rel_path.name.lower()
    if not filename.startswith("readme"):
        return False
    if rel_path.suffix.lower() not in DOC_EXTENSIONS:
        return False

    parts = rel_path.parts
    if len(parts) == 1:
        return True
    if parts[0].lower() == "documentation":
        return True
    return False


def should_include_file(repo_root: Path, path: Path) -> bool:
    if not path.is_file():
        return False

    rel_path = path.relative_to(repo_root)
    return is_projects_readme(rel_path) or is_release_notes(rel_path) or is_top_level_readme(rel_path)


def iter_repo_files(repo_root: Path) -> Iterable[Path]:
    for p in repo_root.rglob("*"):
        if should_include_file(repo_root, p):
            yield p


def read_file_content(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception as exc:
            print(f"[WARN] Cannot read {path}: {exc}")
            return ""


def collect_repo_docs(repo_name: str, repo_root: Path) -> list[dict]:
    if not repo_root.exists():
        raise FileNotFoundError(
            f"Repository folder does not exist: {repo_root}. "
            "Check that you cloned the repository."
        )

    raw_files: list[dict] = []
    print(f"=== Scanning {repo_name} in {repo_root} ===")

    count = 0
    for file_path in iter_repo_files(repo_root):
        count += 1
        rel_path = file_path.relative_to(repo_root)
        print(f"  [{count}] Reading file: {rel_path}")

        content = read_file_content(file_path)
        raw_files.append(
            {
                "repo": repo_name,
                "path": str(rel_path).replace("\\", "/"),
                "content": content,
                "encoding": "utf-8",
            }
        )

    print(f"=== {len(raw_files)} files collected for {repo_name} ===")
    return raw_files


def write_raw_files_json(raw_files: list[dict], output_file: Path) -> None:
    output_file.write_text(
        json.dumps(raw_files, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Written to {output_file}")
