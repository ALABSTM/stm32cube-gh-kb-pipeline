"""Create the missing U5 and WL resolver_cases datasources with all driver files."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BY_SERIES = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready" / "by_series"
ADD_SCRIPT = PROJECT_ROOT / "pipeline_Automation" / "Add_Data_Source_Files.py"

KB_ID = 793
PROCESSOR_PARAMS = '{"label": "{{label}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/issues/{{issue_number}}", "rootTagPath": "resolver_cases"}'


def find_resolver_files(series: str) -> list[Path]:
    files: list[Path] = []
    series_dir = BY_SERIES / series
    main_dir = series_dir / "resolver_cases_json"
    if main_dir.exists():
        for f in sorted(main_dir.glob("st_ready_resolver_cases_*.json")):
            files.append(f)
    drivers_dir = series_dir / "drivers"
    if drivers_dir.exists():
        for driver_dir in sorted(drivers_dir.iterdir()):
            if driver_dir.is_dir():
                fdir = driver_dir / "resolver_cases_json"
                if fdir.exists():
                    for f in sorted(fdir.glob("st_ready_resolver_cases_*.json")):
                        files.append(f)
    return files


def create_resolver_datasource(series_label: str, ds_name: str, files: list[Path]):
    print(f"\n{'='*60}")
    print(f"Creating: {ds_name} ({len(files)} files)")
    print(f"{'='*60}")
    for f in files:
        print(f"  {f.relative_to(PROJECT_ROOT)}")

    cmd = [
        sys.executable, str(ADD_SCRIPT),
        "--kb", str(KB_ID),
        "--operation", "new",
        "--datasource-name", ds_name,
        "--remote-user", "abir.gharbi@st.com",
        "--processor", "JSON",
        "--processor-params", PROCESSOR_PARAMS,
        "--json-split-size", "1000",
        "--empty-json-policy", "skip",
        "--files",
    ]
    cmd.extend(str(f) for f in files)
    cmd.append("--verbose")

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"[WARN] Failed (exit code {result.returncode})")
    else:
        print(f"[OK] Created {ds_name}")


if __name__ == "__main__":
    # U5 resolver
    u5_files = find_resolver_files("stm32cubeu5")
    create_resolver_datasource("U5", "STready_U5_resolver_cases_Datasource", u5_files)

    # WL resolver
    wl_files = find_resolver_files("stm32cubewl")
    create_resolver_datasource("WL", "STready_WL_resolver_cases_Datasource", wl_files)
