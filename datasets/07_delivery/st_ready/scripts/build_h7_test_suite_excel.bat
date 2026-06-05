@echo off
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%build_h7_test_suite_excel.ps1"
if errorlevel 1 (
  echo Failed to build Excel files.
  exit /b 1
)
echo Done.
