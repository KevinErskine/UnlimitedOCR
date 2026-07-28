#!/usr/bin/env pwsh

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
    Write-Host "ERROR: Virtual environment not found" -ForegroundColor Red
    exit 1
}

# Test images
$testImages = "Test_File.jpg", "Test_File.pdf"
$passed = 0
$failed = 0

# Run each test
foreach ($image in $testImages) {
    Write-Host ""
    Write-Host "Running: $image" -ForegroundColor Yellow
    Write-Host "-" * 70
    python test_unlimited_ocr.py $image
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PASSED: $image" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "FAILED: $image" -ForegroundColor Red
        $failed++
    }
}

# Summary
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Results: $passed passed, $failed failed" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
