import json
from pathlib import Path

from jsonschema import validate

from shared.utils.paths import get_config_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

def get_default_repo() -> str:
    cfg = json.loads(get_config_path().read_text(encoding="utf-8-sig"))
    repos = cfg.get("repos", [])
    return next((repo for repo in repos if str(repo).lower().startswith("stm32cube")), repos[0])


def build_schema_data_pairs(repo: str) -> list[tuple[str, str]]:
    slug = repo.lower()
    docs_files_v3 = PROJECT_ROOT / "data" / f"docs_files_{slug}_v3.json"
    docs_files_suffix = "v3" if docs_files_v3.exists() else "v2"
    return [
        (
            "shared/schemas/docs_issues_v2.schema.json",
            f"data/docs_issues_{slug}_v2.json",
        ),
        (
            "shared/schemas/docs_files_v2.schema.json",
            f"data/docs_files_{slug}_{docs_files_suffix}.json",
        ),
        (
            "shared/schemas/chunks_issues_v2.schema.json",
            f"data/chunks_issues_{slug}_v2.json",
        ),
        (
            "shared/schemas/chunks_files_v2.schema.json",
            f"data/chunks_files_{slug}_v2.json",
        ),
    ]


def validate_file(schema_rel: str, data_rel: str) -> bool:
    schema_path = PROJECT_ROOT / schema_rel
    data_path = PROJECT_ROOT / data_rel

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    if not data_path.exists():
        print(f"[WARN] Schema validation skipped; data file not found: {data_path}")
        return False

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    data = json.loads(data_path.read_text(encoding="utf-8"))

    validate(instance=data, schema=schema)
    print(f"OK: {data_rel} matches {schema_rel}")
    return True


def main() -> None:
    repo = get_default_repo()
    print(f"Running schema validation for {repo}...")
    validated = 0
    for schema_rel, data_rel in build_schema_data_pairs(repo):
        if validate_file(schema_rel, data_rel):
            validated += 1
    print(f"Schema validation completed: {validated} file(s) validated.")


if __name__ == "__main__":
    main()
