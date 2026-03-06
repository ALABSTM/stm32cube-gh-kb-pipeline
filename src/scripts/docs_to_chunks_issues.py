
import json

from src.services.chunk_service import doc_issue_to_chunks
from src.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_config()
    repos = cfg["repos"]
    max_chars = cfg.get("chunk_max_chars_issue", 1200)

    data_dir = DATA_DIR

    for repo in repos:
        in_file = data_dir / f"docs_issues_{repo.lower()}.json"
        out_file = data_dir / f"chunks_issues_{repo.lower()}.json"

        if not in_file.exists():
            print(f"[WARN] Fichier docs introuvable : {in_file}")
            continue

        print(f"Chunking des documents issues pour {repo}")
        docs = json.loads(in_file.read_text(encoding="utf-8"))

        all_chunks: list[dict] = []
        for doc in docs:
            all_chunks.extend(doc_issue_to_chunks(doc, max_chars=max_chars))

        out_file.write_text(
            json.dumps(all_chunks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"{len(all_chunks)} chunks écrits → {out_file}")

    print("Terminé.")


if __name__ == "__main__":
    main()