<#
.SYNOPSIS
    Full automated pipeline: Ingestion → Preprocessing → Export → Validation → KB Upload.
    Keeps the ST GitHub Analyzer persona always up-to-date.

.DESCRIPTION
    This script chains all pipeline stages for all configured MCU series,
    validates outputs, and uploads to KB #793 datasources.

    Run weekly (Task Scheduler) or on-demand after major firmware releases.

.PARAMETER Series
    MCU series to process. Default: all (f4, h5, h7, u5, wl).

.PARAMETER SkipIngestion
    Reuse existing raw data (faster re-processing).

.PARAMETER SkipUpload
    Run pipeline only, do not upload to KB.

.PARAMETER ApiKey
    ST AI Bridge API key. Falls back to ST_CHATGPT_API_KEY env var.

.PARAMETER RemoteUser
    Email for API authentication.

.EXAMPLE
    .\Run_Full_Auto_Update_KB.ps1 -RemoteUser "abir.gharbi@st.com"
    .\Run_Full_Auto_Update_KB.ps1 -Series f4,h5 -SkipIngestion
    .\Run_Full_Auto_Update_KB.ps1 -Series h7 -SkipUpload
#>

param(
    [string[]]$Series = @("f4", "h5", "h7", "u5", "wl"),
    [string]$PythonExe = "python",
    [string]$RemoteUser = "",
    [string]$ApiKey = "",
    [switch]$SkipIngestion,
    [switch]$SkipUpload,
    [switch]$ContinueOnError,
    [int]$JsonSplitSize = 1000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
$logDir = Join-Path $repoRoot "logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$logFile = Join-Path $logDir "auto_update_kb_$timestamp.log"

function Log {
    param([string]$Message, [string]$Level = "INFO")
    $entry = "[$Level] $(Get-Date -Format 'HH:mm:ss') $Message"
    Write-Host $entry
    Add-Content -Path $logFile -Value $entry
}

function Run-Step {
    param([string]$Label, [string[]]$CmdArgs)
    Log "=== $Label ==="
    & $PythonExe @CmdArgs 2>&1 | Tee-Object -Append -FilePath $logFile
    if ($LASTEXITCODE -ne 0) {
        if ($ContinueOnError) {
            Log "$Label FAILED (exit code $LASTEXITCODE) - continuing" "WARN"
            return $false
        }
        throw "$Label failed with exit code $LASTEXITCODE"
    }
    Log "$Label completed successfully"
    return $true
}

# ============================================================
# STEP 1: Full pipeline (ingestion + preprocessing + export)
# ============================================================
Log "Starting full auto-update for series: $($Series -join ', ')"

$pipelineArgs = @("-m", "pipeline_Automation.workflow.run_all_series", "--series") + $Series + @("--export-st-ready", "--skip-chunking")

if ($SkipIngestion) {
    $pipelineArgs += "--skip-ingestion"
}
if ($ContinueOnError) {
    $pipelineArgs += "--continue-on-error"
}

$pipelineOk = Run-Step -Label "Full Pipeline (all series)" -CmdArgs $pipelineArgs

if (-not $pipelineOk -and -not $ContinueOnError) {
    Log "Pipeline failed. Aborting." "ERROR"
    exit 1
}

# ============================================================
# STEP 2: Schema Validation Gate
# ============================================================
$validationOk = Run-Step -Label "Schema Validation" -CmdArgs @("-m", "pipeline.evaluation.validate_schemas")

if (-not $validationOk) {
    Log "Schema validation FAILED. KB upload blocked." "ERROR"
    if (-not $ContinueOnError) { exit 2 }
}

# ============================================================
# STEP 3: Upload to KB (if not skipped and validation passed)
# ============================================================
if ($SkipUpload) {
    Log "Upload skipped (--SkipUpload flag)."
} elseif (-not $validationOk) {
    Log "Upload skipped due to validation failure."
} else {
    Log "Starting KB upload..."

    # Datasource ID registry (per series, per artifact type)
    $datasourceIds = @{
        "f4" = @{ issues = 28099; files = 28103; resolver = 28118; diagnostic = 28122 }
        "h5" = @{ issues = 28158; files = 28163; resolver = 28164; diagnostic = 28165 }
        "u5" = @{ issues = 28167; files = 28168; resolver = 28244; diagnostic = 28170 }
        "wl" = @{ issues = 28171; files = 28172; resolver = 28245; diagnostic = 28173 }
        "h7" = @{ issues = 19896; files = 21824; resolver = 20403; diagnostic = 23768 }
    }

    $artifactTypes = @(
        @{ type = "issues";     dir = "issues_json";           pattern = "st_ready_issues_*.json";           rootTag = "issues" }
        @{ type = "files";      dir = "files_json";            pattern = "st_ready_files_*.json";            rootTag = "files" }
        @{ type = "resolver";   dir = "resolver_cases_json";   pattern = "st_ready_resolver_cases_*.json";   rootTag = "resolver_cases" }
        @{ type = "diagnostic"; dir = "diagnostic_cards_json"; pattern = "st_ready_diagnostic_cards_*.json"; rootTag = "diagnostic_cards" }
    )

    $uploaderScript = Join-Path $repoRoot "pipeline_Automation\upload\Add_Data_Source_Files.py"

    foreach ($s in $Series) {
        $seriesDir = Join-Path $repoRoot "datasets\07_delivery\st_ready\by_series\stm32cube$s"

        if (-not (Test-Path $seriesDir)) {
            Log "Series directory not found: $seriesDir - skipping" "WARN"
            continue
        }

        foreach ($artifact in $artifactTypes) {
            $dsId = $datasourceIds[$s][$artifact.type]
            $artifactDir = Join-Path $seriesDir $artifact.dir
            $files = @(Get-ChildItem -Path $artifactDir -Filter $artifact.pattern -File -ErrorAction SilentlyContinue)

            if ($files.Count -eq 0) {
                Log "No $($artifact.type) files for $($s.ToUpper()) - skipping" "WARN"
                continue
            }

            $inputPath = $files[0].FullName
            $uploadArgs = @(
                $uploaderScript,
                "--input", $inputPath,
                "--datasource-id", $dsId,
                "--type", "kb-datasource-add",
                "--root-tag-path", $artifact.rootTag,
                "--json-split-size", $JsonSplitSize
            )

            if ($ApiKey) {
                $uploadArgs += @("--api-key", $ApiKey)
            }
            if ($RemoteUser) {
                $uploadArgs += @("--remote-user", $RemoteUser)
            }

            Run-Step -Label "Upload $($s.ToUpper()) $($artifact.type) (DS#$dsId)" -CmdArgs $uploadArgs
        }
    }
}

# ============================================================
# SUMMARY
# ============================================================
Log "============================================"
Log "AUTO-UPDATE COMPLETE"
Log "  Series processed: $($Series -join ', ')"
Log "  Pipeline: $(if ($pipelineOk) {'OK'} else {'FAILED'})"
Log "  Validation: $(if ($validationOk) {'PASS'} else {'FAIL'})"
Log "  Upload: $(if ($SkipUpload) {'SKIPPED'} else {'DONE'})"
Log "  Log: $logFile"
Log "============================================"
