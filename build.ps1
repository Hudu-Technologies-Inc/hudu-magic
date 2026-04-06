[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$Test,
    [switch]$Install,
    [ValidateSet("none","testpypi","pypi")]
    [string]$Publish = "none"
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Script
    )
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Script
}

$PythonCmd = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonCmd)) {
    throw "Virtual environment not found. Create one (py -m venv .venv) or run .\install-python.ps1 — see GETPYTHON.md"
}

if ($Clean) {
    Invoke-Step "Cleaning build artifacts" {
        Remove-Item -Recurse -Force (Join-Path $PSScriptRoot "dist") -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force (Join-Path $PSScriptRoot "build") -ErrorAction SilentlyContinue
        Get-ChildItem -Path $PSScriptRoot -Directory -Filter "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-Step "Ensuring build tools" {
    & $PythonCmd -m pip install --upgrade pip build twine
}

if ($Install) {
    Invoke-Step "Installing package in editable mode" {
        & $PythonCmd -m pip install -e .
    }
}

if ($Test) {
    Invoke-Step "Running tests" {
        & $PythonCmd -m pytest
    }
}

Invoke-Step "Building sdist and wheel" {
    & $PythonCmd -m build
}

Invoke-Step "Checking distributions" {
    & $PythonCmd -m twine check (Join-Path $PSScriptRoot "dist\*")
}

switch ($Publish) {
    "testpypi" {
        Invoke-Step "Uploading to TestPyPI" {
            & $PythonCmd -m twine upload --repository testpypi (Join-Path $PSScriptRoot "dist\*")
        }
    }
    "pypi" {
        Invoke-Step "Uploading to PyPI" {
            & $PythonCmd -m twine upload (Join-Path $PSScriptRoot "dist\*")
        }
    }
}