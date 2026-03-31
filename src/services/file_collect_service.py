from pathlib import Path
from typing import Iterable, List, Dict
import json


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
    if ext not in DOC_EXTENSIONS:
        return False

    return True


def is_release_notes(rel_path: Path) -> bool:
    parts = rel_path.parts
    filename = parts[-1]

    if not filename.lower().startswith("release_notes"):
        return False

    ext = rel_path.suffix.lower()
    if ext not in DOC_EXTENSIONS:
        return False

    return True


def is_top_level_readme(rel_path: Path) -> bool:
    filename = rel_path.name.lower()
    if not filename.startswith("readme"):
        return False

    ext = rel_path.suffix.lower()
    if ext not in DOC_EXTENSIONS:
        return False

    parts = rel_path.parts
    # Readme root level (ex: README.md)
    if len(parts) == 1:
        return True
    # or under 'Documentation/'
    if parts[0].lower() == "documentation":
        return True

    return False


def should_include_file(repo_root: Path, path: Path) -> bool:
    if not path.is_file():
        return False

    rel_path = path.relative_to(repo_root)

    if is_projects_readme(rel_path):
        return True

    if is_release_notes(rel_path):
        return True

    if is_top_level_readme(rel_path):
        return True

    return False


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
        except Exception as e:
            print(f"[WARN] Unable to read {path} : {e}")
            return ""


def collect_repo_docs(repo_name: str, repo_root: Path) -> list[dict]:
    """
    Scan a local (cloned) repo and return a list of objects:
    {
      "repo": <repo_name>,
      "path": "relative/path",
      "content": "...",
      "encoding": "utf-8"
    }
    """
    if not repo_root.exists():
        raise FileNotFoundError(
            f"The repo folder does not exist: {repo_root}. "
            "Make sure you have cloned the repo."
        )

    raw_files: list[dict] = []

    print(f"=== Scanning repo {repo_name} in {repo_root} ===")

    count = 0
    for file_path in iter_repo_files(repo_root):
        count += 1
        rel_path = file_path.relative_to(repo_root)
        print(f"  [{count}] Reading file: {rel_path}")

        content = read_file_content(file_path)

        raw_obj = {
            "repo": repo_name,
            "path": str(rel_path).replace("\\", "/"),
            "content": content,
            "encoding": "utf-8",
        }
        raw_files.append(raw_obj)

    print(f"=== {len(raw_files)} files collected for {repo_name} ===")
    return raw_files


def write_raw_files_json(raw_files: list[dict], output_file: Path) -> None:
    output_file.write_text(
        json.dumps(raw_files, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Writing to {output_file}")