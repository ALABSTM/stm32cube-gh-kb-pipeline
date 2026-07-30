<#
.SYNOPSIS
    Split ST-ready issues JSON by peripheral/component for one series or all series.

.DESCRIPTION
    - Reads ST-ready issues-with-images JSON (prefers Alfred-enriched files).
    - Creates per-component JSON files in issues_json/by_component.
    - Does not modify existing export files.

.EXAMPLES
    .\Split_Issues_By_Component.ps1 -Series H7
    .\Split_Issues_By_Component.ps1 -AllSeries
#>

param(
    [string]$Series,

    [switch]$AllSeries,
    [string]$PythonExe = "",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$cfgAllPath = "shared/config/config_all_series.json"
$cfgAll = Get-Content -LiteralPath $cfgAllPath -Raw | ConvertFrom-Json
$seriesMap = @{}
foreach ($seriesFull in @($cfgAll.all_series)) {
    $name = [string]$seriesFull
    if (-not $name.StartsWith("STM32Cube")) {
        continue
    }
    $seriesCode = $name.Substring(9).ToUpperInvariant()
    $seriesMap[$seriesCode] = $name.ToLowerInvariant()
}

if (-not $AllSeries -and -not $Series) {
    throw "Use -Series <name> or -AllSeries."
}

if (-not $AllSeries) {
    $Series = $Series.ToUpperInvariant()
    if (-not $seriesMap.ContainsKey($Series)) {
        $allowed = ($seriesMap.Keys | Sort-Object) -join ", "
        throw "Unsupported series '$Series'. Allowed (from $cfgAllPath): $allowed"
    }
}

if (-not $PythonExe) {
    $venvPy = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPy) {
        $PythonExe = $venvPy
    } else {
        $PythonExe = "python"
    }
}

$splitScript = "pipeline/delivery/split_st_ready_issues_by_component.py"
$splitModule = "pipeline.delivery.split_st_ready_issues_by_component"
if (-not (Test-Path -LiteralPath $splitScript)) {
    throw "Missing script: $splitScript"
}

function Invoke-Split {
    param([string]$Slug)

    $issuesDir = "datasets/07_delivery/st_ready/by_series/$Slug/issues_json"
    if (-not (Test-Path -LiteralPath $issuesDir)) {
        Write-Host "[skip] issues_json not found for $Slug" -ForegroundColor Yellow
        return
    }

    $alfredFile = Get-ChildItem -LiteralPath $issuesDir -Filter "st_ready_issues_with_images_*_with_alfred_image_text.json" -ErrorAction SilentlyContinue |
        Sort-Object FullName |
        Select-Object -First 1

    if (-not $alfredFile) {
        $alfredFile = Get-ChildItem -LiteralPath $issuesDir -Filter "st_ready_issues_*_with_alfred_image_text.json" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch "summary" } |
            Sort-Object FullName |
            Select-Object -First 1
    }

    $fallbackFile = Get-ChildItem -LiteralPath $issuesDir -Filter "st_ready_issues_with_images_*.json" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notmatch "summary|with_alfred_image_text" } |
        Sort-Object FullName |
        Select-Object -First 1

    if (-not $fallbackFile) {
        $fallbackFile = Get-ChildItem -LiteralPath $issuesDir -Filter "st_ready_issues_*.json" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch "summary|with_alfred_image_text|with_images" } |
            Sort-Object FullName |
            Select-Object -First 1
    }

    $inputFile = $null
    if ($alfredFile) {
        $inputFile = $alfredFile.FullName
    } elseif ($fallbackFile) {
        $inputFile = $fallbackFile.FullName
    }

    if (-not $inputFile) {
        Write-Host "[skip] no st_ready_issues_with_images JSON found for $Slug" -ForegroundColor Yellow
        return
    }

    $args = @("-m", $splitModule, "--input-file", $inputFile)
    if ($DryRun) {
        $args += "--dry-run"
    }

    Write-Host "[split] $Slug -> $inputFile" -ForegroundColor Cyan
    & $PythonExe @args
    if ($LASTEXITCODE -ne 0) {
        throw "Split failed for $Slug"
    }
}

$targets = @()
if ($AllSeries) {
    $targets = $seriesMap.Values | Sort-Object -Unique
} else {
    $targets = @($seriesMap[$Series])
}

foreach ($slug in $targets) {
    Invoke-Split -Slug $slug
}

Write-Host "Split by component completed." -ForegroundColor Green
