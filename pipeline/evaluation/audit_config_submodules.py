import argparse
import configparser
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from shared.utils.paths import PROJECT_ROOT, get_repos_root

CONFIG_DIR = PROJECT_ROOT / "shared" / "config"


def repo_slug(value: str) -> str:
    return value.strip().removesuffix(".git").split("/")[-1].lower()


def canonical_repo_slug(value: str) -> str:
    return repo_slug(value).replace("_", "-")


def normalize_clone_url(url: str) -> str:
    value = url.strip()
    if value and not value.endswith(".git"):
        value = f"{value}.git"
    return value


def load_config_files() -> list[Path]:
    return sorted(
        path for path in CONFIG_DIR.glob("config*.json")
        if path.name != "config_all_series.json"
    )


def extract_submodules(gitmodules_path: Path) -> dict[str, dict[str, str]]:
    parser = configparser.ConfigParser()
    parser.read(gitmodules_path, encoding="utf-8")

    submodules: dict[str, dict[str, str]] = {}
    for section in parser.sections():
        if not section.startswith("submodule "):
            continue
        url = parser.get(section, "url", fallback="").strip()
        path = parser.get(section, "path", fallback="").strip()
        if not url or not path:
            continue
        parsed = urlparse(url)
        if "github.com" not in parsed.netloc.lower():
            continue
        slug = repo_slug(parsed.path)
        if slug:
            submodules[canonical_repo_slug(slug)] = {
                "repo": slug.replace("_", "-"),
                "path": path,
                "url": normalize_clone_url(url),
            }
    return submodules


def configured_repo_keys(cfg: dict) -> set[str]:
    repos = [str(repo).strip() for repo in cfg.get("repos", []) if str(repo).strip()]
    configured = {canonical_repo_slug(repo) for repo in repos}

    clone_urls = cfg.get("repo_clone_urls", {})
    if isinstance(clone_urls, dict):
        for alias, url in clone_urls.items():
            if isinstance(alias, str) and alias.strip():
                configured.add(canonical_repo_slug(alias))
            if isinstance(url, str) and url.strip():
                configured.add(canonical_repo_slug(urlparse(url).path))

    return configured


def get_submodule_ref(series_root: Path, submodule_path: str) -> str | None:
    proc = subprocess.run(
        ["git", "ls-tree", "HEAD", submodule_path],
        cwd=str(series_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    parts = (proc.stdout or "").strip().split()
    if len(parts) >= 3 and parts[1] == "commit":
        return parts[2]
    return None


def audit_config(cfg_file: Path) -> tuple[str, Path | None, list[dict[str, str]]]:
    cfg = json.loads(cfg_file.read_text(encoding="utf-8-sig"))
    repos = [str(repo).strip() for repo in cfg.get("repos", []) if str(repo).strip()]
    configured = configured_repo_keys(cfg)
    series_repo = next((repo for repo in repos if repo.lower().startswith("stm32cube")), cfg_file.stem)

    repos_root = get_repos_root(cfg.get("repos_dir", "GitHub_repos"))
    series_root = repos_root / series_repo
    gitmodules_path = series_root / ".gitmodules"
    if not gitmodules_path.exists():
        return series_repo, None, []

    missing: list[dict[str, str]] = []
    for submodule_repo, submodule in sorted(extract_submodules(gitmodules_path).items()):
        if submodule_repo not in configured:
            missing.append(submodule)
    return series_repo, series_root, missing


def update_config(cfg_file: Path, series_root: Path, missing: list[dict[str, str]]) -> None:
    cfg = json.loads(cfg_file.read_text(encoding="utf-8-sig"))
    repos = cfg.setdefault("repos", [])
    clone_urls = cfg.setdefault("repo_clone_urls", {})
    linked_refs = cfg.setdefault("linked_repo_refs", {})

    existing = configured_repo_keys(cfg)
    for submodule in missing:
        repo = submodule["repo"]
        key = canonical_repo_slug(repo)
        if key in existing:
            continue
        repos.append(repo)
        clone_urls[repo] = submodule["url"]
        ref = get_submodule_ref(series_root, submodule["path"])
        if ref:
            linked_refs[repo] = ref
        existing.add(key)

    cfg_file.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit config repos against GitHub submodules declared by STM32Cube series."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Append missing submodule repos, clone URLs, and local gitlink refs to config files.",
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Report missing repos without returning a non-zero exit code.",
    )
    args = parser.parse_args()

    total_missing = 0
    for cfg_file in load_config_files():
        series_repo, series_root, missing = audit_config(cfg_file)
        if not missing:
            continue
        total_missing += len(missing)
        print(f"\n[{series_repo}] missing submodule repos in {cfg_file.name}:")
        for submodule in missing:
            print(f"  - {submodule['repo']} ({submodule['path']})")

        if args.fix and series_root is not None:
            update_config(cfg_file, series_root, missing)
            print(f"  -> updated {cfg_file.name}")

    if total_missing == 0:
        print("OK: no missing GitHub submodule repos detected in configs.")
    elif args.fix:
        print(f"\nUpdated configs with {total_missing} missing repos. Run the audit again to verify.")
    else:
        print(f"\nTOTAL missing repos: {total_missing}")
        print("Run with --fix to append missing repos to the matching config files.")
        if not args.no_fail:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
