import os
import re
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
        prs_sleep: float = 0.2,
        pr_details_sleep: float = 0.1,
        commits_sleep: float = 0.1,
        request_timeout: float = 30.0,
        max_request_attempts: int = 3,
    ) -> None:
        self.owner = owner
        self.issues_sleep = issues_sleep
        self.comments_sleep = comments_sleep
        self.prs_sleep = prs_sleep
        self.pr_details_sleep = pr_details_sleep
        self.commits_sleep = commits_sleep
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

    def _extract_issue_numbers(self, *texts: str | None) -> list[int]:
        issue_numbers: list[int] = []
        seen: set[int] = set()

        patterns = [
            r"#(\d+)",
            r"(?:issues|issue)/(\d+)",
            r"\bissue\s*#?\s*(\d+)\b",
            r"\b(?:fixe[sd]?|close[sd]?|resolve[sd]?)\s*:?\s*#?(\d+)\b",
        ]

        for text in texts:
            if not text:
                continue
            for pattern in patterns:
                for match in re.findall(pattern, text, flags=re.IGNORECASE):
                    issue_number = int(match)
                    if issue_number in seen:
                        continue
                    seen.add(issue_number)
                    issue_numbers.append(issue_number)

        return issue_numbers

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

    def fetch_all_pull_requests(self, repo: str) -> list[dict[str, Any]]:
        pull_requests: list[dict[str, Any]] = []
        page = 1

        while True:
            url = f"https://api.github.com/repos/{self.owner}/{repo}/pulls"
            params = {
                "state": "all",
                "per_page": 100,
                "page": page,
            }
            print(f"[{repo}] Fetch pull requests page {page} ...")
            resp = self._safe_get(url, params, context=f"fetch pull requests page {page} for {repo}")
            if resp is None:
                break
            if resp.status_code != 200:
                print(f"  HTTP error {resp.status_code} on pull requests: {resp.text}")
                break

            data = resp.json()
            if not data:
                break

            for item in data:
                pr_number = item["number"]
                detail = self.fetch_pull_request_detail(repo, pr_number)
                if detail is None:
                    continue
                pull_requests.append(detail)

            page += 1
            time.sleep(self.prs_sleep)

        return pull_requests

    def fetch_pull_request_detail(self, repo: str, pr_number: int) -> dict[str, Any] | None:
        url = f"https://api.github.com/repos/{self.owner}/{repo}/pulls/{pr_number}"
        resp = self._safe_get(url, {}, context=f"fetch pull request #{pr_number} for {repo}")
        if resp is None:
            return None
        if resp.status_code != 200:
            print(f"  HTTP error {resp.status_code} on pull request #{pr_number}: {resp.text}")
            return None

        item = resp.json()
        files_changed = self.fetch_pull_request_files(repo, pr_number)
        linked_issue_numbers = self._extract_issue_numbers(item.get("title"), item.get("body"))

        time.sleep(self.pr_details_sleep)

        return {
            "repo": repo,
            "pr_number": pr_number,
            "title": item.get("title") or "",
            "state": item.get("state"),
            "merged": bool(item.get("merged")),
            "draft": bool(item.get("draft")),
            "author": (item.get("user") or {}).get("login"),
            "labels": [lbl["name"] for lbl in item.get("labels", [])],
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "closed_at": item.get("closed_at"),
            "merged_at": item.get("merged_at"),
            "body": item.get("body") or "",
            "github_url": item.get("html_url"),
            "head_ref": ((item.get("head") or {}).get("ref")),
            "base_ref": ((item.get("base") or {}).get("ref")),
            "merge_commit_sha": item.get("merge_commit_sha"),
            "commits_count": item.get("commits", 0),
            "review_comments_count": item.get("review_comments", 0),
            "comments_count": item.get("comments", 0),
            "changed_files_count": item.get("changed_files", 0),
            "additions": item.get("additions", 0),
            "deletions": item.get("deletions", 0),
            "linked_issue_numbers": linked_issue_numbers,
            "files_changed": files_changed,
        }

    def fetch_pull_request_files(self, repo: str, pr_number: int) -> list[dict[str, Any]]:
        files_changed: list[dict[str, Any]] = []
        page = 1

        while True:
            url = f"https://api.github.com/repos/{self.owner}/{repo}/pulls/{pr_number}/files"
            params = {"per_page": 100, "page": page}
            print(f"    [{repo} PR #{pr_number}] Fetch files page {page} ...")
            resp = self._safe_get(
                url,
                params,
                context=f"fetch pull request files page {page} for {repo} #{pr_number}",
            )
            if resp is None:
                break
            if resp.status_code != 200:
                print(f"      HTTP error {resp.status_code} on pull request files: {resp.text}")
                break

            data = resp.json()
            if not data:
                break

            for item in data:
                files_changed.append(
                    {
                        "filename": item.get("filename"),
                        "status": item.get("status"),
                        "additions": item.get("additions", 0),
                        "deletions": item.get("deletions", 0),
                        "changes": item.get("changes", 0),
                        "previous_filename": item.get("previous_filename"),
                        "blob_url": item.get("blob_url"),
                        "raw_url": item.get("raw_url"),
                    }
                )

            page += 1
            time.sleep(self.pr_details_sleep)

        return files_changed

    def fetch_pull_request_commits(self, repo: str, pr_number: int) -> list[dict[str, Any]]:
        commits: list[dict[str, Any]] = []
        page = 1

        while True:
            url = f"https://api.github.com/repos/{self.owner}/{repo}/pulls/{pr_number}/commits"
            params = {"per_page": 100, "page": page}
            print(f"    [{repo} PR #{pr_number}] Fetch commits page {page} ...")
            resp = self._safe_get(
                url,
                params,
                context=f"fetch pull request commits page {page} for {repo} #{pr_number}",
            )
            if resp is None:
                break
            if resp.status_code != 200:
                print(f"      HTTP error {resp.status_code} on pull request commits: {resp.text}")
                break

            data = resp.json()
            if not data:
                break

            commits.extend(data)
            page += 1
            time.sleep(self.commits_sleep)

        return commits

    def fetch_commit_detail(self, repo: str, sha: str) -> dict[str, Any] | None:
        url = f"https://api.github.com/repos/{self.owner}/{repo}/commits/{sha}"
        resp = self._safe_get(url, {}, context=f"fetch commit {sha} for {repo}")
        if resp is None:
            return None
        if resp.status_code != 200:
            print(f"  HTTP error {resp.status_code} on commit {sha}: {resp.text}")
            return None

        item = resp.json()
        commit_info = item.get("commit") or {}
        files = item.get("files") or []

        return {
            "repo": repo,
            "sha": item.get("sha"),
            "author": ((item.get("author") or {}).get("login")) or ((commit_info.get("author") or {}).get("name")),
            "committer": ((item.get("committer") or {}).get("login")) or ((commit_info.get("committer") or {}).get("name")),
            "message": commit_info.get("message") or "",
            "authored_at": (commit_info.get("author") or {}).get("date"),
            "committed_at": (commit_info.get("committer") or {}).get("date"),
            "github_url": item.get("html_url"),
            "parents": [parent.get("sha") for parent in item.get("parents", []) if parent.get("sha")],
            "stats": {
                "additions": (item.get("stats") or {}).get("additions", 0),
                "deletions": (item.get("stats") or {}).get("deletions", 0),
                "total": (item.get("stats") or {}).get("total", 0),
            },
            "files_changed": [
                {
                    "filename": file_item.get("filename"),
                    "status": file_item.get("status"),
                    "additions": file_item.get("additions", 0),
                    "deletions": file_item.get("deletions", 0),
                    "changes": file_item.get("changes", 0),
                    "previous_filename": file_item.get("previous_filename"),
                    "patch": file_item.get("patch"),
                }
                for file_item in files
            ],
            "linked_issue_numbers": self._extract_issue_numbers(commit_info.get("message")),
        }

    def fetch_commits_for_pull_requests(
        self,
        repo: str,
        pull_requests: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        commits_by_sha: dict[str, dict[str, Any]] = {}

        for pull_request in pull_requests:
            pr_number = pull_request.get("pr_number")
            if pr_number is None:
                continue

            linked_issue_numbers = [int(num) for num in pull_request.get("linked_issue_numbers") or []]
            commit_summaries = self.fetch_pull_request_commits(repo, pr_number)

            for summary in commit_summaries:
                sha = summary.get("sha")
                if not sha:
                    continue

                if sha not in commits_by_sha:
                    detail = self.fetch_commit_detail(repo, sha)
                    if detail is None:
                        continue
                    detail["pr_numbers"] = []
                    commits_by_sha[sha] = detail

                record = commits_by_sha[sha]
                pr_numbers = set(record.get("pr_numbers") or [])
                pr_numbers.add(pr_number)
                record["pr_numbers"] = sorted(pr_numbers)

                issue_numbers = set(record.get("linked_issue_numbers") or [])
                issue_numbers.update(linked_issue_numbers)
                record["linked_issue_numbers"] = sorted(issue_numbers)

                time.sleep(self.commits_sleep)

        commits = list(commits_by_sha.values())
        commits.sort(key=lambda item: ((item.get("committed_at") or ""), item.get("sha") or ""))
        return commits
