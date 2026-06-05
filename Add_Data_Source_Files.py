"""Root launcher for datasource upload script.

Allows running:
python Add_Data_Source_Files.py ...
from the repository root.
"""

from pathlib import Path
import runpy


def main() -> None:
    script_path = Path(__file__).resolve().parent / "pipeline_Automation" / "Add_Data_Source_Files.py"
    runpy.run_path(str(script_path), run_name="__main__")


if __name__ == "__main__":
    main()
