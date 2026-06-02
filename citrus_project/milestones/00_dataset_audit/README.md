# Milestone 0: Dataset Audit

This milestone answered the question:

> Can we turn the raw Citrus Farm sensor data into a prepared RGB + depth-label dataset that is reliable enough to start real Lite-Mono baseline evaluation?

Short answer: yes, enough to move into Milestone 1, with clear caveats about valid masks and derived LiDAR labels.

## Current Status

- Milestone 0 is complete through the full dataset build.
- The final/default dense-label route is `exact_lidar_parent_child_inverted`.
- The default densification method is `local_idw`.
- The prepared dataset has already been built at:
  - `citrus_project/dataset_workspace/prepared_training_dataset/`

Final built dataset summary:

- total samples: 5282
- train: 4311
- val: 564
- test: 407

## What We Did

Milestone 0 was not just "download a dataset." The real job was to create trustworthy depth labels for monocular-depth evaluation.

The workflow was:

1. Download the selected Citrus Farm Sequence 01 LiDAR/base bags.
2. Download overlapping ZED bags so RGB/depth timestamps overlap with the LiDAR time window.
3. Extract ZED left RGB images and ZED depth arrays.
4. Extract Velodyne LiDAR scans.
5. Match RGB frames to LiDAR scans by timestamp, not by filename order.
6. Project LiDAR points into the ZED image plane using calibration transforms.
7. Audit multiple LiDAR-to-ZED transform interpretations with visual overlays and metrics.
8. Densify sparse projected LiDAR into semidense image-shaped depth labels.
9. Save a valid mask beside every dense label so evaluation/training can ignore untrusted pixels.
10. Build train/val/test split files and metrics summaries.

The important mental model:

```text
raw sensors
-> timestamp-matched RGB + LiDAR pairs
-> projected LiDAR pixels in the RGB image
-> locally densified depth label in meters
-> valid mask saying which pixels are trusted
-> train/val/test split manifests
```

## Why We Needed An Audit

The Citrus Farm dataset gives raw sensors and calibration, but our final dense labels are a project-derived product.

That means we could not assume:

- every LiDAR point was projected into the camera correctly
- every interpolation method created reliable labels
- every filled pixel should be trusted

So we audited before treating the labels as evaluation data.

The core calibration question was:

```text
Which LiDAR-to-ZED transform chain actually makes LiDAR points land on the correct image structures?
```

Four transform interpretations were checked:

- `production_current`
- `current_chain_no_invert`
- `exact_lidar_parent_child_direct`
- `exact_lidar_parent_child_inverted`

The two direct/no-invert routes looked visibly wrong. The two plausible routes were:

- `production_current`
- `exact_lidar_parent_child_inverted`

The final choice was `exact_lidar_parent_child_inverted` because it agreed much better with ZED depth where both labels overlapped, even though it produced slightly lower dense-label coverage.

## Why We Chose `local_idw`

Sparse LiDAR does not cover every image pixel. Densification fills some nearby gaps.

Earlier interpolation could create visually smooth but unreliable surfaces, especially in vegetation where branches, leaves, and empty space are mixed together.

`local_idw` was chosen because it is more conservative:

- it fills only near LiDAR support
- it uses nearby LiDAR depths instead of inventing large smooth surfaces
- it rejects candidate pixels when nearby depths disagree too much
- it leaves more holes, but those holes are safer than fake labels

This is why the valid mask is part of the dataset. A pixel can exist in the image but still be ignored for scoring if its depth label is not trusted.

## Beginner Questions This Milestone Answered

These are the kinds of questions that came up while building Milestone 0. Teammates with similar background knowledge should understand these before using the dataset outputs.

### Are the dense labels official Citrus Farm ground truth?

No.

They are project-derived LiDAR-densified labels. Citrus Farm provides useful raw modalities, but our pipeline turns RGB + LiDAR into image-aligned dense-ish depth labels for monocular-depth work.

Paper-facing wording should be careful:

```text
LiDAR-densified depth labels with valid masks
```

not:

```text
perfect dense ground truth
```

### What does each dense label value mean?

The label files are numeric `.npz` arrays. Each trusted value is depth in meters.

Example meaning:

```text
label pixel value = 2.4
```

means:

```text
that image pixel is estimated to be 2.4 meters away
```

Invalid or untrusted pixels are ignored by the valid mask.

### Why do we need a valid mask?

Because not every pixel has a trustworthy LiDAR-derived label.

The valid mask is also an image-shaped array:

```text
1 = use this pixel for evaluation/training
0 = ignore this pixel
```

This is especially important in vegetation scenes, where interpolation can easily fill gaps that are not physically reliable.

### Are PNG depth panels the labels?

No.

PNG panels are visual diagnostics for humans. The actual labels and masks are `.npz` numeric arrays.

Use PNGs for:

- sanity checks
- presentations
- future paper figures

Use NPZ arrays for:

- metrics
- training
- evaluation

### Why are split files simple?

The split files mainly answer:

```text
which samples are train, val, or test?
```

The richer metadata is in:

```text
prepared_training_dataset/metrics/all_samples.csv
```

That CSV links each RGB sample to dense labels, valid masks, LiDAR paths, timestamp diagnostics, and quality metrics.

## Final Artifacts

Generated by `build_training_dataset.py`:

- `prepared_training_dataset/dense_lidar_npz/`
- `prepared_training_dataset/dense_lidar_valid_mask_npz/`
- `prepared_training_dataset/metrics/all_samples.csv`
- `prepared_training_dataset/metrics/summary.json`
- `prepared_training_dataset/splits/train_pairs.txt`
- `prepared_training_dataset/splits/val_pairs.txt`
- `prepared_training_dataset/splits/test_pairs.txt`

Important build defaults:

- transform mode: `exact_lidar_parent_child_inverted`
- interpolation method: `local_idw`
- split strategy: `time_block`
- ZED depth sanity metrics: enabled

## How To Read The Evidence

Use these files in this order:

1. `AGENTS.md`
   - current project-wide source of truth
2. this README
   - teammate-friendly Milestone 0 handoff
3. `citrus_project/research/dataset_notes.md`
   - deeper evidence for transform choice, route metrics, and build results
4. `citrus_project/dataset_workspace/prepared_training_dataset/metrics/summary.json`
   - exact machine-readable build parameters and split counts

## Hand-Off To Milestone 1

Milestone 1 uses the prepared dataset to evaluate original Lite-Mono on Citrus.

The most important Milestone 0 output for Milestone 1 is:

```text
RGB image + dense LiDAR label + valid mask
```

Milestone 1 should compare Lite-Mono predictions only where the valid mask says the LiDAR label is trusted.

## Low-Storage Collaboration Support

`sample_pack/` is the place for a small shared set of RGB images, label visuals, and lightweight indexing files so teammates can help without downloading the full dataset workspace.

This is intended for:

- scene taxonomy
- qualitative example selection
- presentation/paper-support discussion
- teammate understanding without large storage requirements
