#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run multiple OCR tests

.DESCRIPTION
    Runs OCR tests on specified images in sequence.
    Activates venv once and runs all tests.
#>

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Running UnlimitedOCR Test Suite" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Activate venv once
$venvActivate = "..\venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Host "ERROR: Virtual environment not found at $venvActivate" -ForegroundColor Red
    exit 1
}

# Array of test images
$testImages = @(
    "Test_File.jpg",
    "Test_File.pdf"
)

$passed = 0
$failed = 0

# Run each test
foreach ($image in $testImages) {
    Write-Host ""
    Write-Host "Running: $image" -ForegroundColor Yellow
    Write-Host "-" * 70

    python test_unlimited_ocr.py $image

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $image - PASSED" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "❌ $image - FAILED (exit code: $LASTEXITCODE)" -ForegroundColor Red
        $failed++
    }
}

# Summary
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Test Results: $passed passed, $failed failed" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed" -ForegroundColor Red
}

Write-Host ""
