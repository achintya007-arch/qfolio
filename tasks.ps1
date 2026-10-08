<#
.SYNOPSIS
    Windows equivalent of the Makefile (no `make` on Windows).
.EXAMPLE
    .\tasks.ps1 lint
    .\tasks.ps1 test
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "lint", "format", "test", "test-all", "reproduce", "notebook",
        "report", "app", "checkpoint", "clean")]
    [string]$Target = "test"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:PYTHONHASHSEED = "0"
$Py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
# Put the venv first on PATH so tools called from bash scripts (jupyter) resolve to it.
$env:PATH = (Join-Path $PSScriptRoot ".venv\Scripts") + ";" + $env:PATH

# Run a command and stop on a non-zero exit code (PowerShell does not do this for native exes).
function Invoke-Step {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

switch ($Target) {
    "setup" {
        if (-not (Test-Path $Py)) { Invoke-Step "python" @("-m", "venv", ".venv") }
        Invoke-Step $Py @("-m", "pip", "install", "-r", "requirements-dev.txt")
        Invoke-Step $Py @("-m", "pre_commit", "install")
    }
    "lint" {
        Invoke-Step $Py @("-m", "ruff", "check", ".")
        Invoke-Step $Py @("-m", "ruff", "format", "--check", ".")
    }
    "format" {
        Invoke-Step $Py @("-m", "ruff", "format", ".")
        Invoke-Step $Py @("-m", "ruff", "check", "--fix", ".")
    }
    "test" { Invoke-Step $Py @("-m", "pytest") }
    "test-all" { Invoke-Step $Py @("-m", "pytest", "-m", "", "--cov", "--cov-report=term-missing") }
    "reproduce" {
        # Full benchmark (~15 min); set $env:QFOLIO_FAST = "1" first for a CI-sized run.
        Invoke-Step $Py @("scripts/run_benchmark.py")
        # P4 (noise study) is optional until scripts/run_noisy.py exists.
        if (Test-Path "scripts/run_noisy.py") { Invoke-Step $Py @("scripts/run_noisy.py") }
        Invoke-Step $Py @("scripts/make_figures.py")
        Invoke-Step $Py @("scripts/fill_readme.py")
    }
    "notebook" {
        Invoke-Step $Py @("-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
            "--inplace", "notebooks/qfolio.ipynb")
    }
    "report" { Invoke-Step "bash" @("scripts/build_report.sh") }
    "app" { Invoke-Step $Py @("-m", "streamlit", "run", "app/streamlit_app.py") }
    "checkpoint" { Invoke-Step $Py @("-m", "qportfolio.demo") }
    "clean" {
        foreach ($d in @("site", ".pytest_cache", ".ruff_cache")) {
            if (Test-Path $d) { Remove-Item -Recurse -Force $d }
        }
        Get-ChildItem -Recurse -Directory -Filter "__pycache__" |
            Where-Object { $_.FullName -notlike "*\.venv\*" } |
            Remove-Item -Recurse -Force
    }
}
