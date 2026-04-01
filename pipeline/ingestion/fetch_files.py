import json

from pipeline.ingestion.file_collect_service import collect_repo_docs, write_raw_files_json
from shared.utils.paths import DATA_DIR, get_config_path, get_repos_root


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_config()
    repos = cfg["repos"]
    data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    repos_root = get_repos_root(cfg.get("repos_dir", "GitHub_repos"))

    for repo_name in repos:
        repo_root = repos_root / repo_name

        if not repo_root.exists():
            print(f"[ERROR] Repo folder does not exist: {repo_root}")
            print("        Make sure repository is cloned under GitHub_repos/")
            continue

        try:
            raw_files = collect_repo_docs(repo_name, repo_root)
        except Exception as exc:
            print(f"[ERROR] Scan failed for {repo_name}: {exc}")
            continue

        output_file = data_dir / f"raw_files_{repo_name.lower()}.json"
        write_raw_files_json(raw_files, output_file)

    print("Done.")


if __name__ == "__main__":
    main()
