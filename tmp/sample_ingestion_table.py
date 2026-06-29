import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = root / "data"
repos = ["STM32CubeH7", "STM32CubeF4", "STM32CubeH5", "STM32CubeU5", "STM32CubeWL"]


def pct(n, d):
    return round((n / d) * 100, 1) if d else 0.0

print("repo,issues_total,body_pct,title_pct,labels_pct,files_total,files_content_pct")
for repo in repos:
    issues_path = data / f"raw_issues_{repo.lower()}.json"
    files_path = data / f"raw_files_{repo.lower()}.json"

    issues_total = body_pct = title_pct = labels_pct = 0
    files_total = files_content_pct = 0

    if issues_path.exists():
        issues = json.loads(issues_path.read_text(encoding="utf-8"))
        issues_total = len(issues)
        body_pct = pct(sum(1 for i in issues if (i.get("body") or "").strip()), issues_total)
        title_pct = pct(sum(1 for i in issues if (i.get("title") or "").strip()), issues_total)
        labels_pct = pct(sum(1 for i in issues if i.get("labels")), issues_total)

    if files_path.exists():
        files = json.loads(files_path.read_text(encoding="utf-8"))
        files_total = len(files)
        files_content_pct = pct(sum(1 for f in files if (f.get("content") or "").strip()), files_total)

    print(f"{repo},{issues_total},{body_pct},{title_pct},{labels_pct},{files_total},{files_content_pct}")
