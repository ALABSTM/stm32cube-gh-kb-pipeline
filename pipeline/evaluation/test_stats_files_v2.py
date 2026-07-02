import json
from collections import Counter

from shared.utils.paths import DATA_DIR, get_config_path


def get_default_repo() -> str:
    cfg = json.loads(get_config_path().read_text(encoding="utf-8-sig"))
    repos = cfg.get("repos", [])
    return next((repo for repo in repos if str(repo).lower().startswith("stm32cube")), repos[0])


def print_counter(title: str, counter: Counter, max_items: int | None = None) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    items = counter.most_common(max_items) if max_items else counter.items()
    for k, v in items:
        print(f"{k!r}: {v}")


def main(repo: str | None = None) -> None:
    if repo is None:
        repo = get_default_repo()
    path = DATA_DIR / f"docs_files_{repo.lower()}_v3.json"
    if not path.exists():
        path = DATA_DIR / f"docs_files_{repo.lower()}_v2.json"
    if not path.exists():
        print(f"[WARN] Stats files skipped; input not found: {path}")
        return
    docs = json.loads(path.read_text(encoding="utf-8"))

    file_types = Counter(d.get("file_type") for d in docs)
    boards = Counter(d.get("board") for d in docs if d.get("board"))
    components = Counter(d.get("component") for d in docs if d.get("component"))
    valid = sum(1 for d in docs if d.get("is_valid", True))
    total = len(docs)

    print(f"Stats files V2 for {repo}")
    print(f"Total docs: {total}, valid: {valid}")
    print_counter("File types", file_types)
    print_counter("Top boards", boards, max_items=10)
    print_counter("Top components", components, max_items=10)


if __name__ == "__main__":
    main()
