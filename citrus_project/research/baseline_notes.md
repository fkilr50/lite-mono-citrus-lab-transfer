# Baseline Notes

This file is the single place for baseline-model notes and early model checks that may later support the paper.

## Original Lite-Mono Single-Image Citrus Demo

Date: 2026-04-16

Paper relevance: qualitative baseline / motivation artifact only. This is not a full baseline result.

Purpose: verify that original pretrained Lite-Mono can run on an extracted Citrus RGB frame and produce a full-image disparity visualization.

### Command

The input image was copied out of the dataset folder first so generated outputs do not contaminate extracted dataset artifacts.

```powershell
D:/Conda_Envs/lite-mono/python.exe test_simple.py --load_weights_folder weights/lite-mono --image_path citrus_project/research/generated/lite_mono_single_image_demo/zed_2023-07-18-14-26-49_0_bag_1689715609331936216.png --model lite-mono --no_cuda
```

### Local Generated Files

These files are ignored by git:

- `citrus_project/research/generated/lite_mono_single_image_demo/zed_2023-07-18-14-26-49_0_bag_1689715609331936216.png`
- `citrus_project/research/generated/lite_mono_single_image_demo/zed_2023-07-18-14-26-49_0_bag_1689715609331936216_disp.jpeg`
- `citrus_project/research/generated/lite_mono_single_image_demo/zed_2023-07-18-14-26-49_0_bag_1689715609331936216_disp.npy`

### Interpretation

This run shows that original Lite-Mono can produce a dense prediction on a Citrus RGB image. It starts the baseline milestone, but it does not complete it.

To complete the baseline milestone, the project still needs:

- original Lite-Mono inference on a validation/test split
- evaluation against LiDAR-densified labels and valid masks
- Citrus-specific metrics without KITTI crop assumptions
- runtime, parameter count, and model-size reporting
- qualitative failure-case analysis in vegetation-heavy scenes

### How This Can Appear In The Paper

Use this kind of output later as a qualitative figure only after we generate a proper set of baseline predictions on selected validation/test frames.

Possible paper figure:

- RGB input
- original Lite-Mono prediction
- LiDAR-densified label visualization
- valid mask
- improved model prediction

Do not use the current single-image run as a quantitative result.

## Hybrid Supervised 30-Epoch Checkpoint Scan

Date completed: 2026-05-22

Run:

```text
C:/Proj/lite-Mono/citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/runs/hybrid_supervised_b12_30ep_logl1_abs_w01_fresh_sched/
```

Sweep outputs:

```text
C:/Proj/lite-Mono/citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/results/hybrid_supervised_b12_30ep_logl1_abs_w01_fresh_sched_checkpoint_sweep/
```

Purpose:

Check whether the final checkpoint from the 30-epoch hybrid supervised run was actually the best checkpoint before using it as the base reference for the next LiDAR-aware edge-loss experiment.

Result summary:

| checkpoint | split | raw abs_rel | raw a1 | median abs_rel | median a1 | median scale ratio |
|---|---:|---:|---:|---:|---:|---:|
| `weights_13` | val | 0.1716 | 0.8131 | 0.1746 | 0.8160 | 1.0407 |
| `weights_29` | val | 0.1913 | 0.7968 | 0.1933 | 0.7805 | 0.9850 |
| `weights_13` | test | 0.1620 | 0.8149 | 0.1677 | 0.8159 | 1.0569 |
| `weights_10` | test | 0.1644 | 0.8227 | 0.1708 | 0.8116 | 1.0223 |
| `weights_8` | test | 0.1669 | 0.8193 | 0.1725 | 0.8042 | 1.0038 |
| `weights_29` | test | 0.1741 | 0.8186 | 0.1791 | 0.8001 | 1.0061 |

Interpretation:

The final checkpoint is not the best checkpoint from the 30-epoch run. The validation sweep selected `weights_13` by raw abs_rel, and test confirmation over the top three validation candidates also favored `weights_13` by raw abs_rel. This means the long run was not wasted, but reporting the final epoch as the best model would be misleading.

Current recommendation:

Use `weights_13` as the selected hybrid supervised checkpoint pending visual comparison. Before preparing the next LiDAR-aware edge-loss training experiment, generate direct Plain Citrus versus Hybrid `weights_13` visual panels so the qualitative story matches the improved metrics.

### Visual Comparison Follow-Up

Date generated: 2026-05-22

Output folder:

```text
C:/Proj/lite-Mono/citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/results/hybrid_supervised_b12_30ep_logl1_abs_w01_fresh_sched_checkpoint_sweep/weights_13_visual_comparisons/
```

Generated panel groups:

```text
plain_vs_weights13_val/
plain_vs_weights13_test/
weights29_vs_weights13_val/
weights29_vs_weights13_test/
```

Direct `weights_29` versus `weights_13` selected-panel summary:

| split | role | index | `weights_29` median abs_rel/a1 | `weights_13` median abs_rel/a1 | verdict |
|---|---|---:|---:|---:|---|
| val | bad | 448 | 0.3389 / 0.4090 | 0.3824 / 0.2692 | `weights_29` better |
| val | typical | 377 | 0.1851 / 0.7994 | 0.1658 / 0.8341 | `weights_13` better |
| val | good | 42 | 0.0936 / 0.9134 | 0.0832 / 0.9417 | `weights_13` better |
| test | bad | 344 | 0.4083 / 0.0866 | 0.4473 / 0.0726 | `weights_29` better |
| test | typical | 373 | 0.2356 / 0.7418 | 0.1694 / 0.8205 | `weights_13` better |
| test | good | 314 | 0.1054 / 0.9125 | 0.0946 / 0.9380 | `weights_13` better |

Interpretation:

The visual comparison supports the checkpoint-sweep result, but it is not a universal per-image win. `weights_13` improves typical and good samples by reducing common-case error and improving `a1`, while some selected bad cases still favor `weights_29`. The final checkpoint does not look catastrophically broken; instead, it seems to have drifted away from the best validation/test tradeoff after the middle of training. This is consistent with mild over-training or noisy late-epoch optimization rather than total model collapse.

