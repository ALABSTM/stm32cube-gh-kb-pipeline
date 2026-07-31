<#
.SYNOPSIS
    Upload per-component ST-ready issues JSON into KB datasources.

.DESCRIPTION
    - Reads issues_json/by_component/summary_by_component_<series>.json.
    - Creates datasource when missing (issues_H7_ADC, issues_H7_ETH, ...).
    - Reuses saved datasource IDs on next runs and performs add automatically.
    - Keeps existing workflows untouched.

.EXAMPLES
    .\Upload_Issues_By_Component.ps1 -Series H7
    .\Upload_Issues_By_Component.ps1 -Series H7 -DryRun
    .\Upload_Issues_By_Component.ps1 -AllSeries
#>

param(
    [string]$Series,

    [switch]$AllSeries,
    [string]$RemoteUser = "abir.gharbi@st.com",
    [string]$ApiKey = "",
    [string]$ClientAppName = "",
    [int]$KbId = 793,
    [int]$JsonSplitSize = 1000,
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

$uploader = "pipeline_Automation/upload/Add_Data_Source_Files.py"
if (-not (Test-Path -LiteralPath $uploader)) {
    throw "Missing uploader script: $uploader"
}

function New-ProcessorParamsBase64 {
    param([string]$RootTagPath, [string]$LinkUrl, [string]$LinkLabel)
    $json = (@{
        rootTagPath = $RootTagPath
        externalURL = $LinkUrl
        label = $LinkLabel
    } | ConvertTo-Json -Compress)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    return "base64:$([Convert]::ToBase64String($bytes))"
}

function Invoke-Uploader {
    param([string]$Label, [string[]]$CommandArgs)

    if ($DryRun) {
        Write-Host "[dry-run] $Label" -ForegroundColor DarkYellow
        Write-Host ("  " + (($CommandArgs | ForEach-Object {
            if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\\"') + '"' } else { $_ }
        }) -join " "))
        return @()
    }

    Write-Host "[upload] $Label" -ForegroundColor Green

    $tmpOut = [System.IO.Path]::GetTempFileName()
    $tmpErr = [System.IO.Path]::GetTempFileName()

    try {
        $argLine = ($CommandArgs | ForEach-Object {
            if ($_ -match '[\s"]') {
                '"' + ($_ -replace '"', '\\"') + '"'
            } else {
                $_
            }
        }) -join ' '

        $proc = Start-Process -FilePath $PythonExe `
            -ArgumentList $argLine `
            -NoNewWindow `
            -Wait `
            -PassThru `
            -RedirectStandardOutput $tmpOut `
            -RedirectStandardError $tmpErr

        $stdout = @()
        if (Test-Path -LiteralPath $tmpOut) {
            $stdout = @(Get-Content -LiteralPath $tmpOut)
        }
        $stderr = @()
        if (Test-Path -LiteralPath $tmpErr) {
            $stderr = @(Get-Content -LiteralPath $tmpErr)
        }

        $stdout | ForEach-Object { Write-Host $_ }
        $stderr | ForEach-Object { Write-Host $_ -ForegroundColor Red }

        if ($proc.ExitCode -ne 0) {
            $details = @($stderr + $stdout) -join "`n"
            throw "Uploader failed ($Label) exit=$($proc.ExitCode)`n$details"
        }

        return @($stdout + $stderr)
    } finally {
        Remove-Item -LiteralPath $tmpOut -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $tmpErr -ErrorAction SilentlyContinue
    }
}

function Get-UploadAuthArgs {
    $authArgs = @()
    if ($ApiKey) {
        $authArgs += @("--api-key", $ApiKey)
    }
    if ($ClientAppName) {
        $authArgs += @("--client-app-name", $ClientAppName)
    }
    return $authArgs
}

function Parse-DatasourceId {
    param([string[]]$Lines)
    foreach ($line in $Lines) {
        if ($line -match "Datasource ID returned:\s*(\d+)") {
            return [int]$Matches[1]
        }
    }
    return $null
}

function Load-IdCache {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return @{}
    }

    $raw = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    $cache = @{}
    foreach ($p in $raw.PSObject.Properties) {
        $v = 0
        if ([int]::TryParse([string]$p.Value, [ref]$v) -and $v -gt 0) {
            $cache[$p.Name] = $v
        }
    }
    return $cache
}

function Save-IdCache {
    param([hashtable]$Cache, [string]$Path)
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $Cache | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Upload-SeriesByComponent {
    param([string]$Slug)

    $byComponentDir = "datasets/07_delivery/st_ready/by_series/$Slug/issues_json/by_component"
    $seriesCode = ($Slug -replace "^stm32cube", "").ToUpper()
    $summaryPath = Join-Path $byComponentDir "summary_by_component_$($seriesCode.ToLower()).json"
    $idCachePath = Join-Path $byComponentDir "upload_ids_by_component_$($seriesCode.ToLower()).json"

    if (-not (Test-Path -LiteralPath $summaryPath)) {
        Write-Host "[skip] summary not found for ${Slug}: $summaryPath" -ForegroundColor Yellow
        return
    }

    $summary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
    if ($null -eq $summary -or $null -eq $summary.datasources) {
        Write-Host "[skip] no datasources in summary for $Slug" -ForegroundColor Yellow
        return
    }

    $idCache = Load-IdCache -Path $idCachePath
    $items = @($summary.datasources)

    foreach ($item in $items) {
        $datasourceName = [string]$item.datasource_name
        $filePath = [string]$item.output_file
        $issuesCount = [int]$item.issues_count

        if (-not $datasourceName) {
            Write-Host "[skip] datasource_name missing in summary row" -ForegroundColor Yellow
            continue
        }
        if (-not $filePath -or -not (Test-Path -LiteralPath $filePath)) {
            Write-Host "[skip] file missing for $datasourceName" -ForegroundColor Yellow
            continue
        }
        if ($issuesCount -le 0) {
            Write-Host "[skip] empty payload for $datasourceName" -ForegroundColor Yellow
            continue
        }

        $componentLabel = if ($null -eq $item.component -or [string]::IsNullOrWhiteSpace([string]$item.component)) { "GENERAL" } else { [string]$item.component }
        $processorParams = New-ProcessorParamsBase64 `
            -RootTagPath "issues" `
            -LinkUrl "https://github.com/STMicroelectronics/$Slug/issues" `
            -LinkLabel "ST GitHub Analyzer - $seriesCode - $componentLabel"

        $existingId = $null
        if ($idCache.ContainsKey($datasourceName)) {
            $existingId = [int]$idCache[$datasourceName]
        }

        if ($existingId) {
            $args = @(
                $uploader,
                "--kb", "$KbId",
                "--operation", "add",
                "--datasource-id", "$existingId",
                "--remote-user", $RemoteUser,
                "--processor", "JSON",
                "--processor-params", $processorParams,
                "--json-root-mode", "auto",
                "--empty-json-policy", "skip",
                "--json-split-size", "$JsonSplitSize",
                "--timeout", "60",
                "--files", $filePath
            )
            $args += @(Get-UploadAuthArgs)

            try {
                Invoke-Uploader -Label "$datasourceName (add:$existingId)" -CommandArgs $args | Out-Null
                continue
            } catch {
                $errText = [string]$_.Exception.Message
                if ($errText -match "KbDataSourceEntity" -or $errText -match "does not exist \(already deleted or invalid\)") {
                    Write-Host "[warn] cached datasource ID $existingId is invalid for $datasourceName; recreating with operation=new" -ForegroundColor Yellow
                    if ($idCache.ContainsKey($datasourceName)) {
                        $idCache.Remove($datasourceName)
                    }
                } else {
                    throw
                }
            }
        }

        $args = @(
            $uploader,
            "--kb", "$KbId",
            "--operation", "new",
            "--datasource-name", $datasourceName,
            "--datasource-classification", "PUBLIC",
            "--existing-datasource-policy", "add",
            "--remote-user", $RemoteUser,
            "--processor", "JSON",
            "--processor-params", $processorParams,
            "--json-root-mode", "auto",
            "--empty-json-policy", "skip",
            "--json-split-size", "$JsonSplitSize",
            "--timeout", "60",
            "--files", $filePath
        )
        $args += @(Get-UploadAuthArgs)

        $outLines = Invoke-Uploader -Label "$datasourceName (new)" -CommandArgs $args
        if (-not $DryRun) {
            $newId = Parse-DatasourceId -Lines $outLines
            if ($newId) {
                $idCache[$datasourceName] = $newId
                Save-IdCache -Cache $idCache -Path $idCachePath
                Write-Host "[saved] $datasourceName -> $newId" -ForegroundColor DarkCyan
            } else {
                Write-Host "[warn] datasource ID not found in output for $datasourceName" -ForegroundColor Yellow
            }
        }
    }

    if (-not $DryRun) {
        Save-IdCache -Cache $idCache -Path $idCachePath
    }

    Write-Host "[done] upload by component completed for $Slug" -ForegroundColor Cyan
}

$targets = @()
if ($AllSeries) {
    $targets = $seriesMap.Values | Sort-Object -Unique
} else {
    $targets = @($seriesMap[$Series])
}

foreach ($slug in $targets) {
    Upload-SeriesByComponent -Slug $slug
}

Write-Host "All requested series processed." -ForegroundColor Green
