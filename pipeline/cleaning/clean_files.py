import json

from shared.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def detect_file_type(path: str) -> str:
    p = path.replace("\\", "/").lower()

    if "release_notes" in p or "releasenotes" in p:
        return "release_notes"

    if "projects/" in p:
        return "project_readme"

    if p.endswith("readme.md") or p.endswith("readme.txt"):
        if "/documentation/" in p:
            return "doc_readme"
        return "root_readme"

    return "other"


def clean_content(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def clean_files_for_repo(repo: str) -> None:
    in_file = DATA_DIR / f"raw_files_{repo.lower()}.json"
    out_file = DATA_DIR / f"clean_files_{repo.lower()}.json"

    if not in_file.exists():
        print(f"[WARN] raw_files not found for {repo}: {in_file}")
        return

    raw_files = json.loads(in_file.read_text(encoding="utf-8"))
    clean_files: list[dict] = []

    for f in raw_files:
        path = f.get("path") or ""
        content = f.get("content") or ""
        encoding = f.get("encoding") or "utf-8"

        clean_text = clean_content(content)
        file_type = detect_file_type(path)

        clean_files.append(
            {
                "repo": repo,
                "path": path,
                "clean_text": clean_text,
                "file_type": file_type,
                "encoding": encoding,
            }
        )

    out_file.write_text(
        json.dumps(clean_files, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[CLEAN] {len(clean_files)} cleaned files -> {out_file}")


def main() -> None:
    cfg = load_config()
    repos = cfg["repos"]

    for repo in repos:
        clean_files_for_repo(repo)

    print("Done clean_files.")


if __name__ == "__main__":
    main()
