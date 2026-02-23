import json
import sys
from pathlib import Path
from typing import Iterable, List, Dict


REPO_NAME = "STM32CubeH7"

REPO_ROOT = Path("repos") / REPO_NAME

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_OUTPUT_FILE = OUTPUT_DIR / f"raw_files_{REPO_NAME.lower()}.json"

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
    if len(parts) == 1:
       
        return True
    if parts[0].lower() == "documentation":
        return True

    return False


def should_include_file(path: Path) -> bool:

    if not path.is_file():
        return False

    rel_path = path.relative_to(REPO_ROOT)

    if is_projects_readme(rel_path):
        return True

    if is_release_notes(rel_path):
        return True

    if is_top_level_readme(rel_path):
        return True

    return False


def iter_repo_files(root: Path) -> Iterable[Path]:

    for p in root.rglob("*"):
        if should_include_file(p):
            yield p


def read_file_content(path: Path) -> str:

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception as e:
            print(f"[WARN] Impossible de lire {path} : {e}")
            return ""




def main() -> None:
    if not REPO_ROOT.exists():
        print(f"[ERREUR] Le dossier du repo n'existe pas : {REPO_ROOT}")
        print("        Vérifie que tu as bien cloné le repo STM32Cube dans ce chemin.")
        sys.exit(1)

    raw_files: List[Dict] = []

    print(f"=== Scan du repo {REPO_NAME} dans {REPO_ROOT} ===")

    count = 0
    for file_path in iter_repo_files(REPO_ROOT):
        count += 1
        rel_path = file_path.relative_to(REPO_ROOT)
        print(f"  [{count}] Lecture fichier : {rel_path}")

        content = read_file_content(file_path)

        raw_obj = {
            "repo": REPO_NAME,
            "path": str(rel_path).replace("\\", "/"),  
            "content": content,
            "encoding": "utf-8",  
        }
        raw_files.append(raw_obj)

    print(f"=== {len(raw_files)} fichiers collectés pour {REPO_NAME} (phase 1) ===")
    print(f"Écriture dans {RAW_OUTPUT_FILE}")

    RAW_OUTPUT_FILE.write_text(
        json.dumps(raw_files, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Terminé.")


if __name__ == "__main__":
    main()