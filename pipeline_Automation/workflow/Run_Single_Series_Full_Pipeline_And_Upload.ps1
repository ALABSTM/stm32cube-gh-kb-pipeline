<#
.SYNOPSIS
    Run the complete STM32Cube preprocessing pipeline and KB upload for one series.

.DESCRIPTION
    One debuggable command per series:
      1. sync parent repo and audit/fix submodule repos in config files
            2. run the full preprocessing workflow with Alfred PDF enrichment
            3. export ST-ready issues/resolver/diagnostic and V3 files for parent and subrepos
            4. run Alfred issue image enrichment for every issue-image JSON under the series
            5. patch Alfred PDF descriptions into root and driver delivery files
            6. validate schemas and fail on unresolved image/PDF placeholders
            7. create KB datasources with operation new, or add to existing IDs when provided
            8. upload driver/subrepo issues/files/diagnostic/resolver outputs into the parent series datasources

.EXAMPLES
    .\pipeline_Automation\workflow\Run_Single_Series_Full_Pipeline_And_Upload.ps1 -Series G4
    .\pipeline_Automation\workflow\Run_Single_Series_Full_Pipeline_And_Upload.ps1 -Series L0 -Mode Prepare
    .\pipeline_Automation\workflow\Run_Single_Series_Full_Pipeline_And_Upload.ps1 -Series L4 -Mode Upload -SkipDrivers
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("G4", "L0", "L1", "L4", "L5", "N6", "U0", "U3", "WB", "WB0", "WBA", "WL3")]
    [string]$Series,

    [ValidateSet("Full", "Prepare", "Upload")]
    [string]$Mode = "Full",

    [string]$RemoteUser = "abir.gharbi@st.com",
    [int]$KbId = 793,
    [string]$PythonExe = "",
    [int]$JsonSplitSize = 1000,
    [int]$IssuesDatasourceId = 0,
    [int]$FilesDatasourceId = 0,
    [int]$DiagnosticDatasourceId = 0,
    [int]$ResolverDatasourceId = 0,
    [switch]$SkipDrivers,
    [switch]$SkipSchemaValidation,
    [switch]$ContinueOnWorkflowError,
    [ValidateSet("Replace", "Add")]
    [string]$ExistingDatasourceMode = "Replace",
    [ValidateSet("Fail", "Warn", "Off")]
    [string]$PlaceholderPolicy = "Fail",
    [switch]$SkipAlfredEnrichment,
    [switch]$SkipPlaceholderGate,
    [switch]$RunAlfredBeforeUpload,
    [switch]$UseAlfredProxy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

# Auto-detect venv python if not specified.
if (-not $PythonExe) {
    $venvPy = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPy) {
        $PythonExe = $venvPy
        Write-Host "Using venv python: $PythonExe" -ForegroundColor DarkCyan
    } else {
        $PythonExe = "python"
        Write-Host "Warning: .venv not found, using system python" -ForegroundColor Yellow
    }
}

$seriesMap = @{
    "G4" = @{ Slug = "stm32cubeg4"; Repo = "STM32CubeG4"; Config = "shared/config/config_g4.json" }
    "L0" = @{ Slug = "stm32cubel0"; Repo = "STM32CubeL0"; Config = "shared/config/config_l0.json" }
    "L1" = @{ Slug = "stm32cubel1"; Repo = "STM32CubeL1"; Config = "shared/config/config_l1.json" }
    "L4" = @{ Slug = "stm32cubel4"; Repo = "STM32CubeL4"; Config = "shared/config/config_l4.json" }
    "L5" = @{ Slug = "stm32cubel5"; Repo = "STM32CubeL5"; Config = "shared/config/config_l5.json" }
    "N6" = @{ Slug = "stm32cuben6"; Repo = "STM32CubeN6"; Config = "shared/config/config_n6.json" }
    "U0" = @{ Slug = "stm32cubeu0"; Repo = "STM32CubeU0"; Config = "shared/config/config_u0.json" }
    "U3" = @{ Slug = "stm32cubeu3"; Repo = "STM32CubeU3"; Config = "shared/config/config_u3.json" }
    "WB" = @{ Slug = "stm32cubewb"; Repo = "STM32CubeWB"; Config = "shared/config/config_wb.json" }
    "WB0" = @{ Slug = "stm32cubewb0"; Repo = "STM32CubeWB0"; Config = "shared/config/config_wb0.json" }
    "WBA" = @{ Slug = "stm32cubewba"; Repo = "STM32CubeWBA"; Config = "shared/config/config_wba.json" }
    "WL3" = @{ Slug = "stm32cubewl3"; Repo = "STM32CubeWL3"; Config = "shared/config/config_wl3.json" }
}

$seriesInfo = $seriesMap[$Series]
$slug = $seriesInfo.Slug
$seriesRepo = $seriesInfo.Repo
$configPath = $seriesInfo.Config
$deliveryRoot = "datasets/07_delivery/st_ready/by_series/$slug"
$uploader = "pipeline_Automation/upload/Add_Data_Source_Files.py"
$idsOutput = Join-Path $deliveryRoot "upload_datasource_ids_$slug.json"
$globalConfigPath = "shared/config/config_all_series.json"
$uploadMaxRetries = 5
$uploadTimeoutSeconds = 300

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    Write-Host "`n===== $Label =====" -ForegroundColor Cyan
    Write-Host ($Args -join " ") -ForegroundColor DarkGray
    $pythonArgs = @("-u") + $Args
    & $PythonExe @pythonArgs
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Invoke-CapturedPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    Write-Host "`n===== $Label =====" -ForegroundColor Cyan
    Write-Host ($Args -join " ") -ForegroundColor DarkGray

    $tmpOut = [System.IO.Path]::GetTempFileName()
    $tmpErr = [System.IO.Path]::GetTempFileName()

    try {
        $pythonArgs = @("-u") + $Args
        $argLine = ($pythonArgs | ForEach-Object {
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

        $exitCode = $proc.ExitCode
        $output = @($stdout + $stderr)
    }
    finally {
        Remove-Item -LiteralPath $tmpOut -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $tmpErr -ErrorAction SilentlyContinue
    }

    if ($exitCode -ne 0) {
        $tail = @($output | Select-Object -Last 25)
        $tailText = if ($tail.Count -gt 0) { "`n" + ($tail -join "`n") } else { "" }
        throw "$Label failed with exit code $exitCode$tailText"
    }
    return @($output | ForEach-Object { [string]$_ })
}

function Get-DatasourceIdFromOutput {
    param([string[]]$OutputLines)

    foreach ($line in $OutputLines) {
        if ($line -match "Datasource ID returned:\s*(\d+)") {
            return [int]$Matches[1]
        }
    }
    return $null
}

function New-ProcessorParamsArg {
    param(
        [string]$RootTagPath,
        [string]$LinkUrlTemplate,
        [string]$LinkLabelTemplate
    )

    $params = @{
        rootTagPath = $RootTagPath
        externalURL = $LinkUrlTemplate
        label = $LinkLabelTemplate
    }
    $json = $params | ConvertTo-Json -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    return "base64:$([Convert]::ToBase64String($bytes))"
}

function Test-JsonRootIsEmpty {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$RootKey
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $true
    }

    $json = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    if ($null -eq $json) {
        return $true
    }

    # Some exports are root arrays (e.g. []), others are objects with root tag.
    if ($json -is [System.Array]) {
        return @($json).Count -eq 0
    }

    $prop = $json.PSObject.Properties[$RootKey]
    if ($null -eq $prop -or $null -eq $prop.Value) {
        return $true
    }

    return @($prop.Value).Count -eq 0
}

function Assert-RequiredFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required file not found: $Path"
    }
}

function Get-ConfigRepos {
    param([string]$Path)
    $cfg = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    return @($cfg.repos | ForEach-Object { [string]$_ })
}

function Get-ReposWithIssueDocs {
    param([string[]]$Repos)

    $withIssueDocs = @()
    foreach ($repo in $Repos) {
        $repoSlug = $repo.ToLowerInvariant()
        $docsFile = "data/docs_issues_${repoSlug}_v2.json"
        if (Test-Path -LiteralPath $docsFile) {
            $withIssueDocs += $repo
        }
    }
    return $withIssueDocs
}

function Assert-SeriesFilesCoverage {
    param([string[]]$Repos)

    Write-Host "`n===== V3 files coverage gate for $Series =====" -ForegroundColor Cyan
    $missingDocs = @()
    $missingDelivery = @()

    foreach ($repo in $Repos) {
        $repoSlug = $repo.ToLowerInvariant()
        $docsFile = "data/docs_files_${repoSlug}_v3.json"

        if ($repo -eq $seriesRepo) {
            $deliveryFile = "$deliveryRoot/files_json/st_ready_files_${repoSlug}_v3.json"
        } else {
            $deliveryFile = "$deliveryRoot/drivers/$repoSlug/files_json/st_ready_files_${repoSlug}_v3.json"
        }

        $hasDocs = Test-Path -LiteralPath $docsFile
        if (-not $hasDocs) {
            $missingDocs += "docs missing: $docsFile"
            continue
        }

        if (-not (Test-Path -LiteralPath $deliveryFile)) {
            $missingDelivery += "delivery missing: $deliveryFile"
        }
    }

    if ($missingDocs.Count -gt 0) {
        Write-Host "[WARN] Some repos have no docs_files_*_v3 input; they are skipped for this gate:" -ForegroundColor Yellow
        $missingDocs | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    }

    if ($missingDelivery.Count -gt 0) {
        $missingDelivery | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        throw "V3 files coverage incomplete for $Series. Do not upload or move to next series yet."
    }

    Write-Host "OK: all repos with docs_files_*_v3.json have matching st_ready_files_*_v3.json" -ForegroundColor Green
}

function Invoke-ParentRepoDeliveryExports {
    Write-Host "`n===== Export parent ST-ready delivery for $Series ($seriesRepo) =====" -ForegroundColor Cyan

    Invoke-Step "Export parent issues JSON" @(
        "-m", "pipeline.delivery.export_st_ready_issues",
        "--repo", $seriesRepo
    )

    Invoke-Step "Export parent resolver cases JSON" @(
        "-m", "pipeline.delivery.export_st_ready_resolver_cases",
        "--repo", $seriesRepo
    )

    Invoke-Step "Export parent diagnostic cards JSON" @(
        "-m", "pipeline.delivery.export_st_ready_diagnostic_cards",
        "--repo", $seriesRepo
    )

    Invoke-Step "Export parent issues with image URLs" @(
        "-m", "pipeline.delivery.export_st_ready_issues_with_images",
        "--repo", $seriesRepo
    )
}

function Invoke-SubrepoIssueDeliveryExports {
    param([string[]]$Repos)

    $issueRepos = @(Get-ReposWithIssueDocs -Repos $Repos | Where-Object { $_ -ne $seriesRepo })
    if ($issueRepos.Count -eq 0) {
        Write-Host "[SKIP] No driver/subrepo issue docs found for $Series" -ForegroundColor Yellow
        return
    }

    $repoArgs = @()
    foreach ($repo in $issueRepos) {
        $repoArgs += @("--repo", $repo)
    }

    Invoke-Step "Export driver/subrepo issues JSON" (@("-m", "pipeline.delivery.export_st_ready_issues") + $repoArgs)
    Invoke-Step "Export driver/subrepo resolver cases JSON" (@("-m", "pipeline.delivery.export_st_ready_resolver_cases") + $repoArgs)
    Invoke-Step "Export driver/subrepo diagnostic cards JSON" (@("-m", "pipeline.delivery.export_st_ready_diagnostic_cards") + $repoArgs)
    Invoke-Step "Export driver/subrepo issues with image URLs" (@("-m", "pipeline.delivery.export_st_ready_issues_with_images") + $repoArgs)
}

function Invoke-AlfredIssueImageDescriptionsForSeries {
    $issueImageFiles = @(Get-ChildItem -Path $deliveryRoot -Recurse -Filter "st_ready_issues_with_images_*.json" -ErrorAction SilentlyContinue |
        Where-Object { $_.Directory.Name -eq "issues_json" -and $_.Name -notmatch "summary" } |
        Sort-Object FullName)

    if ($issueImageFiles.Count -eq 0) {
        Write-Host "[SKIP] No issue image JSON files found for Alfred under $deliveryRoot" -ForegroundColor Yellow
        return
    }

    foreach ($file in $issueImageFiles) {
        $alfredArgs = @(
            "pipeline_Automation/alfred/enrich_json_images_with_alfred.py",
            "--input", $file.FullName,
            "--remote-user", $RemoteUser,
            "--inplace"
        )
        if ($UseAlfredProxy) {
            $alfredArgs += "--use-proxy"
        }
        Invoke-Step "Alfred issue image descriptions for $($file.Directory.Parent.Name)" $alfredArgs
    }
}

function Invoke-AlfredPdfFigureDescriptions {
    $args = @("pipeline_Automation/alfred/enrich_pdf_figures_with_alfred.py")
    if ($UseAlfredProxy) {
        $args += "--use-proxy"
    }
    Invoke-Step "Alfred PDF figure descriptions" $args
}

function Invoke-PlaceholderGate {
    Write-Host "`n===== Placeholder gate for $Series (policy=$PlaceholderPolicy) =====" -ForegroundColor Cyan
    if ($PlaceholderPolicy -ne "Off") {
        $placeholderMatches = Select-String -Path "$deliveryRoot/**/*.json" `
            -Pattern "IMAGE DESCRIPTION UNAVAILABLE|\[FIGURE DETECTED\]|Figure detected on page|no technical description is available yet" `
            -ErrorAction SilentlyContinue

        if ($placeholderMatches) {
            $reportPath = Join-Path $deliveryRoot "alfred_placeholder_report_$slug.txt"
            $placeholderLines = @($placeholderMatches | ForEach-Object { $_.Line })
            $placeholderLines | Set-Content -LiteralPath $reportPath -Encoding UTF8

            Write-Host "Found unresolved Alfred placeholders: $($placeholderLines.Count)" -ForegroundColor Yellow
            Write-Host "Report: $reportPath" -ForegroundColor Yellow

            $placeholderLines | Select-Object -First 5 | ForEach-Object { Write-Host $_ -ForegroundColor Red }
            if ($placeholderLines.Count -gt 5) {
                Write-Host "... ($($placeholderLines.Count - 5) more lines in report)" -ForegroundColor DarkYellow
            }

            if ($PlaceholderPolicy -eq "Fail") {
                throw "Unresolved Alfred image/PDF placeholders found for $Series"
            }

            Write-Host "[WARN] Continuing despite unresolved placeholders (PlaceholderPolicy=Warn)" -ForegroundColor Yellow
        } else {
            Write-Host "OK: no unresolved Alfred image/PDF placeholders for $Series" -ForegroundColor Green
        }
    } else {
        Write-Host "[SKIP] Placeholder gate disabled (PlaceholderPolicy=Off)" -ForegroundColor Yellow
    }
}

function Invoke-PrepareSeries {
    if (-not (Test-Path -LiteralPath $configPath)) {
        throw "Config not found: $configPath"
    }

    $env:STM32CUBE_CONFIG = $configPath
    Write-Host "`nPreparing $Series using $configPath" -ForegroundColor Green

    Invoke-Step "Sync configured repos" @("-m", "pipeline.ingestion.repo_sync_service")
    Invoke-Step "Audit/fix submodule repos" @("-m", "pipeline.evaluation.audit_config_submodules", "--fix")
    Invoke-Step "Audit submodule repos gate" @("-m", "pipeline.evaluation.audit_config_submodules")

    $workflowArgs = @("-m", "pipeline.run_full_workflow", "--skip-chunking")
    if ($SkipAlfredEnrichment) {
        $workflowArgs += "--no-enrich-pdf"
    }
    if ($ContinueOnWorkflowError) {
        $workflowArgs += "--continue-on-error"
    }
    Invoke-Step "Full preprocessing workflow with Alfred PDF" $workflowArgs

    $repos = Get-ConfigRepos $configPath
    Invoke-ParentRepoDeliveryExports
    Invoke-SubrepoIssueDeliveryExports -Repos $repos
    if ($SkipAlfredEnrichment) {
        Write-Host "[SKIP] Alfred issue image enrichment disabled by -SkipAlfredEnrichment" -ForegroundColor Yellow
    } else {
        Invoke-AlfredIssueImageDescriptionsForSeries
    }

    $exportArgs = @("-m", "pipeline.delivery.export_st_ready_files", "--v3")
    foreach ($repo in $repos) {
        $exportArgs += @("--repo", $repo)
    }
    Invoke-Step "Export V3 ST-ready files for configured repos" $exportArgs
    Assert-SeriesFilesCoverage -Repos $repos

    if ($SkipAlfredEnrichment) {
        Write-Host "[SKIP] Patch Alfred PDF descriptions disabled by -SkipAlfredEnrichment" -ForegroundColor Yellow
    } else {
        Invoke-Step "Patch Alfred PDF descriptions into root and driver delivery files" @("pipeline_Automation/patch_pdf_descriptions_in_delivery.py")
    }

    if (-not $SkipSchemaValidation) {
        Invoke-Step "Schema validation" @("-m", "pipeline.evaluation.validate_schemas")
    }

    if ($SkipPlaceholderGate) {
        Write-Host "[SKIP] Placeholder gate disabled by -SkipPlaceholderGate" -ForegroundColor Yellow
    } else {
        Invoke-PlaceholderGate
    }
}

function Invoke-PreUploadAlfredFinalize {
    if (-not (Test-Path -LiteralPath $configPath)) {
        throw "Config not found: $configPath"
    }
    if (-not (Test-Path -LiteralPath $deliveryRoot)) {
        throw "Delivery root not found for ${Series}: $deliveryRoot. Upload mode requires pre-generated delivery artifacts. Run -Mode Full, or run -Mode Prepare then upload from the same workflow run/artifacts."
    }

    $env:STM32CUBE_CONFIG = $configPath

    if ($SkipAlfredEnrichment) {
        Write-Host "[SKIP] Pre-upload Alfred finalize disabled by -SkipAlfredEnrichment" -ForegroundColor Yellow
    } else {
        Invoke-AlfredPdfFigureDescriptions
        Invoke-AlfredIssueImageDescriptionsForSeries
        Invoke-Step "Patch Alfred PDF descriptions into root and driver delivery files" @("pipeline_Automation/patch_pdf_descriptions_in_delivery.py")
    }

    if (-not $SkipSchemaValidation) {
        Invoke-Step "Schema validation" @("-m", "pipeline.evaluation.validate_schemas")
    }

    if ($SkipPlaceholderGate) {
        Write-Host "[SKIP] Placeholder gate disabled by -SkipPlaceholderGate" -ForegroundColor Yellow
    } else {
        Invoke-PlaceholderGate
    }
}

function Invoke-UploadJsonNew {
    param(
        [string]$Label,
        [string]$FilePath,
        [string]$RootKey,
        [string]$DatasourceName,
        [string]$ProcessorParams,
        [switch]$AllowEmpty
    )

    Assert-RequiredFile $FilePath
    if ((Test-JsonRootIsEmpty -Path $FilePath -RootKey $RootKey) -and $AllowEmpty) {
        Write-Host "[SKIP] $Label is empty: $FilePath" -ForegroundColor Yellow
        return $null
    }

    $args = @(
        $uploader,
        "--kb", "$KbId",
        "--operation", "new",
        "--datasource-name", $DatasourceName,
        "--datasource-classification", "PUBLIC",
        "--remote-user", $RemoteUser,
        "--processor", "JSON",
        "--processor-params", $ProcessorParams,
        "--json-root-mode", "auto",
        "--empty-json-policy", "skip",
        "--json-split-size", "$JsonSplitSize",
        "--existing-datasource-policy", $ExistingDatasourceMode.ToLowerInvariant(),
        "--skip-auth-precheck",
        "--max-retries", "$uploadMaxRetries",
        "--timeout", "$uploadTimeoutSeconds",
        "--files", (Resolve-Path $FilePath).Path
    )

    $output = Invoke-CapturedPython "Create datasource and upload $Label" $args
    $id = Get-DatasourceIdFromOutput $output
    if ($null -eq $id) {
        throw "Could not parse datasource ID for $Label"
    }
    return $id
}

function Invoke-UploadJsonAdd {
    param(
        [string]$Label,
        [string]$FilePath,
        [string]$RootKey,
        [int]$DatasourceId,
        [string]$ProcessorParams,
        [string]$DatasourceNameForFallback = "",
        [switch]$AllowEmpty
    )

    if ($DatasourceId -le 0) {
        throw "Invalid datasource ID for ${Label}: $DatasourceId"
    }

    if (-not (Test-Path -LiteralPath $FilePath)) {
        if ($AllowEmpty) {
            Write-Host "[SKIP] $Label file not found (allowed empty): $FilePath" -ForegroundColor Yellow
            return $DatasourceId
        }
        Assert-RequiredFile $FilePath
    }
    if ((Test-JsonRootIsEmpty -Path $FilePath -RootKey $RootKey) -and $AllowEmpty) {
        Write-Host "[SKIP] $Label is empty: $FilePath" -ForegroundColor Yellow
        return $DatasourceId
    }

    if ($ExistingDatasourceMode -eq "Replace") {
        $deleteArgs = @(
            $uploader,
            "--kb", "$KbId",
            "--operation", "delete",
            "--datasource-id", "$DatasourceId",
            "--remote-user", $RemoteUser,
            "--delete-not-found-policy", "ignore",
            "--skip-auth-precheck",
            "--max-retries", "$uploadMaxRetries",
            "--timeout", "$uploadTimeoutSeconds"
        )

        $deleteOutput = Invoke-CapturedPython "Clear existing content for $Label in DS#$DatasourceId" $deleteArgs
        $deleteText = ($deleteOutput -join "`n")

        if ($deleteText -match "Datasource not found") {
            if (-not $DatasourceNameForFallback) {
                throw "DS#$DatasourceId for $Label is missing after delete step, and no fallback datasource name was provided."
            }
            Write-Host "[WARN] DS#$DatasourceId for $Label no longer exists. Recreating datasource '$DatasourceNameForFallback'." -ForegroundColor Yellow
            return Invoke-UploadJsonNew `
                -Label $Label `
                -FilePath $FilePath `
                -RootKey $RootKey `
                -DatasourceName $DatasourceNameForFallback `
                -ProcessorParams $ProcessorParams `
                -AllowEmpty:$AllowEmpty
        } else {
            Write-Host "[REPLACE] DS#$DatasourceId content cleared for $Label. Re-uploading into same datasource." -ForegroundColor DarkCyan
        }
    } else {
        Write-Host "[ADD] Existing datasource mode is Add for $Label (DS#$DatasourceId): appending files." -ForegroundColor DarkCyan
    }

    $args = @(
        $uploader,
        "--kb", "$KbId",
        "--operation", "add",
        "--datasource-id", "$DatasourceId",
        "--remote-user", $RemoteUser,
        "--processor", "JSON",
        "--processor-params", $ProcessorParams,
        "--json-root-mode", "auto",
        "--empty-json-policy", "skip",
        "--json-split-size", "$JsonSplitSize",
        "--skip-auth-precheck",
        "--max-retries", "$uploadMaxRetries",
        "--timeout", "$uploadTimeoutSeconds",
        "--files", (Resolve-Path $FilePath).Path
    )

    try {
        Invoke-CapturedPython "Upload $Label into existing DS#$DatasourceId" $args | Out-Null
        return $DatasourceId
    }
    catch {
        $errorText = $_.Exception.Message
        $normalized = $errorText.ToLowerInvariant()

        $isDatasourceMissing = (
            $normalized -match "could not find any entity of type .*kbdatasourceentity" -or
            $normalized -match "datasource not found" -or
            $normalized -match "cannot upload files to deleted datasource" -or
            $normalized -match "errorcode=3000"
        )

        if ($isDatasourceMissing -and $DatasourceNameForFallback) {
            Write-Host "[WARN] Upload failed because DS#$DatasourceId for $Label does not exist. Recreating datasource '$DatasourceNameForFallback'." -ForegroundColor Yellow
            return Invoke-UploadJsonNew `
                -Label $Label `
                -FilePath $FilePath `
                -RootKey $RootKey `
                -DatasourceName $DatasourceNameForFallback `
                -ProcessorParams $ProcessorParams `
                -AllowEmpty:$AllowEmpty
        }

            if ($isDatasourceMissing -and (-not $DatasourceNameForFallback)) {
                throw "Upload failed because DS#$DatasourceId for $Label does not exist, and no fallback datasource name was provided."
            }

        throw
    }
}

function Get-SubrepoDeliveryFiles {
    param(
        [string]$SubDirectory,
        [string]$Pattern
    )

    $selected = @()
    $driverDirs = @(Get-ChildItem "$deliveryRoot/drivers" -Directory -ErrorAction SilentlyContinue | Sort-Object FullName)

    foreach ($driverDir in $driverDirs) {
        $targetDir = Join-Path $driverDir.FullName $SubDirectory
        if (-not (Test-Path -LiteralPath $targetDir)) {
            continue
        }

        $selected += @(Get-ChildItem $targetDir -Filter $Pattern -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch "summary" } |
            Sort-Object FullName)
    }

    return @($selected)
}

function Get-NonEmptyJsonFiles {
    param(
        [System.IO.FileInfo[]]$Files,
        [string]$RootKey
    )

    $selected = @()
    foreach ($file in @($Files)) {
        if (-not (Test-JsonRootIsEmpty -Path $file.FullName -RootKey $RootKey)) {
            $selected += $file
        }
    }
    return @($selected)
}

function Get-SubrepoIssueUploadFiles {
    $selected = @()
    $driverDirs = @(Get-ChildItem "$deliveryRoot/drivers" -Directory -ErrorAction SilentlyContinue | Sort-Object FullName)

    foreach ($driverDir in $driverDirs) {
        $issuesDir = Join-Path $driverDir.FullName "issues_json"
        if (-not (Test-Path -LiteralPath $issuesDir)) {
            continue
        }

        $withImages = @(Get-ChildItem $issuesDir -Filter "st_ready_issues_with_images_*.json" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch "summary" } |
            Sort-Object FullName)
        if ($withImages.Count -gt 0) {
            $selected += $withImages
            continue
        }

        $plainIssues = @(Get-ChildItem $issuesDir -Filter "st_ready_issues_*.json" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch "summary" -and $_.Name -notmatch "with_images" } |
            Sort-Object FullName)
        $selected += $plainIssues
    }

    return @($selected)
}

function Invoke-UploadSubrepoDeliveryAdd {
    param(
        [string]$Label,
        [System.IO.FileInfo[]]$Files,
        [string]$RootKey,
        [AllowNull()][object]$DatasourceId,
        [string]$ProcessorParams
    )

    $effectiveDatasourceId = 0
    $filesList = @($Files)
    if ($null -ne $DatasourceId) {
        $effectiveDatasourceId = [int]$DatasourceId
    }

    if ($SkipDrivers) {
        Write-Host "[SKIP] Driver/subrepo upload disabled by -SkipDrivers" -ForegroundColor Yellow
        return
    }

    if ($effectiveDatasourceId -le 0) {
        if ($filesList.Count -gt 0) {
            Write-Host "[SKIP] No datasource ID available for $Label; $($filesList.Count) driver/subrepo file(s) not uploaded" -ForegroundColor Yellow
        }
        return
    }

    if ($filesList.Count -eq 0) {
        Write-Host "[SKIP] No driver/subrepo $Label found for $Series under $deliveryRoot/drivers" -ForegroundColor Yellow
        return
    }

    foreach ($file in $filesList) {
        $args = @(
            $uploader,
            "--kb", "$KbId",
            "--operation", "add",
            "--datasource-id", "$effectiveDatasourceId",
            "--remote-user", $RemoteUser,
            "--processor", "JSON",
            "--processor-params", $ProcessorParams,
            "--json-root-mode", "auto",
            "--empty-json-policy", "skip",
            "--json-split-size", "$JsonSplitSize",
            "--skip-auth-precheck",
            "--max-retries", "$uploadMaxRetries",
            "--timeout", "$uploadTimeoutSeconds",
            "--files", $file.FullName
        )
        Invoke-CapturedPython "Upload driver/subrepo $($file.Directory.Parent.Name) $Label into ${Series} DS#$effectiveDatasourceId" $args | Out-Null
    }
}

function Set-OrAddProperty {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Target,
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [AllowNull()][object]$Value
    )

    $prop = $Target.PSObject.Properties[$Name]
    if ($null -eq $prop) {
        $Target | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    } else {
        $prop.Value = $Value
    }
}

function Sync-GlobalConfigDatasourceIds {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Ids
    )

    if (-not (Test-Path -LiteralPath $globalConfigPath)) {
        Write-Host "[WARN] Global config not found, skip datasource sync: $globalConfigPath" -ForegroundColor Yellow
        return
    }

    try {
        $cfg = Get-Content -LiteralPath $globalConfigPath -Raw | ConvertFrom-Json
        if ($null -eq $cfg -or $null -eq $cfg.kb_datasource_ids) {
            Write-Host "[WARN] Invalid global config structure, skip datasource sync: $globalConfigPath" -ForegroundColor Yellow
            return
        }

        $seriesKey = $seriesRepo
        $seriesProp = $cfg.kb_datasource_ids.PSObject.Properties[$seriesKey]
        if ($null -eq $seriesProp) {
            $entry = [pscustomobject]@{}
            $cfg.kb_datasource_ids | Add-Member -NotePropertyName $seriesKey -NotePropertyValue $entry
        } else {
            $entry = $seriesProp.Value
        }

        foreach ($name in @("issues", "files", "diagnostic", "resolver")) {
            $value = $Ids.$name
            if (($value -as [int]) -gt 0) {
                Set-OrAddProperty -Target $entry -Name $name -Value ([int]$value)
            }
        }

        $cfg | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $globalConfigPath -Encoding UTF8
        Write-Host "[UPLOAD] Global datasource IDs synced for ${seriesKey}: $globalConfigPath" -ForegroundColor DarkCyan
    }
    catch {
        Write-Host "[WARN] Failed to sync global datasource IDs: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Save-DatasourceIdsSnapshot {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Ids,
        [string]$Reason = ""
    )

    New-Item -ItemType Directory -Force -Path $deliveryRoot | Out-Null
    $Ids["uploaded_at"] = (Get-Date).ToString("s")
    if ($Reason) {
        $Ids["last_update_reason"] = $Reason
        $Ids["last_successful_stage"] = $Reason
    }

    $Ids | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $idsOutput -Encoding UTF8
    if ($env:GITHUB_ACTIONS -eq "true") {
        Write-Host "[UPLOAD] Skipping shared/config/config_all_series.json update in GitHub Actions (runner-local state must stay immutable)." -ForegroundColor DarkYellow
    } else {
        Sync-GlobalConfigDatasourceIds -Ids $Ids
    }

    if ($Reason) {
        Write-Host "[UPLOAD] Datasource ID registry updated ($Reason): $idsOutput" -ForegroundColor DarkCyan
    } else {
        Write-Host "[UPLOAD] Datasource ID registry updated: $idsOutput" -ForegroundColor DarkCyan
    }
}

function Invoke-UploadSeries {
    if (-not (Test-Path -LiteralPath $deliveryRoot)) {
        throw "Delivery root not found for ${Series}: $deliveryRoot. Upload mode requires pre-generated delivery artifacts. Run with -Mode Full, or run with -Mode Prepare then upload from the same workflow run/artifacts."
    }

    # Reuse datasource IDs from the previous run when available.
    # Existing datasources are reused. Refresh policy is controlled by -ExistingDatasourceMode.
    $reuseLocalSnapshot = $true
    if ($env:GITHUB_ACTIONS -eq "true") {
        $reuseLocalSnapshot = $false
        Write-Host "[UPLOAD] Ignoring runner-local datasource snapshot in GitHub Actions: $idsOutput" -ForegroundColor DarkYellow
    }

    if ($reuseLocalSnapshot -and (Test-Path -LiteralPath $idsOutput)) {
        try {
            $saved = Get-Content -LiteralPath $idsOutput -Raw | ConvertFrom-Json
            if ($null -ne $saved) {
                if (($IssuesDatasourceId -le 0) -and ($saved.issues -as [int]) -gt 0) {
                    $IssuesDatasourceId = [int]$saved.issues
                }
                if (($FilesDatasourceId -le 0) -and ($saved.files -as [int]) -gt 0) {
                    $FilesDatasourceId = [int]$saved.files
                }
                if (($DiagnosticDatasourceId -le 0) -and ($saved.diagnostic -as [int]) -gt 0) {
                    $DiagnosticDatasourceId = [int]$saved.diagnostic
                }
                if (($ResolverDatasourceId -le 0) -and ($saved.resolver -as [int]) -gt 0) {
                    $ResolverDatasourceId = [int]$saved.resolver
                }

                Write-Host "[UPLOAD] Reusing datasource IDs from $idsOutput when available." -ForegroundColor DarkCyan
            }
        } catch {
            Write-Host "[WARN] Could not parse saved datasource IDs from $idsOutput. Proceeding without reuse." -ForegroundColor Yellow
        }
    }

    # Fallback to shared/config/config_all_series.json when no local snapshot IDs are available.
    if ((($IssuesDatasourceId -le 0) -or ($FilesDatasourceId -le 0) -or ($DiagnosticDatasourceId -le 0) -or ($ResolverDatasourceId -le 0)) -and (Test-Path -LiteralPath $globalConfigPath)) {
        try {
            $cfg = Get-Content -LiteralPath $globalConfigPath -Raw | ConvertFrom-Json
            $seriesEntry = $null
            if ($null -ne $cfg -and $null -ne $cfg.kb_datasource_ids) {
                $prop = $cfg.kb_datasource_ids.PSObject.Properties[$seriesRepo]
                if ($null -ne $prop) {
                    $seriesEntry = $prop.Value
                }
            }

            if ($null -ne $seriesEntry) {
                if (($IssuesDatasourceId -le 0) -and ($seriesEntry.issues -as [int]) -gt 0) {
                    $IssuesDatasourceId = [int]$seriesEntry.issues
                }
                if (($FilesDatasourceId -le 0) -and ($seriesEntry.files -as [int]) -gt 0) {
                    $FilesDatasourceId = [int]$seriesEntry.files
                }
                if (($DiagnosticDatasourceId -le 0) -and ($seriesEntry.diagnostic -as [int]) -gt 0) {
                    $DiagnosticDatasourceId = [int]$seriesEntry.diagnostic
                }
                if (($ResolverDatasourceId -le 0) -and ($seriesEntry.resolver -as [int]) -gt 0) {
                    $ResolverDatasourceId = [int]$seriesEntry.resolver
                }

                Write-Host "[UPLOAD] Reusing datasource IDs from $globalConfigPath for ${seriesRepo} when available." -ForegroundColor DarkCyan
            }
        } catch {
            Write-Host "[WARN] Could not parse datasource IDs from $globalConfigPath. Proceeding without global fallback." -ForegroundColor Yellow
        }
    }

    $issuesFile = "$deliveryRoot/issues_json/st_ready_issues_with_images_$slug.json"
    $filesFile = "$deliveryRoot/files_json/st_ready_files_${slug}_v3.json"
    $diagnosticFile = "$deliveryRoot/diagnostic_cards_json/st_ready_diagnostic_cards_$slug.json"
    $resolverFile = "$deliveryRoot/resolver_cases_json/st_ready_resolver_cases_$slug.json"

    $driverIssueFiles = @(Get-SubrepoIssueUploadFiles)
    $driverFiles = @(Get-SubrepoDeliveryFiles -SubDirectory "files_json" -Pattern "st_ready_files_*.json")
    $driverDiagnosticFiles = @(Get-SubrepoDeliveryFiles -SubDirectory "diagnostic_cards_json" -Pattern "st_ready_diagnostic_cards_*.json")
    $driverResolverFiles = @(Get-SubrepoDeliveryFiles -SubDirectory "resolver_cases_json" -Pattern "st_ready_resolver_cases_*.json")
    $driverIssueNonEmptyFiles = @(Get-NonEmptyJsonFiles -Files $driverIssueFiles -RootKey "issues")
    $driverDiagnosticNonEmptyFiles = @(Get-NonEmptyJsonFiles -Files $driverDiagnosticFiles -RootKey "diagnostic_cards")
    $driverResolverNonEmptyFiles = @(Get-NonEmptyJsonFiles -Files $driverResolverFiles -RootKey "resolver_cases")

    $issuesParams = New-ProcessorParamsArg `
        -RootTagPath "issues" `
        -LinkUrlTemplate "{{github_url}}" `
        -LinkLabelTemplate "{{repo}} issue #{{issue_number}} - {{issue_title}}"
    $filesParams = New-ProcessorParamsArg `
        -RootTagPath "files" `
        -LinkUrlTemplate "https://github.com/STMicroelectronics/{{repo}}/search?q={{path}}&type=code" `
        -LinkLabelTemplate "{{repo}} {{file_type}} - {{path}}"
    $diagnosticParams = New-ProcessorParamsArg `
        -RootTagPath "diagnostic_cards" `
        -LinkUrlTemplate "{{externalURL}}" `
        -LinkLabelTemplate "{{repo}} diagnostic #{{issue_number}} - {{title}}"
    $resolverParams = New-ProcessorParamsArg `
        -RootTagPath "resolver_cases" `
        -LinkUrlTemplate "{{externalURL}}" `
        -LinkLabelTemplate "{{repo}} resolver #{{issue_number}} - {{issue_title}}"

    $ids = [ordered]@{
        series = $Series
        slug = $slug
        kb = $KbId
        issues = $null
        files = $null
        diagnostic = $null
        resolver = $null
        last_successful_stage = $null
        uploaded_at = (Get-Date).ToString("s")
    }

    if ($IssuesDatasourceId -gt 0) {
        $ids.issues = Invoke-UploadJsonAdd `
            -Label "${Series} issues" `
            -FilePath $issuesFile `
            -RootKey "issues" `
            -DatasourceId $IssuesDatasourceId `
            -ProcessorParams $issuesParams `
            -DatasourceNameForFallback "DB_STready_${Series}_Issues"
    } elseif ((Test-JsonRootIsEmpty -Path $issuesFile -RootKey "issues") -and ($driverIssueNonEmptyFiles.Count -gt 0)) {
        $firstIssueFile = $driverIssueNonEmptyFiles[0]
        $ids.issues = Invoke-UploadJsonNew `
            -Label "${Series} issues from driver/subrepo $($firstIssueFile.Directory.Parent.Name)" `
            -FilePath $firstIssueFile.FullName `
            -RootKey "issues" `
            -DatasourceName "DB_STready_${Series}_Issues" `
            -ProcessorParams $issuesParams
        $driverIssueFiles = @($driverIssueFiles | Where-Object { $_.FullName -ne $firstIssueFile.FullName })
    } else {
        $ids.issues = Invoke-UploadJsonNew `
            -Label "${Series} issues" `
            -FilePath $issuesFile `
            -RootKey "issues" `
            -DatasourceName "DB_STready_${Series}_Issues" `
            -ProcessorParams $issuesParams `
            -AllowEmpty
    }
    Save-DatasourceIdsSnapshot -Ids $ids -Reason "issues"

    if ($FilesDatasourceId -gt 0) {
        $ids.files = Invoke-UploadJsonAdd `
            -Label "${Series} files" `
            -FilePath $filesFile `
            -RootKey "files" `
            -DatasourceId $FilesDatasourceId `
            -ProcessorParams $filesParams `
            -DatasourceNameForFallback "DB_STready_${Series}_Files"
    } else {
        $ids.files = Invoke-UploadJsonNew `
            -Label "${Series} files" `
            -FilePath $filesFile `
            -RootKey "files" `
            -DatasourceName "DB_STready_${Series}_Files" `
            -ProcessorParams $filesParams
    }
    Save-DatasourceIdsSnapshot -Ids $ids -Reason "files"

    if ($DiagnosticDatasourceId -gt 0) {
        $ids.diagnostic = Invoke-UploadJsonAdd `
            -Label "${Series} diagnostic" `
            -FilePath $diagnosticFile `
            -RootKey "diagnostic_cards" `
            -DatasourceId $DiagnosticDatasourceId `
            -ProcessorParams $diagnosticParams `
            -DatasourceNameForFallback "DB_STready_${Series}_Diagnostic" `
            -AllowEmpty
    } elseif ((Test-JsonRootIsEmpty -Path $diagnosticFile -RootKey "diagnostic_cards") -and ($driverDiagnosticNonEmptyFiles.Count -gt 0)) {
        $firstDiagnosticFile = $driverDiagnosticNonEmptyFiles[0]
        $ids.diagnostic = Invoke-UploadJsonNew `
            -Label "${Series} diagnostic from driver/subrepo $($firstDiagnosticFile.Directory.Parent.Name)" `
            -FilePath $firstDiagnosticFile.FullName `
            -RootKey "diagnostic_cards" `
            -DatasourceName "DB_STready_${Series}_Diagnostic" `
            -ProcessorParams $diagnosticParams
        $driverDiagnosticFiles = @($driverDiagnosticFiles | Where-Object { $_.FullName -ne $firstDiagnosticFile.FullName })
    } else {
        $ids.diagnostic = Invoke-UploadJsonNew `
            -Label "${Series} diagnostic" `
            -FilePath $diagnosticFile `
            -RootKey "diagnostic_cards" `
            -DatasourceName "DB_STready_${Series}_Diagnostic" `
            -ProcessorParams $diagnosticParams `
            -AllowEmpty
    }
    Save-DatasourceIdsSnapshot -Ids $ids -Reason "diagnostic"

    $resolverAllowEmpty = ($driverResolverNonEmptyFiles.Count -eq 0)
    if ($ResolverDatasourceId -gt 0) {
        $ids.resolver = Invoke-UploadJsonAdd `
            -Label "${Series} resolver" `
            -FilePath $resolverFile `
            -RootKey "resolver_cases" `
            -DatasourceId $ResolverDatasourceId `
            -ProcessorParams $resolverParams `
            -DatasourceNameForFallback "DB_STready_${Series}_Resolver" `
            -AllowEmpty
    } elseif ((Test-JsonRootIsEmpty -Path $resolverFile -RootKey "resolver_cases") -and ($driverResolverNonEmptyFiles.Count -gt 0)) {
        $firstResolverFile = $driverResolverNonEmptyFiles[0]
        $ids.resolver = Invoke-UploadJsonNew `
            -Label "${Series} resolver from driver/subrepo $($firstResolverFile.Directory.Parent.Name)" `
            -FilePath $firstResolverFile.FullName `
            -RootKey "resolver_cases" `
            -DatasourceName "DB_STready_${Series}_Resolver" `
            -ProcessorParams $resolverParams
        $driverResolverFiles = @($driverResolverFiles | Where-Object { $_.FullName -ne $firstResolverFile.FullName })
    } else {
        $ids.resolver = Invoke-UploadJsonNew `
            -Label "${Series} resolver" `
            -FilePath $resolverFile `
            -RootKey "resolver_cases" `
            -DatasourceName "DB_STready_${Series}_Resolver" `
            -ProcessorParams $resolverParams `
            -AllowEmpty:$resolverAllowEmpty
    }
            Save-DatasourceIdsSnapshot -Ids $ids -Reason "resolver"

            Write-Host "`nSaved datasource IDs: $idsOutput" -ForegroundColor Green

    Invoke-UploadSubrepoDeliveryAdd -Label "issues" -Files $driverIssueFiles -RootKey "issues" -DatasourceId $ids.issues -ProcessorParams $issuesParams
    Invoke-UploadSubrepoDeliveryAdd -Label "files" -Files $driverFiles -RootKey "files" -DatasourceId $ids.files -ProcessorParams $filesParams
    Invoke-UploadSubrepoDeliveryAdd -Label "diagnostic cards" -Files $driverDiagnosticFiles -RootKey "diagnostic_cards" -DatasourceId $ids.diagnostic -ProcessorParams $diagnosticParams
    Invoke-UploadSubrepoDeliveryAdd -Label "resolver cases" -Files $driverResolverFiles -RootKey "resolver_cases" -DatasourceId $ids.resolver -ProcessorParams $resolverParams

    Write-Host "`n===== $Series upload summary =====" -ForegroundColor Cyan
    $ids | ConvertTo-Json -Depth 4 | Write-Host
}

if ($Mode -in @("Full", "Prepare")) {
    Invoke-PrepareSeries
}

if ($Mode -in @("Full", "Upload")) {
    if ($RunAlfredBeforeUpload) {
        Invoke-PreUploadAlfredFinalize
    }
    Invoke-UploadSeries
}

Write-Host "`nDone for $Series ($Mode)." -ForegroundColor Green