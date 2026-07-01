import json
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

from shared.utils.paths import DATA_DIR
from pipeline.ingestion.pdf_figure_service import extract_pdf_multimodal

try:
    from pypdf import PdfReader  # type: ignore[import-not-found]
except Exception:
    PdfReader = None


DOC_EXTENSIONS = {".md", ".txt", ".htm", ".html"}
TECHNICAL_TEXT_EXTENSIONS = {
    ".c",
    ".h",
    ".hpp",
    ".hh",
    ".s",
    ".asm",
    ".ld",
    ".mk",
    ".cmake",
    ".dox",
    ".rst",
    ".xml",
    ".json",
    ".yml",
    ".yaml",
    ".ini",
    ".cfg",
    ".conf",
    ".csv",
}
PDF_EXTENSION = ".pdf"

TOP_LEVEL_METADATA_FILES = {
    ".deliveryignore",
    ".gitmodules",
    "code_of_conduct.md",
    "contributing.md",
    "license.md",
    "security.md",
    "sw_security_level.md",
    "package.xml",
    "sbom_cdx.json",
}

TECHNICAL_SOURCE_ROOTS = {
    "drivers",
    "middlewares",
    "utilities",
    "components",
    "include",
    "source",
    "inc",
    "src",
}


def is_board_bsp_root(root: str) -> bool:
    if not root.startswith("stm32"):
        return False
    return any(tag in root for tag in ("-dk", "-eval", "-disco", "nucleo"))


def build_github_blob_url(owner: str, repo_name: str, rel_path: str, ref: str = "master") -> str:
    path_norm = (rel_path or "").replace("\\", "/").lstrip("/")
    path_escaped = quote(path_norm, safe="/")
    return f"https://github.com/{owner}/{repo_name}/blob/{ref}/{path_escaped}"


def is_projects_readme(rel_path: Path) -> bool:
    parts = rel_path.parts
    if len(parts) < 2:
        return False
    if parts[0] != "Projects":
        return False

    filename = parts[-1].lower()
    if not filename.startswith("readme"):
        return False

    return rel_path.suffix.lower() in DOC_EXTENSIONS


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
    return False


def is_documentation_pdf(rel_path: Path) -> bool:
    parts = rel_path.parts
    if not parts:
        return False
    if parts[0].lower() not in ("documentation", "documentations"):
        return False
    return rel_path.suffix.lower() == PDF_EXTENSION


def is_top_level_metadata_file(rel_path: Path) -> bool:
    if len(rel_path.parts) != 1:
        return False

    filename = rel_path.name.lower()
    if filename in TOP_LEVEL_METADATA_FILES:
        return True

    if filename.startswith("readme") and rel_path.suffix.lower() in DOC_EXTENSIONS:
        return True

    if filename.startswith("release_notes") and rel_path.suffix.lower() in DOC_EXTENSIONS:
        return True

    return False


def is_technical_source_file(rel_path: Path) -> bool:
    parts = rel_path.parts
    if not parts:
        return False

    filename = rel_path.name.lower()
    suffix = rel_path.suffix.lower()

    if filename.startswith("readme") or filename.startswith("release_notes"):
        return True

    if suffix not in DOC_EXTENSIONS and suffix not in TECHNICAL_TEXT_EXTENSIONS:
        return False

    if len(parts) == 1:
        return True

    root = parts[0].lower()
    if root in TECHNICAL_SOURCE_ROOTS:
        return True

    if is_board_bsp_root(root):
        return True

    return False


def should_include_file(repo_root: Path, path: Path) -> bool:
    if not path.is_file():
        return False

    rel_path = path.relative_to(repo_root)
    return (
        is_projects_readme(rel_path)
        or is_release_notes(rel_path)
        or is_top_level_readme(rel_path)
        or is_documentation_pdf(rel_path)
        or is_top_level_metadata_file(rel_path)
        or is_technical_source_file(rel_path)
    )


def iter_repo_files(repo_root: Path) -> Iterable[Path]:
    for p in repo_root.rglob("*"):
        if should_include_file(repo_root, p):
            yield p


def extract_pdf_text(path: Path) -> str:
    if PdfReader is None:
        print(f"[WARN] pypdf not installed; cannot read PDF {path}. Install with: pip install pypdf")
        return ""

    try:
        reader = PdfReader(str(path))
        pages_text: list[str] = []
        for page in reader.pages:
            pages_text.append(page.extract_text() or "")
        return "\n".join(t for t in pages_text if t).strip()
    except Exception as exc:
        print(f"[WARN] Cannot extract PDF text from {path}: {exc}")
        return ""


def read_text_file_content(path: Path) -> tuple[str, str]:
    try:
        return path.read_text(encoding="utf-8"), "text"
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1"), "text"
        except Exception as exc:
            print(f"[WARN] Cannot read {path}: {exc}")
            return "", "none"


def collect_repo_docs(repo_name: str, repo_root: Path, owner: str = "STMicroelectronics") -> list[dict]:
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
        rel_path_str = str(rel_path).replace("\\", "/")
        print(f"  [{count}] Reading file: {rel_path}")

        github_url = build_github_blob_url(
            owner=owner,
            repo_name=repo_name,
            rel_path=rel_path_str,
        )

        content = ""
        extractor = "none"
        figure_records = []
        media_urls = []
        images_count = 0
        pdf_task_file = None

        if file_path.suffix.lower() == PDF_EXTENSION:
            try:
                result = extract_pdf_multimodal(
                    pdf_path=file_path,
                    repo_name=repo_name,
                    rel_path=rel_path_str,
                    source_pdf_url=github_url,
                    data_dir=DATA_DIR,
                )
                content = result.get("content", "")
                figure_records = result.get("figure_records", [])
                images_count = result.get("figures_count", 0)
                extractor = result.get("content_extractor", "pypdf+render+opencv")
                pdf_task_file = result.get("task_file")
            except Exception as exc:
                print(f"[WARN] Multimodal PDF extraction failed for {file_path}: {exc}")
                content = extract_pdf_text(file_path)
                extractor = "pypdf_fallback"
                figure_records = []
                images_count = 0
        else:
            content, extractor = read_text_file_content(file_path)

        raw_files.append(
            {
                "repo": repo_name,
                "path": rel_path_str,
                "content": content,
                "encoding": "utf-8",
                "github_url": github_url,
                "media_urls": media_urls,
                "image_records": figure_records,
                "images_count": images_count,
                "content_extractor": extractor,
                "pdf_task_file": pdf_task_file,
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