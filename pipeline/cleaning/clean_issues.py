import json

from pipeline.cleaning.cleaning_service import build_clean_issue
from shared.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_config()
    repos = cfg["repos"]

    for repo in repos:
        raw_file = DATA_DIR / f"raw_issues_{repo.lower()}.json"
        out_file = DATA_DIR / f"clean_issues_{repo.lower()}.json"

        print(f"Cleaning issues for {repo}")
        if not raw_file.exists():
            print(f"[WARN] raw_issues file not found: {raw_file}")
            continue

        raw_issues = json.loads(raw_file.read_text(encoding="utf-8"))
        clean_issues = [build_clean_issue(issue) for issue in raw_issues]

        out_file.write_text(
            json.dumps(clean_issues, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"{len(clean_issues)} cleaned issues -> {out_file}")


if __name__ == "__main__":
    main()
