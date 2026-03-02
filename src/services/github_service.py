import os
import time
from typing import Any

import requests


class GitHubService:
    def __init__(
        self,
        owner: str,
        token_env: str | None = "GITHUB_TOKEN",
        issues_sleep: float = 0.2,
        comments_sleep: float = 0.1,
    ) -> None:
        self.owner = owner
        self.issues_sleep = issues_sleep
        self.comments_sleep = comments_sleep

        token = os.environ.get(token_env) if token_env else None

        self.session = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update(headers)

    def fetch_all_issues(self, repo: str) -> list[dict[str, Any]]:
        """Récupère toutes les issues (open + closed) d'un repo, avec commentaires."""
        issues: list[dict[str, Any]] = []
        page = 1

        while True:
            url = f"https://api.github.com/repos/{self.owner}/{repo}/issues"
            params = {
                "state": "all",
                "per_page": 100,
                "page": page,
            }
            print(f"[{repo}] Fetch issues page {page} ...")
            resp = self.session.get(url, params=params)
            if resp.status_code != 200:
                print(f"  Erreur HTTP {resp.status_code}: {resp.text}")
                break

            data = resp.json()
            if not data:
                break

            for item in data:
                # Ignore les pull requests
                if "pull_request" in item:
                    continue

                issue_number = item["number"]
                comments_url = item["comments_url"]
                comments = self.fetch_comments(repo, issue_number, comments_url)

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
            time.sleep(self.issues_sleep)

        return issues

    def fetch_comments(
        self,
        repo: str,
        issue_number: int,
        comments_url: str,
    ) -> list[dict[str, Any]]:
        """Récupère les commentaires d'une issue."""
        comments: list[dict[str, Any]] = []
        page = 1

        while True:
            params = {"per_page": 100, "page": page}
            print(f"    [{repo} #{issue_number}] Fetch comments page {page} ...")
            resp = self.session.get(comments_url, params=params)
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
            time.sleep(self.comments_sleep)

        return comments