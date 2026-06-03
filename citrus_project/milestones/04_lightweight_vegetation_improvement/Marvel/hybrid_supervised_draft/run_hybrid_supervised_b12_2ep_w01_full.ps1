$ErrorActionPreference = "Stop"

$RepoRoot = "C:\Proj\lite-Mono"
$PythonRunner = "C:\Proj\miniforge3\condabin\mamba.bat"
$RunName = "hybrid_supervised_b12_2ep_logl1_median_w01_full"
$LogDir = "citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/runs"
$RunDir = Join-Path $RepoRoot (Join-Path $LogDir $RunName)
$ConsoleLog = Join-Path $RunDir "console.log"
$TrainScript = "citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/hybrid_supervised_draft/train_hybrid_supervised.py"

Set-Location $RepoRoot
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

& $PythonRunner run -n lite-mono python $TrainScript `
  --dataset citrus `
  --split citrus_prepared `
  --data_path citrus_project/dataset_workspace `
  --model lite-mono `
  --model_name $RunName `
  --log_dir $LogDir `
  --mypretrain weights/lite-mono/lite-mono-pretrain.pth `
  --weights_init pretrained `
  --batch_size 12 `
  --num_epochs 2 `
  --lr 0.0001 0.000005 31 0.0001 0.00001 31 `
  --weight_decay 0.01 `
  --drop_path 0.2 `
  --height 192 `
  --width 640 `
  --num_workers 0 `
  --log_frequency 100 `
  --save_frequency 1 `
  --seed 0 `
  --lidar_loss_weight 0.1 `
  --lidar_loss_type log_l1 `
  --lidar_scale_align median `
  --lidar_loss_scales 0 `
  --lidar_loss_min_valid_pixels 500 2>&1 | Tee-Object -FilePath $ConsoleLog