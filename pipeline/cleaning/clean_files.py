import json

from shared.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def is_bsp_board_root(path: str) -> bool:
    root = path.split("/", 1)[0]
    if not root.startswith("stm32"):
        return False
    return any(tag in root for tag in ("-dk", "-eval", "-disco", "nucleo"))


def detect_file_type(path: str) -> str:
    p = path.replace("\\", "/").lower()

    if p.startswith(("documentation/", "documentations/")) and p.endswith(".pdf"):
        return "documentation_pdf"

    if "release_notes" in p or "releasenotes" in p:
        return "release_notes"

    if "projects/" in p:
        return "project_readme"

    if p.endswith("readme.md") or p.endswith("readme.txt"):
        if "/documentation/" in p:
            return "doc_readme"
        return "root_readme"

    if p in {
        "code_of_conduct.md",
        "contributing.md",
        "license.md",
        "security.md",
        "sw_security_level.md",
        "package.xml",
        "sbom_cdx.json",
        ".deliveryignore",
        ".gitmodules",
    }:
        return "repo_metadata"

    if p.startswith("drivers/"):
        return "driver_source"

    if p.startswith("src/") or p.startswith("inc/"):
        return "hal_driver_source"

    if p.startswith("middlewares/"):
        return "middleware_source"

    if p.startswith("utilities/"):
        return "utilities_content"

    if p.startswith("components/"):
        return "bsp_component_source"

    if p.startswith("include/") or p.startswith("source/"):
        return "cmsis_source"

    if is_bsp_board_root(p):
        return "bsp_board_source"

    if "/" not in p and p.startswith("stm32") and p.endswith((".c", ".h", ".hpp", ".s", ".asm")):
        return "bsp_board_source"

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
        github_url = f.get("github_url")
        media_urls = f.get("media_urls") or []
        image_records = f.get("image_records") or []
        images_count = f.get("images_count") or len(image_records)
        content_extractor = f.get("content_extractor") or "text"
        pdf_task_file = f.get("pdf_task_file")

        clean_text = clean_content(content)
        file_type = detect_file_type(path)

        clean_files.append(
            {
                "repo": repo,
                "path": path,
                "clean_text": clean_text,
                "file_type": file_type,
                "encoding": encoding,
                "github_url": github_url,
                "media_urls": media_urls,
                "image_records": image_records,
                "images_count": images_count,
                "content_extractor": content_extractor,
                "pdf_task_file": pdf_task_file,
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
