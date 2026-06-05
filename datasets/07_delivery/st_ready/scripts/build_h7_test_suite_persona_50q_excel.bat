@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%build_h7_test_suite_excel.ps1" ^
  -CsvPath "%SCRIPT_DIR%h7_test_suite_persona_50q_excel_ready.csv" ^
  -XlsxPath "%SCRIPT_DIR%h7_test_suite_persona_50q_excel_ready_real.xlsx" ^
  -XlsPath "%SCRIPT_DIR%h7_test_suite_persona_50q_excel_ready_real.xls"

if errorlevel 1 (
  echo Generation failed.
  exit /b 1
)

echo Generation completed successfully.
endlocal
