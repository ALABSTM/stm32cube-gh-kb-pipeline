import json
from pathlib import Path

from jsonschema import validate


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_DATA_PAIRS = [
    (
        "shared/schemas/docs_issues_v2.schema.json",
        "data/docs_issues_stm32cubeh7_v2.json",
    ),
    (
        "shared/schemas/docs_files_v2.schema.json",
        "data/docs_files_stm32cubeh7_v2.json",
    ),
    (
        "shared/schemas/chunks_issues_v2.schema.json",
        "data/chunks_issues_stm32cubeh7_v2.json",
    ),
    (
        "shared/schemas/chunks_files_v2.schema.json",
        "data/chunks_files_stm32cubeh7_v2.json",
    ),
]


def validate_file(schema_rel: str, data_rel: str) -> None:
    schema_path = PROJECT_ROOT / schema_rel
    data_path = PROJECT_ROOT / data_rel

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    data = json.loads(data_path.read_text(encoding="utf-8"))

    validate(instance=data, schema=schema)
    print(f"OK: {data_rel} matches {schema_rel}")


def main() -> None:
    print("Running schema validation...")
    for schema_rel, data_rel in SCHEMA_DATA_PAIRS:
        validate_file(schema_rel, data_rel)
    print("All schema validations passed.")


if __name__ == "__main__":
    main()
