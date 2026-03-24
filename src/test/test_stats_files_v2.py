import json
from collections import Counter

from src.utils.paths import DATA_DIR


def print_counter(title: str, counter: Counter, max_items: int | None = None) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    items = counter.most_common(max_items) if max_items else counter.items()
    for k, v in items:
        print(f"{k!r}: {v}")


def main(repo: str = "STM32CubeH7") -> None:
    path = DATA_DIR / f"docs_files_{repo.lower()}_v2.json"
    docs = json.loads(path.read_text(encoding="utf-8"))

    file_types = Counter(d.get("file_type") for d in docs)
    boards = Counter(d.get("board") for d in docs if d.get("board"))
    components = Counter(d.get("component") for d in docs if d.get("component"))
    valid = sum(1 for d in docs if d.get("is_valid", True))
    total = len(docs)

    print(f"Stats files V2 pour {repo} ")
    print(f"Total docs: {total}, valides: {valid}")

    print_counter("File types", file_types)
    print_counter("Top boards", boards, max_items=10)
    print_counter("Top components", components, max_items=10)


if __name__ == "__main__":
    main()