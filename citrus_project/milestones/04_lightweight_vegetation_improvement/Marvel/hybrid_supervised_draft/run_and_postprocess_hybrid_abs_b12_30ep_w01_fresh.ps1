$ErrorActionPreference = "Stop"

$RepoRoot = "C:\Proj\lite-Mono"
$Python = "C:\Proj\miniforge3\envs\lite-mono\python.exe"
$RunName = "hybrid_supervised_b12_30ep_logl1_abs_w01_fresh_sched"
$LogDir = "citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/runs"
$RunDir = Join-Path $RepoRoot (Join-Path $LogDir $RunName)
$TrainLog = Join-Path $RunDir "console.log"
$PostprocessLog = Join-Path $RunDir "postprocess.log"
$TrainScript = "citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/hybrid_supervised_draft/train_hybrid_supervised.py"
$WeightsFolder = "$LogDir/$RunName/models/weights_29"
$ResultsDir = "citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/results/$RunName"
$VisualDir = "$ResultsDir/visuals"

Set-Location $RepoRoot
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
Start-Transcript -Path (Join-Path $RunDir "runner_transcript.log") -Append

& $Python -u $TrainScript `
  --dataset citrus `
  --split citrus_prepared `
  --data_path citrus_project/dataset_workspace `
  --model lite-mono `
  --model_name $RunName `
  --log_dir $LogDir `
  --mypretrain weights/lite-mono/lite-mono-pretrain.pth `
  --weights_init pretrained `
  --batch_size 12 `
  --num_epochs 30 `
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
  --lidar_scale_align none `
  --lidar_loss_scales 0 `
  --lidar_loss_min_valid_pixels 500 2>&1 | Tee-Object -FilePath $TrainLog

if (-not (Test-Path $WeightsFolder)) {
  throw "Expected final checkpoint was not found: $WeightsFolder"
}

& $Python citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/plot_training_losses.py `
  --run_dir "$LogDir/$RunName" `
  --output_dir "$ResultsDir/loss_plots" 2>&1 | Tee-Object -FilePath $PostprocessLog

& $Python citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py `
  --split val `
  --max_samples 0 `
  --run_model `
  --summary_only `
  --progress_interval 50 `
  --weights_folder $WeightsFolder `
  --output_dir $ResultsDir 2>&1 | Tee-Object -FilePath $PostprocessLog -Append

& $Python citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py `
  --split test `
  --max_samples 0 `
  --run_model `
  --summary_only `
  --progress_interval 50 `
  --weights_folder $WeightsFolder `
  --output_dir $ResultsDir 2>&1 | Tee-Object -FilePath $PostprocessLog -Append

& $Python citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py `
  --split val `
  --results_dir $ResultsDir `
  --weights_folder $WeightsFolder `
  --output_dir "$VisualDir/single_model_val" 2>&1 | Tee-Object -FilePath $PostprocessLog -Append

& $Python citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py `
  --split test `
  --results_dir $ResultsDir `
  --weights_folder $WeightsFolder `
  --output_dir "$VisualDir/single_model_test" 2>&1 | Tee-Object -FilePath $PostprocessLog -Append

& $Python citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/compare_phase2_visuals.py `
  --split val `
  --phase2_results_dir $ResultsDir `
  --phase2_weights $WeightsFolder `
  --output_dir "$VisualDir/baseline_vs_hybrid_val" `
  --baseline_name "Plain Citrus" `
  --phase2_name "Hybrid abs w0.1 30ep" 2>&1 | Tee-Object -FilePath $PostprocessLog -Append

& $Python citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/compare_phase2_visuals.py `
  --split test `
  --phase2_results_dir $ResultsDir `
  --phase2_weights $WeightsFolder `
  --output_dir "$VisualDir/baseline_vs_hybrid_test" `
  --baseline_name "Plain Citrus" `
  --phase2_name "Hybrid abs w0.1 30ep" 2>&1 | Tee-Object -FilePath $PostprocessLog -Append

Stop-Transcript
