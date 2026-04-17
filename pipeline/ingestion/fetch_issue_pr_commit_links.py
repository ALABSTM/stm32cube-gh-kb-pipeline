import json
from datetime import datetime, timezone
from collections import defaultdict
from typing import Any

from shared.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def load_json_array(path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        return payload
    return []


def is_merge_like_commit(commit: dict[str, Any]) -> bool:
    message = (commit.get("message") or "").strip().lower()
    return message.startswith("merge branch") or message.startswith("merge pull request")


def score_and_confidence(
    explicit_pr_count: int,
    merged_pr_count: int,
    meaningful_commit_count: int,
) -> tuple[float, str]:
    score = 0.0
    if explicit_pr_count > 0:
        score += 0.5
    if merged_pr_count > 0:
        score += 0.3
    elif explicit_pr_count > 0:
        score += 0.1
    if meaningful_commit_count > 0:
        score += 0.2
    score = min(score, 1.0)

    if score >= 0.9:
        confidence = "high"
    elif score >= 0.5:
        confidence = "medium"
    elif score > 0.0:
        confidence = "low"
    else:
        confidence = "none"
    return score, confidence


def derive_resolution_status(
    explicit_pr_count: int,
    merged_pr_count: int,
    meaningful_commit_count: int,
) -> str:
    if merged_pr_count > 0 and meaningful_commit_count > 0:
        return "merged_fix"
    if explicit_pr_count > 0 and meaningful_commit_count > 0:
        return "candidate_fix"
    if explicit_pr_count > 0:
        return "reference_only"
    return "unlinked"


def build_links_for_repo(
    repo: str,
    issues: list[dict[str, Any]],
    pull_requests: list[dict[str, Any]],
    commits: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    pr_by_issue: dict[int, list[dict[str, Any]]] = defaultdict(list)
    pr_by_number: dict[int, dict[str, Any]] = {}

    for pull_request in pull_requests:
        pr_number = pull_request.get("pr_number")
        if not isinstance(pr_number, int):
            continue
        pr_by_number[pr_number] = pull_request
        for issue_number in pull_request.get("linked_issue_numbers") or []:
            if isinstance(issue_number, int):
                pr_by_issue[issue_number].append(pull_request)

    commit_by_issue: dict[int, list[dict[str, Any]]] = defaultdict(list)
    commits_by_pr: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for commit in commits:
        commit_issue_numbers = [num for num in (commit.get("linked_issue_numbers") or []) if isinstance(num, int)]
        for issue_number in commit_issue_numbers:
            commit_by_issue[issue_number].append(commit)

        for pr_number in commit.get("pr_numbers") or []:
            if isinstance(pr_number, int):
                commits_by_pr[pr_number].append(commit)

    links: list[dict[str, Any]] = []
    for issue in issues:
        issue_number = issue.get("issue_number")
        if not isinstance(issue_number, int):
            continue

        explicit_prs = pr_by_issue.get(issue_number, [])
        explicit_pr_numbers = sorted(
            [pr["pr_number"] for pr in explicit_prs if isinstance(pr.get("pr_number"), int)]
        )

        explicit_commits = commit_by_issue.get(issue_number, [])
        explicit_commit_shas = sorted(
            [c["sha"] for c in explicit_commits if isinstance(c.get("sha"), str)]
        )

        pr_linked_commit_shas: set[str] = set()
        for pr_number in explicit_pr_numbers:
            for commit in commits_by_pr.get(pr_number, []):
                sha = commit.get("sha")
                if isinstance(sha, str):
                    pr_linked_commit_shas.add(sha)

        all_commit_shas = sorted(set(explicit_commit_shas) | pr_linked_commit_shas)
        linked_prs = [pr_by_number[pn] for pn in explicit_pr_numbers if pn in pr_by_number]
        all_linked_commits: list[dict[str, Any]] = []
        commit_by_sha = {c.get("sha"): c for c in commits if isinstance(c.get("sha"), str)}
        for sha in all_commit_shas:
            commit_item = commit_by_sha.get(sha)
            if not commit_item:
                continue
            all_linked_commits.append(commit_item)

        merge_like_commits = [c for c in all_linked_commits if is_merge_like_commit(c)]
        linked_commits = [c for c in all_linked_commits if not is_merge_like_commit(c)]
        linked_commit_shas = sorted(
            [c["sha"] for c in linked_commits if isinstance(c.get("sha"), str)]
        )
        merge_like_commit_shas = sorted(
            [c["sha"] for c in merge_like_commits if isinstance(c.get("sha"), str)]
        )

        merged_pr_count = len([pr for pr in linked_prs if pr.get("merged")])

        score, confidence = score_and_confidence(
            explicit_pr_count=len(explicit_pr_numbers),
            merged_pr_count=merged_pr_count,
            meaningful_commit_count=len(linked_commit_shas),
        )
        resolution_status = derive_resolution_status(
            explicit_pr_count=len(explicit_pr_numbers),
            merged_pr_count=merged_pr_count,
            meaningful_commit_count=len(linked_commit_shas),
        )

        links.append(
            {
                "repo": repo,
                "issue_number": issue_number,
                "issue_title": issue.get("title") or "",
                "issue_labels": issue.get("labels") or [],
                "issue_state": issue.get("state"),
                "issue_url": issue.get("github_url"),
                "linked_pr_numbers": explicit_pr_numbers,
                "linked_commit_shas": linked_commit_shas,
                "linked_prs": [
                    {
                        "pr_number": pr.get("pr_number"),
                        "title": pr.get("title") or "",
                        "state": pr.get("state"),
                        "merged": bool(pr.get("merged")),
                        "github_url": pr.get("github_url"),
                        "changed_files_count": pr.get("changed_files_count", 0),
                        "merge_commit_sha": pr.get("merge_commit_sha"),
                    }
                    for pr in linked_prs
                ],
                "linked_commits": [
                    {
                        "sha": c.get("sha"),
                        "message": c.get("message") or "",
                        "committed_at": c.get("committed_at"),
                        "github_url": c.get("github_url"),
                        "pr_numbers": c.get("pr_numbers") or [],
                        "stats": c.get("stats") or {},
                    }
                    for c in linked_commits
                ],
                "evidence": {
                    "explicit_pr_numbers": explicit_pr_numbers,
                    "explicit_commit_shas": explicit_commit_shas,
                    "commits_via_linked_prs": sorted(pr_linked_commit_shas),
                    "merge_like_commit_shas": merge_like_commit_shas,
                    "merged_pr_count": merged_pr_count,
                },
                "link_score": round(score, 2),
                "link_confidence": confidence,
                "resolution_status": resolution_status,
            }
        )

    links.sort(key=lambda item: item.get("issue_number") or 0)
    return links


def main() -> None:
    cfg = load_config()
    repos = cfg.get("repos", [])
    data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    for repo in repos:
        repo_slug = repo.lower()
        issues_path = data_dir / f"raw_issues_{repo_slug}.json"
        prs_path = data_dir / f"raw_prs_{repo_slug}.json"
        commits_path = data_dir / f"raw_commits_{repo_slug}.json"

        issues = load_json_array(issues_path)
        pull_requests = load_json_array(prs_path)
        commits = load_json_array(commits_path)

        links = build_links_for_repo(repo, issues, pull_requests, commits)
        out_file = data_dir / f"issue_pr_commit_links_{repo_slug}.json"
        out_file.write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8")

        linked_only = [item for item in links if item.get("link_score", 0) > 0]
        linked_only_file = data_dir / f"issue_pr_commit_links_{repo_slug}_linked_only.json"
        linked_only_file.write_text(
            json.dumps(linked_only, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        summary = {
            "repo": repo,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "issues_total": len(links),
            "linked_issues": len(linked_only),
            "unlinked_issues": len(links) - len(linked_only),
            "link_rate": round((len(linked_only) / len(links)) if links else 0.0, 4),
            "resolution_status_counts": {
                "merged_fix": len([x for x in linked_only if x.get("resolution_status") == "merged_fix"]),
                "candidate_fix": len([x for x in linked_only if x.get("resolution_status") == "candidate_fix"]),
                "reference_only": len([x for x in linked_only if x.get("resolution_status") == "reference_only"]),
            },
            "top_linked_issue_numbers": [
                item.get("issue_number")
                for item in sorted(
                    linked_only,
                    key=lambda x: (
                        len(x.get("linked_pr_numbers") or []),
                        len(x.get("linked_commit_shas") or []),
                        x.get("link_score") or 0,
                    ),
                    reverse=True,
                )[:20]
            ],
        }
        summary_file = data_dir / f"issue_pr_commit_links_{repo_slug}_summary.json"
        summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

        linked_count = len(linked_only)
        print(
            f"[{repo}] {len(links)} issue link records generated ({linked_count} linked issues) -> {out_file}"
        )
        print(f"[{repo}] linked-only file -> {linked_only_file}")
        print(f"[{repo}] summary file -> {summary_file}")


if __name__ == "__main__":
    main()