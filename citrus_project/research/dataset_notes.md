# Dataset Notes

This file is the single place for current dataset-building, alignment, and label-quality notes that may later support the paper.

## Final Label Route Decision

Date: 2026-04-17

Decision: use `exact_lidar_parent_child_inverted` as the default LiDAR-to-ZED transform for final Citrus dense-label generation.

### Evidence Used

#### 1. Transform Candidate Audit

Four physically meaningful calibration-chain interpretations were checked:

- `production_current`
- `current_chain_no_invert`
- `exact_lidar_parent_child_direct`
- `exact_lidar_parent_child_inverted`

The two direct/no-invert variants produced clearly wrong vertical projection bands. The remaining plausible routes were:

- Route A: `production_current`
- Route B: `exact_lidar_parent_child_inverted`

#### 2. 200-Sample Time-Spread Route Probe

Raw output files:

- `citrus_project/dataset_workspace/projection_alignment_audit/time_spread_metrics_200/audit_metrics.csv`
- `citrus_project/dataset_workspace/projection_alignment_audit/time_spread_metrics_200/audit_summary.json`

Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/dataset_workspace/audit_projection_alignment.py --max_samples 200 --metrics_only --output_dir projection_alignment_audit/time_spread_metrics_200
```

What was tested:

- 200 RGB-LiDAR pairs selected across 5282 matched pairs
- interpolation method: `local_idw`
- Route A: `production_current`
- Route B: `exact_lidar_parent_child_inverted`

Timing quality:

| Metric | Median |
|---|---:|
| RGB-LiDAR timestamp difference | 27.874 ms |
| RGB-ZED depth timestamp difference | 12.711 ms |

Route comparison:

| Metric | Route A: production_current | Route B: exact_lidar_parent_child_inverted | Better direction |
|---|---:|---:|---|
| Dense fill ratio | 42.46% | 36.63% | Higher gives more label coverage |
| ZED/LiDAR overlap ratio | 23.13% | 21.25% | Higher gives more comparison area |
| ZED median absolute difference | 0.538 m | 0.192 m | Lower is closer to ZED |
| ZED median relative difference | 22.12% | 6.90% | Lower is closer to ZED |
| Valid projected ratio | 32.82% | 32.91% | Higher means more projected points land validly |

Pairwise result:

- Route A had higher dense fill on 198/200 samples
- Route B had lower ZED absolute difference on 200/200 samples
- Route B had lower ZED relative difference on 200/200 samples

Interpretation:

Route A produces more filled label pixels, but Route B agrees much better with ZED depth wherever both labels can be compared.

#### 3. Final Visual Spot-Check

Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/dataset_workspace/audit_projection_alignment.py --max_samples 12 --output_dir projection_alignment_audit/time_spread_visual_12
```

Generated local visual diagnostics:

- `citrus_project/dataset_workspace/projection_alignment_audit/time_spread_visual_12/overlays/`
- `citrus_project/dataset_workspace/projection_alignment_audit/time_spread_visual_12/details_production_current/`
- `citrus_project/dataset_workspace/projection_alignment_audit/time_spread_visual_12/details_exact_lidar_parent_child_inverted/`

Visual result:

- Route B keeps the natural horizontal LiDAR scan structure
- Route B remains visually plausible across time-spread samples
- The two rejected transform candidates remain visibly wrong

### Rationale

`production_current` gives more filled pixels, but label coverage is less important than label correctness. For training and evaluation, lower-coverage labels with a valid mask are preferable to denser labels whose depth values disagree strongly with ZED depth.

The final route therefore prioritizes:

- lower ZED agreement error
- physically plausible overlays
- conservative `local_idw` densification
- valid-mask-aware training/evaluation

## Conservative Dense Label Generation

Current default interpolation is `local_idw`.

Why it matters:

- it fills only near LiDAR support
- it rejects fills when neighboring depths disagree too much
- it is more conservative than visually fuller interpolation methods

Paper-facing use:

- dataset preprocessing
- label reliability
- valid-mask-aware training/evaluation

## Current State

Implemented and decided:

- final/default route: `exact_lidar_parent_child_inverted`
- alternate route kept available: `production_current`
- default dense-label interpolation: `local_idw`

Still pending:

- full `build_training_dataset.py` run
- final built-sample counts
- final train/val/test counts
- any final parameter lock after the full build

