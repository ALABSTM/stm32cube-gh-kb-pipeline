<#
.SYNOPSIS
    Upload all driver sub-repo artifacts (issues, files, diagnostic_cards, resolver_cases)
    to the correct series datasources in KB #793.

.DESCRIPTION
    Scans by_series/<serie>/drivers/<driver>/ for JSON artifacts and uploads them
    using --operation add to the datasource matching the series AND artifact type.
    
    Each artifact type (issues, files, diag_cards, resolver_cases) goes to its own datasource.
#>

param(
    [string]$RemoteUser = "abir.gharbi@st.com",
    [int]$KB = 793,
    [int]$JsonSplitSize = 1000
)

$ErrorActionPreference = "Continue"
Set-Location "c:\Users\gharbiab\OneDrive - STMicroelectronics\Desktop\PFE_Chatbot_STM32Cube"

# === Datasource IDs per series per artifact type ===
# Format: series -> { artifact_type -> datasource_id }
$datasourceMap = @{
    "stm32cubec0" = @{
        "issues_json"           = 29193
        "files_json"            = 29192
        "diagnostic_cards_json" = 29212
        "resolver_cases_json"   = 0  # empty - skip
    }
    "stm32cubef0" = @{
        "issues_json"           = 29195
        "files_json"            = 29196
        "diagnostic_cards_json" = 29213
        "resolver_cases_json"   = 0  # empty
    }
    "stm32cubef1" = @{
        "issues_json"           = 29197
        "files_json"            = 29198
        "diagnostic_cards_json" = 29214
        "resolver_cases_json"   = 29211
    }
    "stm32cubef2" = @{
        "issues_json"           = 29199
        "files_json"            = 29200
        "diagnostic_cards_json" = 29215
        "resolver_cases_json"   = 0  # empty
    }
    "stm32cubef3" = @{
        "issues_json"           = 29282
        "files_json"            = 29283
        "diagnostic_cards_json" = 29284
        "resolver_cases_json"   = 0  # empty
    }
    "stm32cubef7" = @{
        "issues_json"           = 29276
        "files_json"            = 29277
        "diagnostic_cards_json" = 29278
        "resolver_cases_json"   = 29279
    }
    "stm32cubeg0" = @{
        "issues_json"           = 29273
        "files_json"            = 29274
        "diagnostic_cards_json" = 29275
        "resolver_cases_json"   = 0  # empty
    }
    "stm32cubeh7rs" = @{
        "issues_json"           = 29270
        "files_json"            = 29271
        "diagnostic_cards_json" = 29272
        "resolver_cases_json"   = 0  # empty
    }
}

# === Processor params (base64 encoded) ===
$paramsIssues = '{"label": "{{repo}} issue #{{issue_number}} - {{issue_title}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/issues/{{issue_number}}", "rootTagPath": "issues"}'
$b64I = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($paramsIssues))

$paramsFiles = '{"label": "{{repo}} {{file_type}} - {{path}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/{{root_dir}}/{{root_ref}}/{{path_url}}", "rootTagPath": "files"}'
$b64F = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($paramsFiles))

$paramsDiag = '{"label": "{{label}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/issues/{{evidence_refs[0].id}}"}'
$b64D = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($paramsDiag))

$paramsResolver = '{"label": "{{label}}", "externalURL": "https://github.com/STMicroelectronics/{{repo}}/issues/{{issue_number}}", "rootTagPath": "resolver_cases"}'
$b64R = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($paramsResolver))

# Map artifact type to processor params
$artifactParams = @{
    "issues_json"           = $b64I
    "files_json"            = $b64F
    "diagnostic_cards_json" = $b64D
    "resolver_cases_json"   = $b64R
}

$bySeriesRoot = "datasets\07_delivery\st_ready\by_series"

$totalUploaded = 0
$totalSkipped = 0
$totalFailed = 0
$uploadDelaySec = 5      # seconds between uploads to avoid API rate limit
$retryCount = 2          # number of retries on failure
$retryDelaySec = 30      # seconds to wait before retry (API cooldown)

foreach ($series in $datasourceMap.Keys) {
    $seriesMap = $datasourceMap[$series]
    $driversDir = Join-Path $bySeriesRoot "$series\drivers"
    
    if (-not (Test-Path $driversDir)) {
        Write-Host "[SKIP] $series - no drivers/ folder" -ForegroundColor Yellow
        continue
    }

    $drivers = Get-ChildItem -Path $driversDir -Directory
    Write-Host "`n========== $series ==========" -ForegroundColor Cyan
    
    foreach ($driver in $drivers) {
        foreach ($artifactType in $artifactParams.Keys) {
            $dsId = $seriesMap[$artifactType]
            if ($dsId -eq 0) {
                continue  # No datasource for this artifact type
            }

            $artifactDir = Join-Path $driver.FullName $artifactType
            if (-not (Test-Path $artifactDir)) { continue }
            
            $jsonFiles = Get-ChildItem -Path $artifactDir -Filter "st_ready_*.json" | Where-Object { $_.Name -notmatch "summary" }
            
            foreach ($jsonFile in $jsonFiles) {
                # Check if file is empty JSON
                $content = Get-Content $jsonFile.FullName -Raw -ErrorAction SilentlyContinue
                if ($content -match '^\s*\[\s*\]\s*$' -or $content -match '^\s*\{\s*"[^"]+"\s*:\s*\[\s*\]\s*\}\s*$') {
                    Write-Host "  [EMPTY] $($driver.Name)/$artifactType/$($jsonFile.Name)" -ForegroundColor DarkGray
                    $totalSkipped++
                    continue
                }

                $relativePath = $jsonFile.FullName.Replace((Get-Location).Path + "\", "")
                $b64Param = $artifactParams[$artifactType]
                
                Write-Host "  [UPLOAD] $($driver.Name)/$artifactType -> DS#$dsId | $($jsonFile.Name)" -ForegroundColor Green
                
                $success = $false
                for ($attempt = 1; $attempt -le ($retryCount + 1); $attempt++) {
                    python pipeline_Automation/upload/Add_Data_Source_Files.py `
                        --kb $KB --operation add --datasource-id $dsId `
                        --remote-user $RemoteUser --processor JSON `
                        --processor-params "base64:$b64Param" --json-split-size $JsonSplitSize `
                        --files $relativePath
                    
                    if ($LASTEXITCODE -eq 0) {
                        $success = $true
                        break
                    }
                    
                    if ($attempt -le $retryCount) {
                        Write-Host "  [RETRY] Attempt $attempt failed, waiting ${retryDelaySec}s before retry..." -ForegroundColor Yellow
                        Start-Sleep -Seconds $retryDelaySec
                    }
                }
                
                if ($success) {
                    $totalUploaded++
                } else {
                    $totalFailed++
                    Write-Host "  [FAIL] Upload failed for $($jsonFile.Name) after $($retryCount + 1) attempts" -ForegroundColor Red
                }
                
                # Throttle: pause between uploads to respect API rate limits
                Start-Sleep -Seconds $uploadDelaySec
            }
        }
    }
}

Write-Host "`n====== SUMMARY ======" -ForegroundColor Cyan
Write-Host "Uploaded: $totalUploaded" -ForegroundColor Green
Write-Host "Skipped (empty): $totalSkipped" -ForegroundColor Yellow
Write-Host "Failed: $totalFailed" -ForegroundColor Red
