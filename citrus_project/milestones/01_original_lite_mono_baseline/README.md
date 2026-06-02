# Milestone 1: Original Lite-Mono Baseline

Use this folder for milestone-specific helpers, notes, or experiment files related to:

- original Lite-Mono inference on Citrus
- baseline evaluation scripts/results
- qualitative baseline figures and failure cases

Current status:

- This is the active next milestone.
- A one-image Lite-Mono sanity demo already exists as qualitative context only.
- The Citrus evaluator entry point has started as `evaluate_lite_mono_citrus.py`.
- Current evaluator slice: data inspection, optional model inference, valid-mask-aware metric comparison, aggregate metric summaries, optional result-file saving, runtime/FPS metadata, and model parameter/checkpoint metadata.
- Current analysis slice: `analyze_lite_mono_citrus_results.py` selects good/typical/bad samples from the full per-sample CSV and renders visual panels.
- Full validation/test baseline runs were completed on GPU on 2026-04-28.
- First validation good/typical/bad visual panels were generated on 2026-04-28.
- First beginner-friendly visual interpretation note is now available in `visual_interpretation.md`.
- Test good/typical/bad visual panels were generated on 2026-04-29.
- Remaining Milestone 1 work: expand failure taxonomy if needed, and optionally add FLOPs or a dedicated deployment-speed benchmark.

Main input dataset:

- `citrus_project/dataset_workspace/prepared_training_dataset/`

What this milestone should produce:

- baseline inference on Citrus validation/test data: done for original Lite-Mono
- evaluation against dense LiDAR labels: done for original Lite-Mono
- valid-mask-aware metrics: done for original Lite-Mono
- runtime/parameter notes: evaluator-level timing and parameter metadata are saved
- qualitative examples and failure cases: validation and test good/typical/bad panels generated and explained in `visual_interpretation.md`

Current helper commands:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 3
```

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 1 --run_model --no_cuda
```

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 0 --run_model --summary_only
```

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 3 --run_model --summary_only --progress_interval 1 --no_cuda --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results
```

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 3 --run_model --summary_only --progress_interval 1 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results
```

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 2 --run_model --summary_only --progress_interval 1 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results
```

Full baseline commands used:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 0 --run_model --summary_only --progress_interval 50 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results
```

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split test --max_samples 0 --run_model --summary_only --progress_interval 50 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results
```

Validation visual-analysis command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py --split val
```

Test visual-analysis command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py --split test
```

Current helper behavior:

- reads the prepared split file
- joins split entries with `metrics/all_samples.csv`
- checks RGB, dense LiDAR label, and valid-mask paths
- prints image size, array shapes, value summaries, valid-pixel count, and pairing diagnostics
- with `--run_model`, loads `weights/lite-mono`, runs the original model, and prints input tensor, raw closeness level, scaled disparity, predicted depth, and resized depth summaries
- with `--run_model`, also compares predicted depth to dense LiDAR labels on valid-mask pixels and prints raw-scale plus median-scaled depth metrics
- with `--summary_only`, suppresses per-sample detail and prints aggregate metric summaries using per-image metric means
- with `--max_samples 0`, evaluates the full selected split
- with `--output_dir`, saves one aggregate `*_summary.json` file and one `*_per_sample.csv` file
- saved summaries include evaluator-loop timing and synchronized model-forward timing/FPS
- per-sample CSV files include wall-time and model-forward timing columns
- printed model setup includes encoder, depth-decoder, and total depth-inference parameter counts
- saved summaries include `model_info` with parameter counts and checkpoint sizes
- `analyze_lite_mono_citrus_results.py` reads a full per-sample CSV, selects good/typical/bad samples by `median_scaled_a1`, reruns inference for only those samples, and saves visual panels plus selection summaries

Current original `lite-mono` depth-inference model size:

- total depth-inference parameters: 3,074,747
- encoder parameters: 2,848,120
- depth-decoder parameters: 226,627
- total checkpoint size: about 11.94 MiB
- note: this excludes the training-only pose network

Saved result location:

- `citrus_project/milestones/01_original_lite_mono_baseline/results/`
- `maxN` smoke result files are ignored by default so they are not mistaken for official full-split results
- full validation/test result files are:
  - `val_lite-mono_full_summary.json`
  - `val_lite-mono_full_per_sample.csv`
  - `test_lite-mono_full_summary.json`
  - `test_lite-mono_full_per_sample.csv`

Headline full-split metrics:

- validation: median-scaled `abs_rel=0.4176`, `rmse=3.1642`, `a1=0.4629`, model-forward FPS `28.478`
- test: median-scaled `abs_rel=0.3836`, `rmse=3.1451`, `a1=0.4989`, model-forward FPS `29.529`
- raw-scale metrics are much worse, which is expected for a pretrained monocular model with poor absolute scale transfer to Citrus

Visual-analysis output location:

- `citrus_project/milestones/01_original_lite_mono_baseline/visuals/`
- first validation selection by `median_scaled_a1`:
  - good index 420: `a1=0.8264`, `abs_rel=0.1510`
  - typical index 82: `a1=0.4784`, `abs_rel=0.3405`
  - bad index 442: `a1=0.0468`, `abs_rel=0.7835`
- test selection by `median_scaled_a1`:
  - good index 24: `a1=0.7709`, `abs_rel=0.1821`
  - typical index 7: `a1=0.5301`, `abs_rel=0.3168`
  - bad index 46: `a1=0.0761`, `abs_rel=0.6204`

Main record files:

- `AGENTS.md`
- `citrus_project/research/baseline_notes.md`
- `citrus_project/milestones/01_original_lite_mono_baseline/visual_interpretation.md`
- `citrus_project/TASK_BOARD.md`
