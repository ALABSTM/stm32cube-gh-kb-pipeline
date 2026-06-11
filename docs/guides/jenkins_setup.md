# DEPRECATED — Jenkins Removed

This file previously documented a Jenkins setup. **Jenkins is no longer used** in this project.

All CI/CD automation is handled by:

1. **GitHub Actions** — `.github/workflows/auto_update_kb.yml` (cloud, bi-weekly)
2. **PowerShell scripts** — `pipeline_Automation/workflow/Run_Full_Auto_Update_KB.ps1` (local fallback)

See the [GitHub Actions workflow](../../.github/workflows/auto_update_kb.yml) for details.
