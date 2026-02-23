import os
import json
import time
from pathlib import Path

import requests


OWNER = "STMicroelectronics"

REPOS = ["STM32CubeH7"] 

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def make_session() -> requests.Session:
    session = requests.Session()
    headers = {
        "Accept": "application/vnd.github+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    session.headers.update(headers)
    return session


def fetch_all_issues_for_repo(session: requests.Session, repo: str):
    """Récupère toutes les issues (open + closed) d'un repo, avec commentaires."""
    issues = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{OWNER}/{repo}/issues"
        params = {
            "state": "all",      # open + closed
            "per_page": 100,   
            "page": page
        }
        print(f"[{repo}] Fetch issues page {page} ...")
        resp = session.get(url, params=params)
        if resp.status_code != 200:
            print(f"  Erreur HTTP {resp.status_code}: {resp.text}")
            break

        data = resp.json()
        if not data:
            break

        for item in data:
         
            if "pull_request" in item:
                continue  

            issue_number = item["number"]
            comments_url = item["comments_url"]

            # Récupérer les commentaires
            comments = fetch_comments_for_issue(session, comments_url, repo, issue_number)

            issue_obj = {
                "repo": repo,
                "issue_number": issue_number,
                "title": item.get("title") or "",
                "state": item.get("state"),
                "labels": [lbl["name"] for lbl in item.get("labels", [])],
                "created_at": item.get("created_at"),
                "closed_at": item.get("closed_at"),
                "body": item.get("body") or "",
                "comments": comments,
                "github_url": item.get("html_url"),
            }
            issues.append(issue_obj)

        page += 1
     
        time.sleep(0.2)

    return issues


def fetch_comments_for_issue(session: requests.Session, comments_url: str, repo: str, issue_number: int):
    """Récupère les commentaires d'une issue."""
    comments = []
    page = 1
    while True:
        params = {"per_page": 100, "page": page}
        print(f"    [{repo} #{issue_number}] Fetch comments page {page} ...")
        resp = session.get(comments_url, params=params)
        if resp.status_code != 200:
            print(f"      Erreur HTTP {resp.status_code} sur comments: {resp.text}")
            break

        data = resp.json()
        if not data:
            break

        for c in data:
            comments.append(
                {
                    "author": (c.get("user") or {}).get("login"),
                    "created_at": c.get("created_at"),
                    "body": c.get("body") or "",
                }
            )

        page += 1
        time.sleep(0.1)

    return comments


def main():
    session = make_session()

    for repo in REPOS:
        print(f"=== Traitement repo {repo} ===")
        issues = fetch_all_issues_for_repo(session, repo)

        output_file = OUTPUT_DIR / f"raw_issues_{repo.lower()}.json"
        print(f"[{repo}] {len(issues)} issues récupérées, écriture dans {output_file}")
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(issues, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()