"""Upload only st_ready_files_stm32cubef4.json (main repo) with split."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

cmd = [
    sys.executable,
    str(ROOT / "pipeline_Automation" / "Add_Data_Source_Files.py"),
    "--kb", "793",
    "--operation", "add",
    "--datasource-id", "28103",
    "--remote-user", "abir.gharbi@st.com",
    "--processor", "JSON",
    "--processor-params",
    '{"label": "{{repo}} {{file_type}} - {{path}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/{{root_dir}}/{{root_ref}}/{{path_url}}", "rootTagPath": "files"}',
    "--json-split-size", "1000",
    "--files",
    str(ROOT / "datasets" / "07_delivery" / "st_ready" / "by_series" / "stm32cubef4" / "files_json" / "st_ready_files_stm32cubef4.json"),
    "--verbose",
]

sys.exit(subprocess.run(cmd, cwd=str(ROOT)).returncode)
