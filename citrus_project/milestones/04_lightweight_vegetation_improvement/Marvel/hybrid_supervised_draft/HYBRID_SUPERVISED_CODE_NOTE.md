# Hybrid Supervised Draft Code Note

Date: 2026-05-18
Status: isolated draft code only; root runnable training files were not modified by this draft.

## Purpose

This folder contains copied Phase 2-aware Lite-Mono code files modified for the next proposed hybrid supervised Citrus experiment.

The method keeps the existing Lite-Mono self-supervised photometric training and Phase 2 boundary-loss compatibility, then adds an optional masked LiDAR depth supervision term:

```text
total_loss = photometric_self_supervised_loss
           + optional_boundary_loss
           + lidar_loss_weight * masked_scale_aware_lidar_depth_loss
```

## Copied Files

```text
layers.py
trainer.py
options.py
```

These were copied from the current root code after Phase 2 boundary-loss integration. They are placed here so the implementation can be reviewed or shown without immediately changing the root runnable training path.

## Main Code Changes

### options.py

Added hybrid supervised flags:

```text
--lidar_loss_weight
--lidar_loss_type
--lidar_scale_align
--lidar_loss_min_depth
--lidar_loss_max_depth
--lidar_loss_warmup_epochs
--lidar_loss_scales
--lidar_loss_min_valid_pixels
--lidar_scale_penalty_weight
```

Default behavior stays disabled:

```text
--lidar_loss_weight 0.0
```

### trainer.py

Added option defaults and validation for the LiDAR loss settings.

Added:

```text
current_lidar_loss_weight()
compute_lidar_supervision_loss(inputs, outputs, scale)
```

Integrated the supervised term into `compute_losses()` after the normal smoothness and optional boundary loss terms.

The first draft uses:

```text
masked log-depth L1
median scale alignment
scale 0 by default
valid pixels from inputs["label_mask"] or inputs["valid_mask"]
```

## Data Used

The current Citrus prepared dataset loader already returns:

```text
inputs["depth_gt"]
inputs["valid_mask"]
inputs["label_mask"]
```

The loss uses `label_mask` first because it combines valid, finite, positive label checks. If `label_mask` is missing, it falls back to `valid_mask`.

## First Intended Experiment

Recommended first gate after integrating this draft into the runnable root path:

```text
hybrid_supervised_b12_2ep_logl1_median_w01
```

Suggested settings:

```text
--lidar_loss_weight 0.1
--lidar_loss_type log_l1
--lidar_scale_align median
--lidar_loss_scales 0
--batch_size 12
--num_epochs 2
--seed 0
```

Compare against:

```text
plain_citrus_b12_2ep_control
phase2_boundary_loss_b12_2ep_w005
phase2_boundary_loss_b12_30ep_w005
plain Citrus final 30ep baseline
```

## Review Notes

This draft is intentionally conservative:

- It does not force absolute scale by default; it median-aligns the prediction to the LiDAR labels first.
- It only applies supervision on valid label pixels.
- It logs supervised loss, weighted supervised loss, valid fraction, and scale ratio.
- It keeps `lidar_loss_weight=0.0` as the default so existing behavior remains unchanged until explicitly enabled.

Before running a real experiment, copy or merge these changes into the root runnable files and run a one-step smoke test.
## 2026-05-19 Scale-Anchoring Update

Added an optional middle-ground scale anchor:

```text
--lidar_scale_penalty_weight
```

When `--lidar_scale_align median` is active, the normal masked LiDAR loss still learns relative depth after median alignment. The new scale penalty also measures the raw predicted median depth against the LiDAR median depth and adds a small log-scale penalty. This tests whether the median-aligned recipe can keep its relative-depth advantage without allowing absolute scale to drift.

Validation status:

- `py_compile` passed for `layers.py`, `options.py`, `trainer.py`, and `train_hybrid_supervised.py`.
- one-step smoke `hybrid_supervised_scale_penalty_smoke_1step` logged `lidar_scale_penalty/0` successfully.
- 2-epoch gate `hybrid_supervised_b12_2ep_logl1_median_scaleanchor_w01_p01` completed and postprocessing finished.

Current interpretation:

The middle-ground code works, but the direct absolute-scale recipe with `--lidar_scale_align none` produced stronger metrics after 2 epochs.