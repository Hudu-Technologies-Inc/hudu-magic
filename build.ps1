[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$Test,
    [switch]$Build = $true,
    [ValidateSet("none","testpypi","pypi")]
    [string]$Publish = "none"
)


function Get-PythonCommand {
    $candidates = @(
        (Get-Command py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
        (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
        "$env:LocalAppData\Programs\Python\Python314\python.exe",
        "$env:ProgramFiles\Python314\python.exe",
        "$env:ProgramFiles\Python\Python314\python.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    $python = $candidates | Select-Object -First 1
    if (-not $python) {
        throw "Could not find a working Python executable."
    }
    return $python
}

$PythonCmd = Get-PythonCommand
& $PythonCmd --version

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Script
    )
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Script
}

if ($Clean) {
    Invoke-Step "Cleaning build artifacts" {
        Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
        Get-ChildItem -Directory -Filter *.egg-info | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Invoke-Step "Ensuring build tools" {
    & $PythonCmd -m pip install --upgrade pip build twine
}

if ($Test) {
    Invoke-Step "Running tests" {
        & $PythonCmd -m pytest
    }
}

if ($Build) {
    Invoke-Step "Building sdist and wheel" {
        & $PythonCmd -m build
    }

    Invoke-Step "Checking distributions" {
        & $PythonCmd -m twine check dist/*
    }
}

switch ($Publish) {
    "testpypi" {
        Invoke-Step "Uploading to TestPyPI" {
            & $PythonCmd -m twine upload --repository testpypi dist/*
        }
    }
    "pypi" {
        Invoke-Step "Uploading to PyPI" {
            & $PythonCmd -m twine upload dist/*
        }
    }
}