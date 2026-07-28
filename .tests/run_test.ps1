#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run OCR test on specified image file

.DESCRIPTION
    Tests UnlimitedOCR on a given image. Activates venv, runs test,
    and outputs results to both console and log file.

.PARAMETER ImageFile
    Image file to test (jpg, png, etc.)
    Default: Test_File.jpg

.EXAMPLE
    .\run_test.ps1 Test_File.jpg
    .\run_test.ps1 test_image.png
    .\run_test.ps1  # uses default Test_File.jpg
#>

param(
    [string]$ImageFile = "Test_File.jpg"
)

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Testing UnlimitedOCR with $ImageFile" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Activate venv
$venvActivate = "..\venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Host "ERROR: Virtual environment not found at $venvActivate" -ForegroundColor Red
    exit 1
}

# Run test
python test_unlimited_ocr.py $ImageFile

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Test completed successfully" -ForegroundColor Green
    Write-Host "Log file: $ImageFile.log" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Test failed with error code $LASTEXITCODE" -ForegroundColor Red
}

Write-Host ""
