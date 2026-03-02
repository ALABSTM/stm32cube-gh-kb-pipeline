from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = SRC_DIR / "config"


def get_config_path() -> Path:
    return CONFIG_DIR / "config.json"


def get_repos_root(repos_dir_name: str) -> Path:
    return PROJECT_ROOT / repos_dir_name