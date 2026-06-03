$ErrorActionPreference = "Stop"

$RepoRoot = "C:\Proj\lite-Mono"
$PythonRunner = "C:\Proj\miniforge3\condabin\mamba.bat"
$RunName = "hybrid_supervised_b12_2ep_logl1_median_w01_full"
$RunDir = "citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/runs/$RunName"
$WeightsFolder = "$RunDir/models/weights_1"
$ResultsDir = "citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/results/$RunName"
$VisualDir = "$ResultsDir/visuals"

Set-Location $RepoRoot

& $PythonRunner run -n lite-mono python `
  citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/plot_training_losses.py `
  --run_dir $RunDir `
  --output_dir "$ResultsDir/loss_plots"

& $PythonRunner run -n lite-mono python `
  citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py `
  --split val `
  --max_samples 0 `
  --run_model `
  --summary_only `
  --progress_interval 50 `
  --weights_folder $WeightsFolder `
  --output_dir $ResultsDir

& $PythonRunner run -n lite-mono python `
  citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py `
  --split test `
  --max_samples 0 `
  --run_model `
  --summary_only `
  --progress_interval 50 `
  --weights_folder $WeightsFolder `
  --output_dir $ResultsDir

& $PythonRunner run -n lite-mono python `
  citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py `
  --split val `
  --results_dir $ResultsDir `
  --weights_folder $WeightsFolder `
  --output_dir "$VisualDir/single_model_val"

& $PythonRunner run -n lite-mono python `
  citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py `
  --split test `
  --results_dir $ResultsDir `
  --weights_folder $WeightsFolder `
  --output_dir "$VisualDir/single_model_test"

& $PythonRunner run -n lite-mono python `
  citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/compare_phase2_visuals.py `
  --split val `
  --phase2_results_dir $ResultsDir `
  --phase2_weights $WeightsFolder `
  --output_dir "$VisualDir/baseline_vs_hybrid_val" `
  --baseline_name "Plain Citrus" `
  --phase2_name "Hybrid supervised w0.1"

& $PythonRunner run -n lite-mono python `
  citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/compare_phase2_visuals.py `
  --split test `
  --phase2_results_dir $ResultsDir `
  --phase2_weights $WeightsFolder `
  --output_dir "$VisualDir/baseline_vs_hybrid_test" `
  --baseline_name "Plain Citrus" `
  --phase2_name "Hybrid supervised w0.1"