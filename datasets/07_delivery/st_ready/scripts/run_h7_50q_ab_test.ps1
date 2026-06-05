param(
    [string]$SuiteCsv = "datasets/07_delivery/st_ready/h7_test_suite_excel_ready.csv",
    [string]$OutDir = "datasets/06_eval_outputs",
    [double]$Temperature = 0.3,
    [int]$MaxRetries = 3,
    [int]$SleepMs = 250
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# In newer PowerShell versions, stderr from native commands can become terminating
# errors when ErrorActionPreference is Stop. Keep stderr as output so batch can continue.
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

# Ensure commands run from repository root, regardless of where script is launched.
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "../../..")
Set-Location $repoRoot

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

function Run-Batch {
    param(
        [string]$ModeName
    )

    $rows = Import-Csv -Path $SuiteCsv -Delimiter ';'
    if (-not $rows -or $rows.Count -eq 0) {
        throw "No rows found in CSV: $SuiteCsv"
    }

    $outFile = Join-Path $OutDir ("run50_" + $ModeName + "_" + $stamp + ".csv")
    $all = @()

    $i = 0
    foreach ($r in $rows) {
        $i++
        Write-Host ("[" + $ModeName + "] " + $i + "/" + $rows.Count + " -> " + $r.Question)

        try {
            $raw = python pipeline_Automation/Chat_With_Persona_KB.py -q "$($r.Question)" --temperature $Temperature --max-retries $MaxRetries 2>&1 | Out-String
        } catch {
            $raw = "[RUNNER_EXCEPTION] " + $_.Exception.Message
        }

        $exitCode = $LASTEXITCODE
        $m = [regex]::Match($raw, "Assistant:\s*(?<ans>[\s\S]*)$")
        $ans = if ($m.Success) { $m.Groups["ans"].Value.Trim() } else { $raw.Trim() }
        if ($exitCode -ne 0 -and -not $ans) {
            $ans = "[PYTHON_EXIT_" + $exitCode + "]"
        }

        $all += [pscustomobject]@{
            QID = ("Q" + $i.ToString("00"))
            Question = $r.Question
            GoldAnswer = $r.Answer
            Tags = $r.Tags
            AssistantAnswer = $ans
            Mode = $ModeName
            ExitCode = $exitCode
        }

        Start-Sleep -Milliseconds $SleepMs
    }

    $all | Export-Csv -Path $outFile -Delimiter ';' -NoTypeInformation -Encoding UTF8
    Write-Host ("Saved -> " + $outFile)
    return $outFile
}

$classicFile = Run-Batch -ModeName "classic"

Write-Host "Classic file: $classicFile"
