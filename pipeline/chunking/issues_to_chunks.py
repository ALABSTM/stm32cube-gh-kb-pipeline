import json

from pipeline.chunking.chunk_service import clean_issue_to_chunk
from shared.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main() -> None:
    cfg = load_config()
    repos = cfg["repos"]
    ingest_version = cfg.get("ingest_version", "v1.0")

    for repo in repos:
        in_file = DATA_DIR / f"clean_issues_{repo.lower()}.json"
        out_file = DATA_DIR / f"chunks_issues_{repo.lower()}.json"

        print(f"Converting issues into chunks for {repo}")
        clean_issues = json.loads(in_file.read_text(encoding="utf-8"))
        chunks = [clean_issue_to_chunk(issue, ingest_version=ingest_version) for issue in clean_issues]

        out_file.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"{len(chunks)} chunks written -> {out_file}")


if __name__ == "__main__":
    main()
