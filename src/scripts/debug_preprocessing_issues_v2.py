import json
from pathlib import Path

from src.services.preprocessing_model import PreprocessingModelIssuesV2
from src.utils.paths import DATA_DIR 


def main(repo: str = "STM32CubeH7", max_issues: int = 20) -> None:
    in_path = DATA_DIR / f"clean_issues_{repo}.json"
    if not in_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {in_path}")

    with open(in_path, "r", encoding="utf-8") as f:
        issues = json.load(f)

    model = PreprocessingModelIssuesV2()

    for issue in issues[:max_issues]:
        doc = model.process_clean_issue(issue)
        print(f"Issue #{doc['issue_number']} - {doc.get('issue_title')[:60]}")
        print(f"  issue_kind : {doc.get('issue_kind')}")
        print(f"  layer      : {doc.get('layer')}")
        print(f"  severity   : {doc.get('severity')}")
        print(f"  board      : {doc.get('board')}")
        print(f"  component  : {doc.get('component')}")
        print(f"  is_valid   : {doc.get('is_valid')}")
        print("-" * 80)


if __name__ == "__main__":
    main()