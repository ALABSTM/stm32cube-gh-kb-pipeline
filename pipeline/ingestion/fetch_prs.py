import json

from pipeline.ingestion.github_service import GitHubService
from shared.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_config()
    owner = cfg["owner"]
    repos = cfg["repos"]
    data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    rate_limits = cfg.get("rate_limits", {})
    gh = GitHubService(
        owner=owner,
        token_env=cfg.get("github_token_env", "GITHUB_TOKEN"),
        prs_sleep=rate_limits.get("prs_sleep", 0.2),
        pr_details_sleep=rate_limits.get("pr_details_sleep", 0.1),
        commits_sleep=rate_limits.get("commits_sleep", 0.1),
    )

    for repo in repos:
        print(f"Processing repo {repo}")
        pull_requests = gh.fetch_all_pull_requests(repo)

        out_file = data_dir / f"raw_prs_{repo.lower()}.json"
        out_file.write_text(
            json.dumps(pull_requests, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[{repo}] {len(pull_requests)} pull requests fetched -> {out_file}")


if __name__ == "__main__":
    main()