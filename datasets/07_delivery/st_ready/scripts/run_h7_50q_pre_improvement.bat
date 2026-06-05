@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run_h7_50q_ab_test.ps1" ^
  -SuiteCsv "datasets/07_delivery/st_ready/h7_test_suite_pre_improvement_50q.csv" ^
  -OutDir "datasets/06_eval_outputs/pre_improvement"

if errorlevel 1 (
  echo Run failed.
  exit /b 1
)

echo Run completed successfully.
endlocal
