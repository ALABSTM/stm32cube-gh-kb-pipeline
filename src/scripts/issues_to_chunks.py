import json

from src.services.chunk_service import clean_issue_to_chunk
from src.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def main():
    cfg = load_config()
    repos = cfg["repos"]
    ingest_version = cfg.get("ingest_version", "v1.0")
    data_dir = DATA_DIR

    for repo in repos:
        in_file = data_dir / f"clean_issues_{repo.lower()}.json"
        out_file = data_dir / f"chunks_issues_{repo.lower()}.json"

        print(f"Conversion en chunks pour {repo}")
        clean_issues = json.loads(in_file.read_text(encoding="utf-8"))
        chunks = [
            clean_issue_to_chunk(issue, ingest_version=ingest_version)
            for issue in clean_issues
        ]

        out_file.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"{len(chunks)} chunks écrits → {out_file}")


if __name__ == "__main__":
    main()