# Milestone 1 Results

This folder is for saved original Lite-Mono Citrus baseline result files.

Expected files from `evaluate_lite_mono_citrus.py`:

- `*_summary.json`
  - one aggregate summary for a run
  - contains split name, run settings, valid-pixel coverage, raw-scale mean metrics, and median-scaled mean metrics
  - contains evaluator timing and synchronized model-forward timing when model inference is enabled
  - contains `model_info` with encoder/depth-decoder parameter counts and checkpoint sizes
- `*_per_sample.csv`
  - one row per evaluated RGB image
  - useful for finding easy/hard samples and later qualitative failure cases
  - includes per-sample wall time and model-forward timing columns

Smoke-test outputs with `maxN` in the filename are ignored by default because they are not official baseline results.

Final full-split outputs should use:

```powershell
--max_samples 0
```

and should be reviewed before being committed.

## Current Full-Split Outputs

Generated on 2026-04-28 with GPU:

- `val_lite-mono_full_summary.json`
- `val_lite-mono_full_per_sample.csv`
- `test_lite-mono_full_summary.json`
- `test_lite-mono_full_per_sample.csv`

Headline metrics:

- validation, 564/564 samples: median-scaled `abs_rel=0.4176`, `rmse=3.1642`, `a1=0.4629`
- test, 407/407 samples: median-scaled `abs_rel=0.3836`, `rmse=3.1451`, `a1=0.4989`
- validation raw-scale `abs_rel=0.7128`; test raw-scale `abs_rel=0.7273`

Interpretation note:

- raw-scale tells us the original pretrained model's absolute distance scale transfers poorly to Citrus
- median-scaled tells us how much relative depth structure remains after aligning the prediction scale per image
- the per-sample CSV files are the next place to look for easy/hard frames and qualitative failure cases

Timing note:

- evaluator-loop timing includes image/label loading, model inference, resizing, and metric computation
- model-forward timing is closer to neural-network inference speed, but it is still measured inside this evaluator rather than a dedicated deployment benchmark
- small GPU smoke runs can be distorted by first-sample CUDA warmup overhead
