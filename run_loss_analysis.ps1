#!/usr/bin/env powershell
# Run Milestone 3 loss analysis

$ErrorActionPreference = "Stop"

$RepoRoot = "c:\Users\user\Documents\brgkuliah\sem6\ai apps\plantdepths\Lite-Mono-Main"
$PythonPath = "D:/Conda_Envs/lite-mono/python.exe"
$ScriptPath = Join-Path $RepoRoot "citrus_project/milestones/03_self_supervised_adaptation/analyze_loss_progression.py"

Write-Host "Starting Milestone 3 Loss Analysis..."
Write-Host "Repo root: $RepoRoot"
Write-Host "Script: $ScriptPath"
Write-Host ""

Push-Location $RepoRoot
try {
    & cmd /c "$PythonPath $ScriptPath"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Script exited with code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Analysis complete. Check citrus_project/milestones/03_self_supervised_adaptation/loss_analysis_output/"
