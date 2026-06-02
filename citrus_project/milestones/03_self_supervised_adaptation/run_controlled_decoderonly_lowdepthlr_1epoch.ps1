param(
    [int]$MaxTrainSteps = 1000,
    [int]$SaveStepFrequency = 250,
    [string]$RunName = "",
    [switch]$AllowExisting,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$PythonExe = "D:/Conda_Envs/lite-mono/python.exe"
$LogDirRel = "citrus_project/milestones/03_self_supervised_adaptation/runs"

if ($RunName -eq "") {
    $RunName = "citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_${MaxTrainSteps}steps"
}

$RunDir = Join-Path $RepoRoot "$LogDirRel/$RunName"
$TrainLog = Join-Path $RunDir "train_terminal.log"

if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

if ((Test-Path $RunDir) -and -not $AllowExisting -and -not $DryRun) {
    throw "Run folder already exists: $RunDir. Use -AllowExisting only if you intentionally want to append/reuse this folder."
}

$TrainArgs = @(
    "-u",
    "train.py",
    "--dataset", "citrus",
    "--load_weights_folder", "weights/lite-mono",
    "--models_to_load", "encoder", "depth",
    "--weights_init", "pretrained",
    "--batch_size", "4",
    "--num_workers", "0",
    "--num_epochs", "1",
    "--seed", "0",
    "--max_train_steps", "$MaxTrainSteps",
    "--freeze_depth_steps", "25",
    "--freeze_depth_encoder",
    "--save_step_frequency", "$SaveStepFrequency",
    "--save_frequency", "1",
    "--log_frequency", "50",
    "--drop_path", "0",
    "--lr", "0.00001", "0.0000005", "31", "0.0001", "0.00001", "31",
    "--log_dir", $LogDirRel,
    "--model_name", $RunName
)

Write-Host "Repo root: $RepoRoot"
Write-Host "Run name:  $RunName"
Write-Host "Run dir:   $RunDir"
Write-Host "Log file:  $TrainLog"
Write-Host ""
Write-Host "Recipe meaning:"
Write-Host "- Start from original Lite-Mono encoder/depth weights."
Write-Host "- Train pose normally, but freeze depth updates for the first 25 steps."
Write-Host "- Keep the depth encoder frozen; only the depth decoder can adapt."
Write-Host "- Use a low depth learning rate and save step checkpoints."
Write-Host ""

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv
}

Write-Host ""
Write-Host "Command:"
Write-Host "$PythonExe $($TrainArgs -join ' ')"
Write-Host ""

if ($DryRun) {
    Write-Host "Dry run only; training was not started."
    exit 0
}

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

Push-Location $RepoRoot
try {
    & $PythonExe @TrainArgs 2>&1 | Tee-Object -FilePath $TrainLog
    if ($LASTEXITCODE -ne 0) {
        throw "Training failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Training command finished."
Write-Host "Expected checkpoints are under:"
Write-Host (Join-Path $RunDir "models")
