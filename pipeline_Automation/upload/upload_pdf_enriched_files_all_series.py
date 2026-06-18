"""
Upload PDF-enriched files to KB #793 for all 13 series.

Usage:
    python pipeline_Automation/upload/upload_pdf_enriched_files_all_series.py --dry-run
    python pipeline_Automation/upload/upload_pdf_enriched_files_all_series.py
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BY_SERIES = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "by_series"
ADD_SCRIPT = PROJECT_ROOT / "pipeline_Automation" / "upload" / "Add_Data_Source_Files.py"

KB_ID = 793

# Files datasource IDs for all 13 series
SERIES_FILES_DATASOURCES = {
    "stm32cubec0": 29192,
    "stm32cubef0": 29196,
    "stm32cubef1": 29198,
    "stm32cubef2": 29200,
    "stm32cubef3": 29283,
    "stm32cubef4": 29042,   # V3
    "stm32cubef7": 29277,
    "stm32cubeg0": 29274,
    "stm32cubeh5": 29043,   # V3
    "stm32cubeh7": 29041,   # V3
    "stm32cubeh7rs": 29271,
    "stm32cubeu5": 29044,   # V3
    "stm32cubewl": 29045,   # V3
}

# Processor params for files
PROCESSOR_PARAMS = 'eyJsYWJlbCI6ICJ7e3JlcG99fSB7e2ZpbGVfdHlwZX19IC0ge3twYXRofX0iLCAiZXh0ZXJuYWxVUkwiOiAiaHR0cHM6Ly9naXRodWIuY29tL1NUTWljcm9lbGVjdHJvbmljcy97e3JlcG99fS97e3Jvb3RfZGlyfX0ve3tyb290X3JlZn19L3t7cGF0aF91cmx9fSIsICJyb290VGFnUGF0aCI6ICJmaWxlcyJ9'

UPLOAD_DELAY_SEC = 5


def find_files_json(series: str) -> Path | None:
    """Find the best files JSON to upload for a series."""
    files_dir = BY_SERIES / series / "files_json"
    if not files_dir.exists():
        return None

    # Priority: _v3 > _pdf_enriched > base
    candidates = [
        files_dir / f"st_ready_files_{series}_v3.json",
        files_dir / f"st_ready_files_{series}_pdf_enriched.json",
        files_dir / f"st_ready_files_{series}.json",
    ]

    for c in candidates:
        if c.exists():
            return c
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Upload PDF-enriched files to KB")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print(f"Uploading PDF-enriched files to KB #{KB_ID}")
    print()

    uploaded = 0
    skipped = 0

    for series, ds_id in SERIES_FILES_DATASOURCES.items():
        files_json = find_files_json(series)

        if not files_json:
            print(f"[SKIP] {series}: No files JSON found")
            skipped += 1
            continue

        size_mb = files_json.stat().st_size / (1024 * 1024)
        print(f"[{series}] {files_json.name} ({size_mb:.1f} MB) -> datasource #{ds_id}")

        if args.dry_run:
            uploaded += 1
            continue

        cmd = [
            sys.executable, str(ADD_SCRIPT),
            "--kb", str(KB_ID),
            "--operation", "add",
            "--datasource-id", str(ds_id),
            "--remote-user", "abir.gharbi@st.com",
            "--processor", "JSON",
            "--processor-params", f"base64:{PROCESSOR_PARAMS}",
            "--json-split-size", "1000",
            "--files", str(files_json),
        ]
        if args.verbose:
            cmd.append("--verbose")

        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            print(f"  [WARN] Upload failed (exit code {result.returncode})")
        else:
            print(f"  [OK] Uploaded")
            uploaded += 1

        # Throttle to avoid rate limiting
        time.sleep(UPLOAD_DELAY_SEC)

    print(f"\nDone. {uploaded} uploaded, {skipped} skipped.")


if __name__ == "__main__":
    main()
