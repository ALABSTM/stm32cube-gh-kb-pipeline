import json

from pipeline.chunking.chunk_service import doc_issue_to_chunks
from shared.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_config()
    repos = cfg["repos"]
    max_chars = cfg.get("chunk_max_chars_issue", 1200)

    for repo in repos:
        in_file = DATA_DIR / f"docs_issues_{repo.lower()}_v2_sim.json"
        if not in_file.exists():
            in_file = DATA_DIR / f"docs_issues_{repo.lower()}_v2.json"

        out_file = DATA_DIR / f"chunks_issues_{repo.lower()}_v2.json"

        if not in_file.exists():
            print(f"[WARN] docs_issues_v2 file not found: {in_file}")
            continue

        print(f"[V2] Multi-chunk splitting for {repo} (max_chars={max_chars})")
        docs = json.loads(in_file.read_text(encoding="utf-8"))

        all_chunks: list[dict] = []
        for doc in docs:
            if not doc.get("is_valid", True):
                continue
            all_chunks.extend(doc_issue_to_chunks(doc, max_chars=max_chars))

        out_file.write_text(
            json.dumps(all_chunks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[V2] {len(all_chunks)} chunks written -> {out_file}")

    print("Done V2 chunks_issues.")


if __name__ == "__main__":
    main()
