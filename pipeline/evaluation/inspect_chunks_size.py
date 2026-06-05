import json

from shared.utils.paths import DATA_DIR


def inspect(path_name: str) -> None:
    path = DATA_DIR / path_name
    chunks = json.loads(path.read_text(encoding="utf-8"))
    lengths = [len(c.get("text", "")) for c in chunks]
    print(path_name)
    print("  chunks:", len(lengths))
    print("  min len:", min(lengths))
    print("  max len:", max(lengths))
    print("  avg len:", sum(lengths) / len(lengths))
    print()


def main() -> None:
    inspect("chunks_issues_stm32cubeh7_v2.json")
    inspect("chunks_files_stm32cubeh7_v2.json")


if __name__ == "__main__":
    main()
