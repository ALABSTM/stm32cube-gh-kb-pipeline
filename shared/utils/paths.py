from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "shared" / "config"
LEGACY_CONFIG_DIR = SRC_DIR / "config"


def get_config_path() -> Path:
    """Return the active config path. Supports STM32CUBE_CONFIG env var override."""
    env_cfg = os.environ.get("STM32CUBE_CONFIG")
    if env_cfg:
        p = Path(env_cfg)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        if p.exists():
            return p
    cfg = CONFIG_DIR / "config.json"
    if cfg.exists():
        return cfg
    return LEGACY_CONFIG_DIR / "config.json"


def get_repos_root(repos_dir_name: str) -> Path:
    return PROJECT_ROOT / repos_dir_name
