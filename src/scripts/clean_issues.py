import json

from src.services.cleaning_service import build_clean_issue
from src.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))



def main():
    cfg = load_config()
    repos = cfg["repos"]
    data_dir = DATA_DIR

    for repo in repos:
        raw_file = data_dir / f"raw_issues_{repo.lower()}.json"
        out_file = data_dir / f"clean_issues_{repo.lower()}.json"

        print(f"Nettoyage des issues pour {repo}")
        raw_issues = json.loads(raw_file.read_text(encoding="utf-8"))
        clean_issues = [build_clean_issue(issue) for issue in raw_issues]

        out_file.write_text(
            json.dumps(clean_issues, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"{len(clean_issues)} issues nettoyées → {out_file}")


if __name__ == "__main__":
    main()