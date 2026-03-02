import json

from src.services.github_service import GitHubService
from src.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main():
    cfg = load_config()
    owner = cfg["owner"]
    repos = cfg["repos"]
    data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    gh = GitHubService(
        owner=owner,
        token_env=cfg.get("github_token_env", "GITHUB_TOKEN"),
        issues_sleep=cfg.get("rate_limits", {}).get("issues_sleep", 0.2),
        comments_sleep=cfg.get("rate_limits", {}).get("comments_sleep", 0.1),
    )

    for repo in repos:
        print(f"Traitement repo {repo}")
        issues = gh.fetch_all_issues(repo)

        out_file = data_dir / f"raw_issues_{repo.lower()}.json"
        out_file.write_text(
            json.dumps(issues, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[{repo}] {len(issues)} issues récupérées → {out_file}")


if __name__ == "__main__":
    main()