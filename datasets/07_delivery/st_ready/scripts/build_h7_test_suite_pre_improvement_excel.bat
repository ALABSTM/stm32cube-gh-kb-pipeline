@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%build_h7_test_suite_excel.ps1" ^
  -CsvPath "%SCRIPT_DIR%h7_test_suite_pre_improvement_50q.csv" ^
  -XlsxPath "%SCRIPT_DIR%h7_test_suite_pre_improvement_50q_real.xlsx" ^
  -XlsPath "%SCRIPT_DIR%h7_test_suite_pre_improvement_50q_real.xls"

if errorlevel 1 (
  echo Generation failed.
  exit /b 1
)

echo Generation completed successfully.
endlocal
