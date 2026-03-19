import json

from src.services.preprocessing_model import PreprocessingConfig, PreprocessingModelFilesV2
from src.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_config()
    repos = cfg["repos"]
    preprocess_version = cfg.get("preprocess_version", "v2.0")

    pp_config = PreprocessingConfig(version=preprocess_version)
    pp_model = PreprocessingModelFilesV2(pp_config)

    for repo in repos:
        in_file = DATA_DIR / f"clean_files_{repo.lower()}.json"
        out_file = DATA_DIR / f"docs_files_{repo.lower()}_v2.json"

        if not in_file.exists():
            print(f"[WARN] Fichier clean_files introuvable : {in_file}")
            continue

        print(f"[V2] Génération docs_files pour {repo}")
        clean_files = json.loads(in_file.read_text(encoding="utf-8"))

        docs: list[dict] = []
        for f in clean_files:
            doc = pp_model.process_clean_file(f)
            docs.append(doc)

        out_file.write_text(
            json.dumps(docs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[V2] {len(docs)} docs_files écrits → {out_file}")

    print("Terminé V2 docs_files.")


if __name__ == "__main__":
    main()