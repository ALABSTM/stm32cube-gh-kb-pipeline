$targetScript = Join-Path $PSScriptRoot "pipeline_Automation\Upload_STReady_New_Batch.ps1"

if (-not (Test-Path -LiteralPath $targetScript)) {
    throw "Target script not found: $targetScript"
}

& $targetScript @args
exit $LASTEXITCODE
