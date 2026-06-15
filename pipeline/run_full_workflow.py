import argparse

from pipeline.chunking.docs_to_chunks_files_v2 import main as chunks_files_v2_main
from pipeline.chunking.docs_to_chunks_issues_v2 import main as chunks_issues_v2_main
from pipeline.cleaning.clean_files import main as clean_files_main
from pipeline.cleaning.clean_issues import main as clean_issues_main
from pipeline.delivery.export_st_ready_diagnostic_cards import export_repo_json as export_diagnostic_cards_repo_json
from pipeline.delivery.export_st_ready_files import export_repo_json as export_files_repo_json
from pipeline.delivery.export_st_ready_issues import export_repo_json as export_issues_repo_json
from pipeline.delivery.export_st_ready_resolver_cases import export_repo_json as export_resolver_cases_repo_json
from pipeline.enrichment.files_to_docs_v2 import main as files_to_docs_v2_main
from pipeline.enrichment.issues_to_docs_v2 import main as issues_to_docs_v2_main
from pipeline.evaluation.test_stats_files_v2 import main as stats_files_main
from pipeline.evaluation.test_stats_issues_v2 import main as stats_issues_main
from pipeline.evaluation.validate_schemas import main as validate_schemas_main
from pipeline.ingestion.fetch_issue_pr_commit_links import main as fetch_issue_pr_commit_links_main
from pipeline.ingestion.fetch_commits import main as fetch_commits_main
from pipeline.ingestion.fetch_files import main as fetch_files_main
from pipeline.ingestion.fetch_issues import main as fetch_issues_main
from pipeline.ingestion.fetch_prs import main as fetch_prs_main
from pipeline.ingestion.repo_sync_service import main as sync_local_repos_main
from pipeline.similarity.compute_issue_similarity_v2 import main as similarity_main
from shared.utils.paths import get_config_path


def _enrich_pdf_figures_main() -> None:
    """Run Alfred Vision on PDF figure crops (tasks generated during ingestion)."""
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "pipeline_Automation" / "alfred" / "enrich_pdf_figures_with_alfred.py"
    if not script.exists():
        print(f"[SKIP] Alfred PDF enrichment script not found: {script}")
        return

    # Import and call main directly
    sys.path.insert(0, str(script.parent))
    import importlib.util
    spec = importlib.util.spec_from_file_location("enrich_pdf_figures", str(script))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Isolate sys.argv so the sub-script argparse doesn't see workflow args
    original_argv = sys.argv
    sys.argv = [str(script)]
    try:
        mod.main()
    finally:
        sys.argv = original_argv


def load_config() -> dict:
    return __import__("json").loads(get_config_path().read_text(encoding="utf-8"))


def export_st_ready_issues_all() -> None:
    repos = load_config().get("repos", [])
    for repo in repos:
        total, exported, out_root = export_issues_repo_json(repo=repo, include_invalid=False, comments_chars=1200)
        print(f"[ST-READY:json:issues] {repo}: exported {exported}/{total} -> {out_root}")


def export_st_ready_files_all() -> None:
    repos = load_config().get("repos", [])
    for repo in repos:
        total, exported, out_root = export_files_repo_json(
            repo=repo,
            include_invalid=False,
            summary_max_chars=240,
            technical_max_chars=4000,
        )
        print(f"[ST-READY:json:files] {repo}: exported {exported}/{total} -> {out_root}")


def export_st_ready_resolver_cases_all() -> None:
    repos = load_config().get("repos", [])
    for repo in repos:
        total, exported, out_root = export_resolver_cases_repo_json(repo=repo, include_reference_only=False)
        print(f"[ST-READY:json:resolver_cases] {repo}: exported {exported}/{total} -> {out_root}")


def export_st_ready_diagnostic_cards_all() -> None:
    repos = load_config().get("repos", [])
    for repo in repos:
        try:
            total, exported, out_root = export_diagnostic_cards_repo_json(repo=repo, include_all_issues=False)
        except FileNotFoundError as exc:
            print(f"[ST-READY:json:diagnostic_cards] {repo}: skipped ({exc})")
            continue
        print(f"[ST-READY:json:diagnostic_cards] {repo}: exported {exported}/{total} -> {out_root}")


STEPS = [
    ("Ingestion issues", fetch_issues_main),
    ("Ingestion pull requests", fetch_prs_main),
    ("Ingestion commits", fetch_commits_main),
    ("Ingestion issue-pr-commit links", fetch_issue_pr_commit_links_main),
    ("Ingestion sync local repos", sync_local_repos_main),
    ("Ingestion files", fetch_files_main),
    ("Alfred PDF figure descriptions", _enrich_pdf_figures_main),
    ("Cleaning issues", clean_issues_main),
    ("Cleaning files", clean_files_main),
    ("Enrichment issues V2", issues_to_docs_v2_main),
    ("Enrichment files V2", files_to_docs_v2_main), 
    ("Similarity issues V2", similarity_main),
    ("Chunking issues V2", chunks_issues_v2_main),
    ("Chunking files V2", chunks_files_v2_main),
    ("Stats issues V2", stats_issues_main),
    ("Stats files V2", stats_files_main),
    ("Schema validation", validate_schemas_main),
]


def main(skip_ingestion: bool = False, skip_chunking: bool = False, continue_on_error: bool = False, export_st_ready: bool = False, enrich_pdf: bool = True) -> None:
    steps = STEPS
    if skip_ingestion:
        steps = [step for step in steps if not step[0].startswith("Ingestion")]
    if not enrich_pdf:
        steps = [step for step in steps if not step[0].startswith("Alfred")]
    if skip_chunking:
        steps = [step for step in steps if not step[0].startswith("Chunking")]
    if export_st_ready:
        steps = steps + [
            ("Delivery ST-ready issues", export_st_ready_issues_all),
            ("Delivery ST-ready files", export_st_ready_files_all),
            ("Delivery ST-ready resolver cases", export_st_ready_resolver_cases_all),
            ("Delivery ST-ready diagnostic cards", export_st_ready_diagnostic_cards_all),
        ]

    for idx, (label, fn) in enumerate(steps, start=1):
        print(f"\n[{idx}/{len(steps)}] {label}...")
        try:
            fn()
        except Exception as exc:
            print(f"[ERROR] Step '{label}' failed: {exc}")
            if not continue_on_error:
                raise
            print("[WARN] Continuing to next step because --continue-on-error is enabled.")
    print("\nWorkflow completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full STM32Cube preprocessing workflow.")
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip GitHub ingestion steps and use existing raw files.",
    )
    parser.add_argument(
        "--skip-chunking",
        action="store_true",
        help="Skip local chunking (ST platform handles chunking at upload).",
    )
    parser.add_argument(
        "--no-enrich-pdf",
        action="store_true",
        help="Skip Alfred Vision enrichment of PDF figures.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue running next steps when one step fails.",
    )
    parser.add_argument(
        "--export-st-ready",
        action="store_true",
        help="Run ST-ready delivery exports after preprocessing and validation.",
    )
    args = parser.parse_args()
    main(
        skip_ingestion=args.skip_ingestion,
        skip_chunking=args.skip_chunking,
        continue_on_error=args.continue_on_error,
        export_st_ready=args.export_st_ready,
        enrich_pdf=not args.no_enrich_pdf,
    )
