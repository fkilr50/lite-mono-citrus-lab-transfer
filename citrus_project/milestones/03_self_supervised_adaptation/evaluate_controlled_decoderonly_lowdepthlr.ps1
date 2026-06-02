param(
    [string]$RunName = "citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps",
    [string]$CheckpointName = "weights_0",
    [int]$MaxSamples = 100,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$PythonExe = "D:/Conda_Envs/lite-mono/python.exe"
$RunDir = Join-Path $RepoRoot "citrus_project/milestones/03_self_supervised_adaptation/runs/$RunName"
$WeightsFolder = Join-Path $RunDir "models/$CheckpointName"
$OutputDir = Join-Path $RunDir "eval_val${MaxSamples}_$CheckpointName"
$EvalLog = Join-Path $OutputDir "eval_terminal.log"

if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

$EvalArgs = @(
    "-u",
    "citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py",
    "--split", "val",
    "--max_samples", "$MaxSamples",
    "--run_model",
    "--summary_only",
    "--progress_interval", "25",
    "--weights_folder", "$WeightsFolder",
    "--output_dir", "$OutputDir"
)

Write-Host "Repo root:      $RepoRoot"
Write-Host "Run name:       $RunName"
Write-Host "Checkpoint:     $CheckpointName"
Write-Host "Weights folder: $WeightsFolder"
Write-Host "Output dir:     $OutputDir"
Write-Host ""
Write-Host "Command:"
Write-Host "$PythonExe $($EvalArgs -join ' ')"
Write-Host ""

if ($DryRun) {
    Write-Host "Dry run only; evaluation was not started."
    exit 0
}

if (-not (Test-Path $WeightsFolder)) {
    throw "Checkpoint folder not found: $WeightsFolder"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Push-Location $RepoRoot
try {
    & $PythonExe @EvalArgs 2>&1 | Tee-Object -FilePath $EvalLog
    if ($LASTEXITCODE -ne 0) {
        throw "Evaluation failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Evaluation command finished."
Write-Host "Saved summary/per-sample files under:"
Write-Host $OutputDir
