import json
from typing import Any

from pipeline.ingestion.github_service import GitHubService
from shared.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def load_pull_requests(data_dir, repo: str) -> list[dict[str, Any]]:
    prs_path = data_dir / f"raw_prs_{repo.lower()}.json"
    if prs_path.exists():
        return json.loads(prs_path.read_text(encoding="utf-8"))
    return []


def select_pull_requests_for_commit_ingestion(
    pull_requests: list[dict[str, Any]],
    scope: str,
) -> list[dict[str, Any]]:
    if scope == "all":
        return pull_requests

    if scope == "linked_only":
        return [pr for pr in pull_requests if pr.get("linked_issue_numbers")]

    if scope == "merged_only":
        return [pr for pr in pull_requests if pr.get("merged")]

    # Default resolver-friendly mode: keep merged PRs + PRs explicitly linked to issues.
    return [
        pr for pr in pull_requests
        if pr.get("merged") or pr.get("linked_issue_numbers")
    ]


def main() -> None:
    cfg = load_config()
    owner = cfg["owner"]
    repos = cfg["repos"]
    data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    rate_limits = cfg.get("rate_limits", {})
    commit_pr_scope = cfg.get("commit_pr_scope", "linked_or_merged")
    gh = GitHubService(
        owner=owner,
        token_env=cfg.get("github_token_env", "GITHUB_TOKEN"),
        prs_sleep=rate_limits.get("prs_sleep", 0.2),
        pr_details_sleep=rate_limits.get("pr_details_sleep", 0.1),
        commits_sleep=rate_limits.get("commits_sleep", 0.1),
    )

    for repo in repos:
        print(f"Processing repo {repo}")
        pull_requests = load_pull_requests(data_dir, repo)
        if not pull_requests:
            print(f"[{repo}] raw PR file missing or empty, fetching pull requests first")
            pull_requests = gh.fetch_all_pull_requests(repo)
            prs_out_file = data_dir / f"raw_prs_{repo.lower()}.json"
            prs_out_file.write_text(
                json.dumps(pull_requests, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        selected_pull_requests = select_pull_requests_for_commit_ingestion(
            pull_requests,
            scope=commit_pr_scope,
        )
        commits = gh.fetch_commits_for_pull_requests(repo, selected_pull_requests)

        out_file = data_dir / f"raw_commits_{repo.lower()}.json"
        out_file.write_text(
            json.dumps(commits, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        linked_selected_count = len(
            [pr for pr in selected_pull_requests if pr.get("linked_issue_numbers")]
        )
        merged_selected_count = len([pr for pr in selected_pull_requests if pr.get("merged")])
        print(
            f"[{repo}] {len(commits)} commits fetched from {len(selected_pull_requests)} PRs "
            f"(scope={commit_pr_scope}, merged={merged_selected_count}, linked={linked_selected_count}) -> {out_file}"
        )


if __name__ == "__main__":
    main()