import json
from collections import Counter

from shared.utils.paths import DATA_DIR


def print_counter(title: str, counter: Counter, max_items: int | None = None) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    items = counter.most_common(max_items) if max_items else counter.items()
    for k, v in items:
        print(f"{k!r}: {v}")


def main(repo: str = "STM32CubeH7") -> None:
    path = DATA_DIR / f"docs_issues_{repo.lower()}_v2.json"
    docs = json.loads(path.read_text(encoding="utf-8"))

    layers = Counter(d.get("layer") for d in docs)
    severities = Counter(d.get("severity") for d in docs)
    kinds = Counter(d.get("issue_kind") for d in docs)
    boards = Counter(d.get("board") for d in docs if d.get("board"))
    components = Counter(d.get("component") for d in docs if d.get("component"))

    print(f"Stats issues V2 for {repo}")
    print_counter("Layers", layers)
    print_counter("Severities", severities)
    print_counter("Issue kinds", kinds)
    print_counter("Top boards", boards, max_items=10)
    print_counter("Top components", components, max_items=10)


if __name__ == "__main__":
    main()
