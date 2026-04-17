import argparse
import json
import re
from pathlib import Path
from typing import Any

from shared.utils.paths import DATA_DIR, PROJECT_ROOT, get_config_path


def load_config() -> dict[str, Any]:
    return json.loads(get_config_path().read_text(encoding="utf-8"))


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def first_sentence(text: str, max_chars: int = 260) -> str:
    s = normalize_whitespace(text)
    if not s:
        return ""
    match = re.search(r"[.!?]", s)
    if match and match.end() <= max_chars:
        return s[: match.end()].strip()
    return s[:max_chars].strip()


def compact_list(items: list[str], max_items: int = 6) -> list[str]:
    cleaned = [normalize_whitespace(x) for x in items if normalize_whitespace(x)]
    return cleaned[:max_items]


def build_resolver_card_text(case: dict[str, Any]) -> str:
    issue_title = normalize_whitespace(case.get("issue_title") or "")
    issue_number = case.get("issue_number")
    labels = ", ".join(case.get("issue_labels") or [])
    status = case.get("resolution_status") or "unlinked"
    confidence = case.get("link_confidence") or "none"
    score = case.get("link_score") or 0

    linked_prs = case.get("linked_prs") or []
    linked_commits = case.get("linked_commits") or []

    pr_titles = compact_list([pr.get("title") or "" for pr in linked_prs], max_items=3)
    commit_hints = compact_list([
        first_sentence(c.get("message") or "", max_chars=180)
        for c in linked_commits
    ], max_items=4)

    resolution_hint = {
        "merged_fix": "Fix likely integrated in mainline; prefer this as primary recommendation.",
        "candidate_fix": "Potential fix identified, but integration status is uncertain.",
        "reference_only": "Reference link exists without enough technical fix evidence.",
        "unlinked": "No actionable fix linkage detected.",
    }.get(status, "Potential fix linkage requires validation.")

    lines = [
        f"Problem: Issue #{issue_number} - {issue_title}",
        f"Context: repo={case.get('repo')}, labels={labels or 'none'}, issue_state={case.get('issue_state')}",
        f"Resolver signal: resolution_status={status}, confidence={confidence}, score={score}",
        f"Assessment: {resolution_hint}",
    ]

    if pr_titles:
        lines.append(f"Candidate PRs: {' | '.join(pr_titles)}")
    if commit_hints:
        lines.append(f"Commit evidence: {' | '.join(commit_hints)}")

    lines.append("Constraints: Validate against exact MCU series, board, firmware package version, and local project config before applying.")
    return "\n".join(lines).strip()


def to_st_ready_case(case: dict[str, Any]) -> dict[str, Any]:
    linked_prs = case.get("linked_prs") or []
    linked_commits = case.get("linked_commits") or []
    repo = case.get("repo")

    pr_urls = [pr.get("github_url") for pr in linked_prs if pr.get("github_url")]
    commit_urls = [c.get("github_url") for c in linked_commits if c.get("github_url")]
    primary_pr_number = (case.get("linked_pr_numbers") or [None])[0]
    primary_commit_sha = (case.get("linked_commit_shas") or [None])[0]

    return {
        "id": f"resolver::{case.get('repo')}::issue::{case.get('issue_number')}",
        "url_base": "https://github.com/STMicroelectronics/",
        "repo": repo,
        "issue_root_path": "issues",
        "pr_root_path": "pull",
        "commit_root_path": "commit",
        "issue_number": case.get("issue_number"),
        "issue_title": case.get("issue_title"),
        "issue_labels": case.get("issue_labels") or [],
        "issue_state": case.get("issue_state"),
        "issue_url": case.get("issue_url"),
        "linked_pr_numbers": case.get("linked_pr_numbers") or [],
        "linked_commit_shas": case.get("linked_commit_shas") or [],
        "primary_pr_number": primary_pr_number,
        "primary_commit_sha": primary_commit_sha,
        "linked_pr_urls": pr_urls,
        "linked_commit_urls": commit_urls,
        "resolution_status": case.get("resolution_status"),
        "link_confidence": case.get("link_confidence"),
        "link_score": case.get("link_score"),
        "delivery_template": "st_v1_resolver_case",
        "resolver_card_text": build_resolver_card_text(case),
    }


def export_repo_json(repo: str, include_reference_only: bool) -> tuple[int, int, Path]:
    linked_only_path = DATA_DIR / f"issue_pr_commit_links_{repo.lower()}_linked_only.json"
    full_links_path = DATA_DIR / f"issue_pr_commit_links_{repo.lower()}.json"

    in_path = linked_only_path if linked_only_path.exists() else full_links_path
    if not in_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {linked_only_path} (or fallback {full_links_path})"
        )

    out_root = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "resolver_cases_json"
    out_root.mkdir(parents=True, exist_ok=True)

    cases = json.loads(in_path.read_text(encoding="utf-8"))
    total = len(cases)

    selected: list[dict[str, Any]] = []
    for case in cases:
        status = case.get("resolution_status") or "unlinked"
        if not include_reference_only and status == "reference_only":
            continue
        if status == "unlinked":
            continue
        selected.append(to_st_ready_case(case))

    payload = {
        "resolver_cases": selected,
    }

    out_file = out_root / f"st_ready_resolver_cases_{repo.lower()}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "repo": repo,
        "input_file": str(in_path),
        "output_file": str(out_file),
        "total_cases_in_input": total,
        "exported_cases": len(selected),
        "include_reference_only": include_reference_only,
        "format": "json",
        "root_tag_path": "resolver_cases",
        "status_breakdown": {
            "merged_fix": len([c for c in selected if c.get("resolution_status") == "merged_fix"]),
            "candidate_fix": len([c for c in selected if c.get("resolution_status") == "candidate_fix"]),
            "reference_only": len([c for c in selected if c.get("resolution_status") == "reference_only"]),
        },
    }
    (out_root / f"summary_resolver_cases_{repo.lower()}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return total, len(selected), out_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Export issue-pr-commit links into ST-ready resolver cases JSON.")
    parser.add_argument("--repo", action="append", help="Repo name, e.g., STM32CubeH7. Can be repeated.")
    parser.add_argument(
        "--include-reference-only",
        action="store_true",
        help="Include low-value reference_only cases in output.",
    )
    args = parser.parse_args()

    cfg = load_config()
    repos = args.repo or cfg.get("repos", [])

    if not repos:
        raise ValueError("No repos provided and no repos found in config.")

    for repo in repos:
        total, exported, out_root = export_repo_json(
            repo=repo,
            include_reference_only=args.include_reference_only,
        )
        print(f"[ST-READY:json:resolver_cases] {repo}: exported {exported}/{total} -> {out_root}")


if __name__ == "__main__":
    main()