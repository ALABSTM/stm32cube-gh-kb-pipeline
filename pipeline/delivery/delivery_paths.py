from pathlib import Path

from shared.utils.paths import PROJECT_ROOT


ST_READY_ROOT = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready"
ST_READY_BY_SERIES_ROOT = ST_READY_ROOT / "by_series"

# Map sub-repos (drivers/BSP) to their parent series folder
_REPO_TO_SERIES: dict[str, str] = {}

# H7 sub-repos
for _r in [
    "stm32h7xx-hal-driver", "cmsis_device_h7",
    "stm32h735g-dk-bsp", "stm32h743i-eval-bsp", "stm32h745i-disco-bsp",
    "stm32h747i-disco-bsp", "stm32h747i-eval-bsp", "stm32h750b-dk-bsp",
    "stm32h7b3i-dk-bsp", "stm32h7b3i-eval-bsp", "stm32h7xx-nucleo-bsp",
]:
    _REPO_TO_SERIES[_r] = "stm32cubeh7"

# F4 sub-repos
for _r in [
    "stm32f4xx-hal-driver", "cmsis_device_f4",
    "stm32f4xx-nucleo-bsp", "stm32f4xx-nucleo-144-bsp", "stm32f4discovery-bsp",
    "32f401cdiscovery-bsp", "32f411ediscovery-bsp", "32f412gdiscovery-bsp",
    "32f413hdiscovery-bsp", "32f429idiscovery-bsp", "32f469idiscovery-bsp",
    "stm324x9i-eval-bsp", "stm324xg-eval-bsp", "stm32446e-eval-bsp",
    "stm32469i-eval-bsp",
]:
    _REPO_TO_SERIES[_r] = "stm32cubef4"

# H5 sub-repos
for _r in [
    "stm32h5xx-hal-driver", "cmsis_device_h5",
    "stm32h5xx-nucleo-bsp", "stm32h573i-discovery-bsp", "stm32h5f5j-discovery-bsp",
]:
    _REPO_TO_SERIES[_r] = "stm32cubeh5"

# U5 sub-repos
for _r in [
    "stm32u5xx-hal-driver", "cmsis_device_u5",
    "b-u585i-iot02a-bsp", "stm32u575i-ev-bsp", "stm32u5x9j-dk-bsp",
    "stm32u5g9j-dk2-bsp", "stm32u5xx-nucleo-bsp",
]:
    _REPO_TO_SERIES[_r] = "stm32cubeu5"

# WL sub-repos
for _r in [
    "stm32wlxx-hal-driver", "cmsis_device_wl",
    "stm32wlxx-nucleo-bsp", "b-wl5m-subg1-bsp",
]:
    _REPO_TO_SERIES[_r] = "stm32cubewl"

# C0 sub-repos
for _r in [
    "stm32c0xx-hal-driver", "cmsis_device_c0",
    "stm32c0xx-nucleo-bsp",
]:
    _REPO_TO_SERIES[_r] = "stm32cubec0"


def repo_slug(repo: str) -> str:
    return str(repo).strip().lower()


def get_repo_series_root(repo: str) -> Path:
    slug = repo_slug(repo)
    parent_series = _REPO_TO_SERIES.get(slug)
    if parent_series:
        # Sub-repo goes under parent_series/drivers/<sub-repo>/
        return ST_READY_BY_SERIES_ROOT / parent_series / "drivers" / slug
    return ST_READY_BY_SERIES_ROOT / slug


def get_repo_artifact_dir(repo: str, artifact_dir: str) -> Path:
    return get_repo_series_root(repo) / artifact_dir


def get_repo_artifact_file(repo: str, artifact_dir: str, file_name: str) -> Path:
    return get_repo_artifact_dir(repo, artifact_dir) / file_name


def get_legacy_artifact_dir(artifact_dir: str) -> Path:
    return ST_READY_ROOT / artifact_dir


def get_legacy_artifact_file(artifact_dir: str, file_name: str) -> Path:
    return get_legacy_artifact_dir(artifact_dir) / file_name


def get_existing_repo_artifact_file(repo: str, artifact_dir: str, file_name: str) -> Path:
    repo_file = get_repo_artifact_file(repo, artifact_dir, file_name)
    if repo_file.exists():
        return repo_file

    legacy_file = get_legacy_artifact_file(artifact_dir, file_name)
    if legacy_file.exists():
        return legacy_file

    return repo_file
