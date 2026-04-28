param(
    [string]$CsvPath = "$(Split-Path -Parent $MyInvocation.MyCommand.Path)\h7_test_suite_excel_ready.csv",
    [string]$XlsxPath = "$(Split-Path -Parent $MyInvocation.MyCommand.Path)\h7_test_suite_excel_ready_real.xlsx",
    [string]$XlsPath = "$(Split-Path -Parent $MyInvocation.MyCommand.Path)\h7_test_suite_excel_ready_real.xls"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $CsvPath)) {
    throw "CSV not found: $CsvPath"
}

$rows = Import-Csv -Path $CsvPath -Delimiter ';'

if ($rows.Count -eq 0) {
    throw "CSV has no data rows: $CsvPath"
}

foreach ($outPath in @($XlsxPath, $XlsPath)) {
    $parent = Split-Path -Parent $outPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    if (Test-Path -LiteralPath $outPath) {
        try {
            Remove-Item -LiteralPath $outPath -Force -ErrorAction Stop
        }
        catch {
            throw "Cannot overwrite output file: $outPath. Close Excel or any app using this file and retry."
        }
    }
}

$excel = $null
$workbook = $null
$worksheet = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false

    $workbook = $excel.Workbooks.Add()
    $worksheet = $workbook.Worksheets.Item(1)
    $worksheet.Name = 'test_dataset'

    $headers = @('Question', 'Answer', 'Tags')
    for ($col = 0; $col -lt $headers.Count; $col++) {
        $worksheet.Cells.Item(1, $col + 1) = $headers[$col]
    }

    $rowIndex = 2
    foreach ($row in $rows) {
        $worksheet.Cells.Item($rowIndex, 1) = [string]$row.Question
        $worksheet.Cells.Item($rowIndex, 2) = [string]$row.Answer
        $worksheet.Cells.Item($rowIndex, 3) = [string]$row.Tags
        $rowIndex++
    }

    $worksheet.Columns.Item('A:C').EntireColumn.AutoFit() | Out-Null

    # 56 = xlExcel8 (.xls, Excel 97-2003)
    $workbook.SaveAs($XlsPath, 56)
    Write-Host "Created: $XlsPath"

    # 51 = xlOpenXMLWorkbook (.xlsx)
    try {
        $workbook.SaveAs($XlsxPath, 51)
        Write-Host "Created: $XlsxPath"
    }
    catch {
        Write-Warning "Could not create xlsx copy: $XlsxPath ($($_.Exception.Message))"
    }
}
finally {
    if ($workbook -ne $null) {
        $workbook.Close($false) | Out-Null
    }
    if ($excel -ne $null) {
        $excel.Quit() | Out-Null
    }

    if ($worksheet -ne $null) {
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet)
    }
    if ($workbook -ne $null) {
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook)
    }
    if ($excel -ne $null) {
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    }

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
