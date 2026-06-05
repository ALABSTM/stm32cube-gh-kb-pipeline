"""
Remove orphan sub-repo folders from by_series/ that should be under their parent series/drivers/.
Run after reexport_delivery to clean up old structure.
"""

import os
import shutil
import stat
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BY_SERIES = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "by_series"

# Valid top-level series folders
VALID_SERIES = {"stm32cubef4", "stm32cubeh5", "stm32cubeh7", "stm32cubeu5", "stm32cubewl"}


def force_remove_readonly(func, path, exc_info):
    """Handle read-only files on Windows (OneDrive / git)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def main():
    if not BY_SERIES.exists():
        print("by_series/ not found")
        return

    removed = []
    for entry in sorted(BY_SERIES.iterdir()):
        if entry.is_dir() and entry.name not in VALID_SERIES:
            print(f"  Removing: {entry.name}/")
            shutil.rmtree(entry, onexc=force_remove_readonly)
            removed.append(entry.name)

    if removed:
        print(f"\nRemoved {len(removed)} orphan folders.")
    else:
        print("No orphan folders found.")

    print("\nRemaining:")
    for entry in sorted(BY_SERIES.iterdir()):
        if entry.is_dir():
            print(f"  {entry.name}/")


if __name__ == "__main__":
    main()
