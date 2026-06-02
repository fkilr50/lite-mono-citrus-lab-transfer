# Paper Shortlist

This file tracks research artifacts that may later become paper tables, figures, or method details.

## Strong Candidates

### Dataset/Label Route Selection

Evidence notes:

- `citrus_project/research/dataset_notes.md`
- raw metrics: `citrus_project/dataset_workspace/projection_alignment_audit/time_spread_metrics_200/audit_metrics.csv`

Why it matters:

- Shows the LiDAR-to-camera transform route was selected using a time-spread quantitative check.
- Supports the claim that label generation was validated rather than assumed.
- Provides a table-ready comparison between `production_current` and `exact_lidar_parent_child_inverted`.

Paper section fit:

- Dataset construction
- Ground-truth / pseudo-label generation
- Calibration validation

Current status:

- Locked as the final/default dense-label route: `exact_lidar_parent_child_inverted`.
- Full prepared dataset build is still a heavy local artifact step and has not been run in the cleanup commit.

### Conservative Dense Label Generation

Evidence notes:

- `citrus_project/dataset_workspace/densify_lidar.py`
- `citrus_project/research/dataset_notes.md`

Why it matters:

- `local_idw` fills only near LiDAR support and rejects fills when neighboring depths disagree too much.
- This supports a paper-facing argument that sparse vegetation labels should prefer validity masks over visually full but hallucinated labels.

Paper section fit:

- Dataset preprocessing
- Label reliability
- Training/evaluation mask construction

Current status:

- Implemented and tested.
- Needs final parameter lock before full dataset build.

## Early Candidates

### Original Lite-Mono Qualitative Citrus Prediction

Evidence notes:

- `citrus_project/research/baseline_notes.md`
- generated local files under `citrus_project/research/generated/lite_mono_single_image_demo/`

Why it matters:

- Demonstrates original Lite-Mono can run on Citrus RGB frames.
- Useful as an early qualitative baseline/motivation example.

Paper section fit:

- Motivation
- Qualitative baseline comparison
- Failure-case analysis

Current status:

- Single-image sanity demo only.
- Not enough for claims or metrics.
- Needs validation/test split inference and masked evaluation before becoming paper evidence.

## Not Paper Evidence Yet

### Completed Presentation Slides

Source:

- removed after presentation cleanup

Why not:

- Useful for explaining progress at the time, but not a primary research artifact.
- Any table/figure from it should be regenerated from raw metrics or tracked research summaries before paper use.

