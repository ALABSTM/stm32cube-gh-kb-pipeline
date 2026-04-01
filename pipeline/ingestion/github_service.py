import os
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class GitHubService:
    def __init__(
        self,
        owner: str,
        token_env: str | None = "GITHUB_TOKEN",
        issues_sleep: float = 0.2,
        comments_sleep: float = 0.1,
        request_timeout: float = 30.0,
        max_request_attempts: int = 3,
    ) -> None:
        self.owner = owner
        self.issues_sleep = issues_sleep
        self.comments_sleep = comments_sleep
        self.request_timeout = request_timeout
        self.max_request_attempts = max_request_attempts

        token = os.environ.get(token_env) if token_env else None

        self.session = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update(headers)

        retry_cfg = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry_cfg)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _safe_get(self, url: str, params: dict[str, Any], context: str) -> requests.Response | None:
        for attempt in range(1, self.max_request_attempts + 1):
            try:
                return self.session.get(url, params=params, timeout=self.request_timeout)
            except requests.exceptions.RequestException as exc:
                print(f"  [WARN] {context} failed (attempt {attempt}/{self.max_request_attempts}): {exc}")
                if attempt == self.max_request_attempts:
                    print(f"  [ERROR] {context} failed after retries.")
                    return None
                time.sleep(1.5 * attempt)

    def fetch_all_issues(self, repo: str) -> list[dict[str, Any]]:
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
            resp = self._safe_get(url, params, context=f"fetch issues page {page} for {repo}")
            if resp is None:
                break
            if resp.status_code != 200:
                print(f"  HTTP error {resp.status_code}: {resp.text}")
                break

            data = resp.json()
            if not data:
                break

            for item in data:
                if "pull_request" in item:
                    continue

                issue_number = item["number"]
                comments_url = item["comments_url"]
                comments = self.fetch_comments(repo, issue_number, comments_url)

                issues.append(
                    {
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
                )

            page += 1
            time.sleep(self.issues_sleep)

        return issues

    def fetch_comments(
        self,
        repo: str,
        issue_number: int,
        comments_url: str,
    ) -> list[dict[str, Any]]:
        comments: list[dict[str, Any]] = []
        page = 1

        while True:
            params = {"per_page": 100, "page": page}
            print(f"    [{repo} #{issue_number}] Fetch comments page {page} ...")
            resp = self._safe_get(
                comments_url,
                params,
                context=f"fetch comments page {page} for {repo} #{issue_number}",
            )
            if resp is None:
                break
            if resp.status_code != 200:
                print(f"      HTTP error {resp.status_code} on comments: {resp.text}")
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
