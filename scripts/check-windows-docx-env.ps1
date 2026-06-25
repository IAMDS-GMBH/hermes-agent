param(
    [string]$InstallDir = "$env:LOCALAPPDATA\hermes\hermes-agent",
    [switch]$Fix
)

$ErrorActionPreference = "Stop"

$venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"
$installerScript = Join-Path $InstallDir "scripts\install.ps1"

if (-not (Test-Path $venvPython)) {
    throw "Venv python not found: $venvPython"
}

Write-Host "== Hermes venv check =="
& $venvPython -c "import docx,sys; print('venv ok', docx.__version__, sys.executable)"

Write-Host ""
Write-Host "== Global python check =="
try {
    & python -c "import docx,sys; print('global ok', docx.__version__, sys.executable)"
} catch {
    Write-Warning "Global python check failed: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "== python3 alias check =="
try {
    & python3 -c "import sys; print(sys.executable)"
} catch {
    Write-Warning "python3 check failed (often Windows Store alias): $($_.Exception.Message)"
}

Write-Host ""
Write-Host "== Installer capability check =="
if (Test-Path $installerScript) {
    Select-String -Path $installerScript -Pattern "Ensure-OfficeDocumentDependencies" | ForEach-Object { $_.Line }
} else {
    Write-Warning "Installer script not found: $installerScript"
}

if ($Fix) {
    Write-Host ""
    Write-Host "== Repair: install python-docx into Hermes venv =="
    & $venvPython -m pip install python-docx
}
