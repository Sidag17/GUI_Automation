$ErrorActionPreference = "Stop"

# ============================================================
# Project root
# ============================================================

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================"
Write-Host "Simplicity Studio GUI Automation"
Write-Host "============================================"
Write-Host "Project Root: $ProjectRoot"


# ============================================================
# Add src folder to Python module path
# ============================================================

$SrcPath = Join-Path $ProjectRoot "src"

if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$SrcPath;$env:PYTHONPATH"
}
else {
    $env:PYTHONPATH = $SrcPath
}

Write-Host "Python Path: $SrcPath"


# ============================================================
# Create reports directory
# ============================================================

$ReportsPath = Join-Path $ProjectRoot "reports"

if (-not (Test-Path $ReportsPath)) {

    New-Item `
        -ItemType Directory `
        -Path $ReportsPath `
        -Force | Out-Null
}


# ============================================================
# Verify Python
# ============================================================

Write-Host ""
Write-Host "Python executable:"

python -c "import sys; print(sys.executable)"


# ============================================================
# Verify studio_automation package
# ============================================================

Write-Host ""
Write-Host "Checking studio_automation package..."

python -c "import studio_automation; print('Package found:', studio_automation.__file__)"

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "ERROR: studio_automation package could not be imported."

    exit $LASTEXITCODE
}


# ============================================================
# Run pytest
# ============================================================

Write-Host ""
Write-Host "Starting pytest..."
Write-Host ""

python -m pytest

$TestExitCode = $LASTEXITCODE


# ============================================================
# Final result
# ============================================================

Write-Host ""
Write-Host "============================================"

if ($TestExitCode -eq 0) {

    Write-Host "TEST EXECUTION COMPLETED SUCCESSFULLY"

}
else {

    Write-Host "TEST EXECUTION FAILED"
    Write-Host "Exit code: $TestExitCode"

}

Write-Host "============================================"

exit $TestExitCode