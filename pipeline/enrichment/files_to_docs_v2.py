import json

from pipeline.enrichment.preprocessing_model import PreprocessingConfig, PreprocessingModelFilesV2
from shared.utils.paths import DATA_DIR, get_config_path


def load_selected_repos() -> list[str]:
    """Load repos from the active config only (selected by workflow)."""
    cfg = json.loads(get_config_path().read_text(encoding="utf-8-sig"))
    return cfg.get("repos", [])


def main() -> None:
    cfg = json.loads(get_config_path().read_text(encoding="utf-8-sig"))
    repos = load_selected_repos()
    preprocess_version = cfg.get("preprocess_version", "v2.0")

    pp_config = PreprocessingConfig(version=preprocess_version)
    pp_model = PreprocessingModelFilesV2(pp_config)

    for repo in repos:
        # Prefer V3 (type-aware cleaned) if available, fallback to V1
        in_file_v3 = DATA_DIR / f"clean_files_{repo.lower()}_v3.json"
        in_file_v1 = DATA_DIR / f"clean_files_{repo.lower()}.json"
        in_file = in_file_v3 if in_file_v3.exists() else in_file_v1
        # Write to _v3 output if reading from v3 source, else _v2
        if in_file == in_file_v3:
            out_file = DATA_DIR / f"docs_files_{repo.lower()}_v3.json"
        else:
            out_file = DATA_DIR / f"docs_files_{repo.lower()}_v2.json"

        if not in_file.exists():
            print(f"[WARN] clean_files file not found: {in_file}")
            continue

        source_tag = "v3" if in_file == in_file_v3 else "v1"
        print(f"[V2] Generating docs_files for {repo} (source: clean_{source_tag})")
        raw = in_file.read_text(encoding="utf-8-sig")
        if not raw.strip():
            print(f"[WARN] Empty clean_files JSON, skipping: {in_file}")
            continue
        try:
            clean_files = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"[WARN] Invalid JSON in {in_file}: {exc}. Skipping.")
            continue

        docs: list[dict] = []
        for file_obj in clean_files:
            docs.append(pp_model.process_clean_file(file_obj))

        out_file.write_text(
            json.dumps(docs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[V2] {len(docs)} docs_files written -> {out_file}")

    print("Done V2 docs_files.")


if __name__ == "__main__":
    main()
