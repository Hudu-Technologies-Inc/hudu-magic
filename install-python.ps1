[CmdletBinding()]
param(
    [switch]$ForceRecreateVenv
)

$ErrorActionPreference = "Stop"

function Get-PythonCommand {
    $candidates = @()

    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { $candidates += $pyCmd.Source }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { $candidates += $pythonCmd.Source }

    $candidates += @(
        "$env:LocalAppData\Programs\Python\Python314\python.exe",
        "$env:ProgramFiles\Python314\python.exe",
        "$env:ProgramFiles\Python\Python314\python.exe"
    )

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Ensure-Python {
    $python = Get-PythonCommand
    if ($python) {
        return $python
    }

    Write-Host "Python not found. Installing Python 3.14 with winget..." -ForegroundColor Yellow
    winget install -e --id Python.Python.3.14

    $python = Get-PythonCommand
    if (-not $python) {
        $python = "$env:LocalAppData\Programs\Python\Python314\python.exe"
    }

    if (-not (Test-Path $python)) {
        throw "Python installation appears to have succeeded, but python.exe could not be found."
    }

    return $python
}

function Invoke-Step {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Script
    )
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Script
}

$PythonCmd = Ensure-Python
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if ($ForceRecreateVenv -and (Test-Path (Join-Path $PSScriptRoot ".venv"))) {
    Invoke-Step "Removing existing virtual environment" {
        Remove-Item -Recurse -Force (Join-Path $PSScriptRoot ".venv")
    }
}

if (-not (Test-Path $VenvPython)) {
    Invoke-Step "Creating virtual environment" {
        & $PythonCmd -m venv (Join-Path $PSScriptRoot ".venv")
    }
}

$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Invoke-Step "Upgrading pip" {
    & $VenvPython -m pip install --upgrade pip --no-cache-dir
}

Invoke-Step "Installing package in editable mode" {
    & $VenvPython -m pip install -e .
}

if (Test-Path (Join-Path $PSScriptRoot "requirements-dev.txt")) {
    Invoke-Step "Installing dev requirements" {
        & $VenvPython -m pip install -r (Join-Path $PSScriptRoot "requirements-dev.txt")
    }
}

Invoke-Step "Smoke testing import" {
    & $VenvPython -c "import hudu_magic; print('hudu_magic import OK')"
}

Write-Host ""
Write-Host "Done. Use this Python for the project:" -ForegroundColor Green
Write-Host "  $VenvPython"
Write-Host ""
Write-Host "Activate with:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1"