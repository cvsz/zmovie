param(
    [string]$StatePath = "$HOME\storage_state.json",
    [string]$UserDataDir = "$env:LOCALAPPDATA\Google\Chrome\User Data"
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "[zMovie Chrome capture] $Message"
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $RepoRoot "requirements.txt"

Write-Step "This reuses the Chrome profile that is already open."
Write-Step "In that Chrome, open chrome://inspect/#remote-debugging and enable remote debugging first."
Write-Step "Keep the Chrome window open and approve Chrome's connection dialog when prompted."

if (-not (Test-Path $Python)) {
    Write-Step "creating local Python virtual environment"
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -m venv (Join-Path $RepoRoot ".venv")
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv (Join-Path $RepoRoot ".venv")
    } else {
        throw "Python was not found. Install Python 3 and rerun this script."
    }
}

Write-Step "installing/updating zMovie Python dependencies"
& $Python -m pip install -r $Requirements
if ($LASTEXITCODE -ne 0) { throw "dependency installation failed" }

Write-Step "capturing Bilibili session from the existing Chrome context"
Push-Location $RepoRoot
try {
    & $Python -m zmovie_platform.publishers.bilibili_hardened capture-chrome `
        --state $StatePath `
        --user-data-dir $UserDataDir
    if ($LASTEXITCODE -ne 0) { throw "Chrome session capture failed" }
} finally {
    Pop-Location
}

if (-not (Test-Path $StatePath)) {
    throw "capture command returned without creating $StatePath"
}

Write-Step "PASS: saved authenticated browser state to $StatePath"
Write-Step "Treat this file as a credential. Do not commit, upload, or share it."
