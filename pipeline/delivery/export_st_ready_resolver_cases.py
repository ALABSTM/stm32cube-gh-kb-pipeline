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


def normalize_path(path: str | None) -> str:
    if not path:
        return ""
    return str(path).replace("\\", "/").strip().lstrip("/").lower()


def infer_module_from_path(path: str | None) -> str:
    norm = normalize_path(path)
    if not norm:
        return "unknown"
    if norm.startswith("drivers/"):
        if "hal_driver" in norm:
            return "HAL_Driver"
        if "cmsis" in norm:
            return "CMSIS"
        return "Drivers"
    if norm.startswith("middlewares/"):
        return "Middlewares"
    if norm.startswith("projects/"):
        return "Projects"
    if norm.startswith("utilities/"):
        return "Utilities"
    if norm.startswith("documentation/"):
        return "Documentation"
    return norm.split("/", 1)[0] or "unknown"


def load_raw_commits_index(repo: str) -> dict[str, dict[str, Any]]:
    path = DATA_DIR / f"raw_commits_{repo.lower()}.json"
    if not path.exists():
        return {}
    commits = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for c in commits:
        sha = str(c.get("sha") or "").strip().lower()
        if sha:
            out[sha] = c
    return out


def load_files_lookup(repo: str) -> dict[str, dict[str, Any]]:
    files_path = (
        PROJECT_ROOT
        / "datasets"
        / "07_delivery"
        / "st_ready"
        / "files_json"
        / f"st_ready_files_{repo.lower()}.json"
    )
    if not files_path.exists():
        return {}

    payload = json.loads(files_path.read_text(encoding="utf-8"))
    docs = payload.get("files") if isinstance(payload, dict) else []

    lookup: dict[str, dict[str, Any]] = {}
    for doc in docs:
        key = normalize_path(doc.get("path"))
        if not key:
            continue
        if key not in lookup:
            lookup[key] = doc
            continue
        # Prefer valid documents when duplicates exist.
        if doc.get("is_valid", True) and not lookup[key].get("is_valid", True):
            lookup[key] = doc
    return lookup


def aggregate_changed_files(
    case: dict[str, Any],
    raw_commits_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}

    for linked_commit in case.get("linked_commits") or []:
        sha = str(linked_commit.get("sha") or "").strip().lower()
        if not sha:
            continue
        raw_commit = raw_commits_index.get(sha)
        if not raw_commit:
            continue
        for f in raw_commit.get("files_changed") or []:
            filename = f.get("filename")
            key = normalize_path(filename)
            if not key:
                continue
            entry = merged.setdefault(
                key,
                {
                    "path": str(filename).replace("\\", "/").lstrip("/"),
                    "status": f.get("status"),
                    "additions": 0,
                    "deletions": 0,
                    "changes": 0,
                    "touched_by_commits": 0,
                    "commit_shas": set(),
                    "module": infer_module_from_path(filename),
                },
            )
            entry["status"] = f.get("status") or entry.get("status")
            entry["additions"] += int(f.get("additions") or 0)
            entry["deletions"] += int(f.get("deletions") or 0)
            entry["changes"] += int(f.get("changes") or 0)
            entry["touched_by_commits"] += 1
            entry["commit_shas"].add(sha)

    out: list[dict[str, Any]] = []
    for _, v in merged.items():
        v["commit_shas"] = sorted(v["commit_shas"])
        out.append(v)

    out.sort(key=lambda x: (x.get("changes", 0), x.get("touched_by_commits", 0)), reverse=True)
    return out


def build_github_file_url(repo: str, path: str | None) -> str | None:
    if not path:
        return None
    normalized = str(path).replace("\\", "/").lstrip("/")
    if not normalized:
        return None
    return f"https://github.com/STMicroelectronics/{repo}/blob/master/{normalized}"


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
        "commit_only_candidate": "Commit-level evidence exists, but PR linkage is incomplete.",
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
    if case.get("merged_pr_with_file_evidence"):
        lines.append("File evidence: merged PR modifies files even when commit log is merge-heavy")

    lines.append("Constraints: Validate against exact MCU series, board, firmware package version, and local project config before applying.")
    return "\n".join(lines).strip()


def to_st_ready_case(
    case: dict[str, Any],
    files_lookup: dict[str, dict[str, Any]],
    raw_commits_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    linked_prs = case.get("linked_prs") or []
    linked_commits = case.get("linked_commits") or []
    repo = case.get("repo")

    pr_urls = [pr.get("github_url") for pr in linked_prs if pr.get("github_url")]
    commit_urls = [c.get("github_url") for c in linked_commits if c.get("github_url")]
    primary_pr_number = (case.get("linked_pr_numbers") or [None])[0]
    primary_commit_sha = (case.get("linked_commit_shas") or [None])[0]

    changed_files = aggregate_changed_files(case, raw_commits_index=raw_commits_index)
    matched_docs_count = 0
    linked_file_ids: list[str] = []
    linked_file_paths: list[str] = []
    impacted_modules: set[str] = set()
    impacted_components: set[str] = set()
    impacted_boards: set[str] = set()
    impacted_file_types: set[str] = set()

    for f in changed_files:
        key = normalize_path(f.get("path"))
        doc = files_lookup.get(key)
        if doc:
            matched_docs_count += 1
            f["file_doc_id"] = doc.get("id")
            f["file_type"] = doc.get("file_type")
            f["component"] = doc.get("component")
            f["board"] = doc.get("board")
            f["example_name"] = doc.get("example_name")
            f["source_match"] = "docs_files_exact"
            f["github_url"] = doc.get("github_url") or build_github_file_url(repo=repo, path=f.get("path"))
            if doc.get("id"):
                linked_file_ids.append(doc.get("id"))
            if doc.get("path"):
                linked_file_paths.append(doc.get("path"))
            if doc.get("component"):
                impacted_components.add(doc.get("component"))
            if doc.get("board"):
                impacted_boards.add(doc.get("board"))
            if doc.get("file_type"):
                impacted_file_types.add(doc.get("file_type"))
        else:
            f["file_doc_id"] = None
            f["file_type"] = None
            f["component"] = None
            f["board"] = None
            f["example_name"] = None
            f["source_match"] = "commit_only"
            f["github_url"] = build_github_file_url(repo=repo, path=f.get("path"))

        impacted_modules.add(f.get("module") or "unknown")
        f["score"] = round(float(f.get("changes") or 0) + (20.0 if doc else 0.0), 2)

    changed_files_total = len(changed_files)
    unmatched_files_count = changed_files_total - matched_docs_count
    match_rate = (float(matched_docs_count) / float(changed_files_total)) if changed_files_total else 0.0
    primary_changed_file = changed_files[0] if changed_files else None

    return {
        "id": f"resolver::{case.get('repo')}::issue::{case.get('issue_number')}",
        "title": case.get("issue_title"),
        "label": case.get("issue_title"),
        "externalURL": case.get("issue_url"),
        "rootTagPath": "resolver_cases",
        "evidence_refs": [
            {
                "type": "issue",
                "id": case.get("issue_number"),
                "url": case.get("issue_url"),
            }
        ],
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
        "merged_pr_with_file_evidence": bool(
            case.get("merged_pr_with_file_evidence")
            or (case.get("evidence") or {}).get("merged_pr_with_file_evidence")
        ),
        "merged_pr_with_file_evidence_pr_numbers": (
            (case.get("evidence") or {}).get("merged_pr_with_file_evidence_pr_numbers") or []
        ),
        "merged_pr_changed_files_total": int((case.get("evidence") or {}).get("merged_pr_changed_files_total") or 0),
        "link_confidence": case.get("link_confidence"),
        "link_score": case.get("link_score"),
        "delivery_template": "st_v1_resolver_case",
        "resolver_card_text": build_resolver_card_text(case),
        "linked_file_ids": sorted(set([x for x in linked_file_ids if x])),
        "linked_file_paths": sorted(set([x for x in linked_file_paths if x])),
        "files_evidence": {
            "changed_files_total": changed_files_total,
            "matched_docs_files_count": matched_docs_count,
            "unmatched_files_count": unmatched_files_count,
            "match_rate": round(match_rate, 4),
            "files": changed_files,
        },
        "impacted_modules": sorted([x for x in impacted_modules if x and x != "unknown"]),
        "impacted_components": sorted(impacted_components),
        "impacted_boards": sorted(impacted_boards),
        "impacted_file_types": sorted(impacted_file_types),
        "primary_changed_file": primary_changed_file,
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
    files_lookup = load_files_lookup(repo)
    raw_commits_index = load_raw_commits_index(repo)
    total = len(cases)

    selected: list[dict[str, Any]] = []
    for case in cases:
        status = case.get("resolution_status") or "unlinked"
        if not include_reference_only and status == "reference_only":
            continue
        if status == "unlinked":
            continue
        selected.append(
            to_st_ready_case(
                case,
                files_lookup=files_lookup,
                raw_commits_index=raw_commits_index,
            )
        )

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
            "commit_only_candidate": len(
                [c for c in selected if c.get("resolution_status") == "commit_only_candidate"]
            ),
            "reference_only": len([c for c in selected if c.get("resolution_status") == "reference_only"]),
        },
        "merged_pr_with_file_evidence_cases": len(
            [c for c in selected if c.get("merged_pr_with_file_evidence")]
        ),
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