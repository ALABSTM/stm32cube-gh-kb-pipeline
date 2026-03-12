import json

from src.services.preprocessing_model import PreprocessingConfig, PreprocessingModelIssuesV2
from src.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_config()
    repos = cfg["repos"]
    preprocess_version = cfg.get("preprocess_version", "v2.0")

    pp_config = PreprocessingConfig(version=preprocess_version)
    pp_model = PreprocessingModelIssuesV2(pp_config)

    for repo in repos:
        in_file = DATA_DIR / f"clean_issues_{repo.lower()}.json"
        out_file = DATA_DIR / f"docs_issues_{repo.lower()}_v2.json"

        if not in_file.exists():
            print(f"[WARN] Fichier clean_issues introuvable : {in_file}")
            continue

        print(f"[V2] Génération docs_issues pour {repo}")
        clean_issues = json.loads(in_file.read_text(encoding="utf-8"))

        docs: list[dict] = []
        for issue in clean_issues:
            doc = pp_model.process_clean_issue(issue)
            docs.append(doc)

        out_file.write_text(
            json.dumps(docs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[V2] {len(docs)} docs écrits → {out_file}")

    print("Terminé V2 docs_issues.")


if __name__ == "__main__":
    main()