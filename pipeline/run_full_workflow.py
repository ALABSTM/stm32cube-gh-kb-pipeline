import argparse

from pipeline.chunking.docs_to_chunks_files_v2 import main as chunks_files_v2_main
from pipeline.chunking.docs_to_chunks_issues_v2 import main as chunks_issues_v2_main
from pipeline.cleaning.clean_files import main as clean_files_main
from pipeline.cleaning.clean_issues import main as clean_issues_main
from pipeline.enrichment.files_to_docs_v2 import main as files_to_docs_v2_main
from pipeline.enrichment.issues_to_docs_v2 import main as issues_to_docs_v2_main
from pipeline.evaluation.test_stats_files_v2 import main as stats_files_main
from pipeline.evaluation.test_stats_issues_v2 import main as stats_issues_main
from pipeline.evaluation.validate_schemas import main as validate_schemas_main
from pipeline.ingestion.fetch_files import main as fetch_files_main
from pipeline.ingestion.fetch_issues import main as fetch_issues_main
from pipeline.similarity.compute_issue_similarity_v2 import main as similarity_main


STEPS = [
    ("Ingestion issues", fetch_issues_main),
    ("Ingestion files", fetch_files_main),
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


def main(skip_ingestion: bool = False, continue_on_error: bool = False) -> None:
    steps = STEPS
    if skip_ingestion:
        steps = [step for step in STEPS if not step[0].startswith("Ingestion")]

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
        "--continue-on-error",
        action="store_true",
        help="Continue running next steps when one step fails.",
    )
    args = parser.parse_args()
    main(skip_ingestion=args.skip_ingestion, continue_on_error=args.continue_on_error)
