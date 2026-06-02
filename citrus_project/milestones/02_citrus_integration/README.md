# Milestone 2: Citrus Integration

Use this folder for milestone-specific helpers, notes, or experiment files related to:

- Citrus Dataset/DataLoader integration
- Citrus-specific evaluation code
- split-manifest and evaluation plumbing

Current status:

- Milestone 2 has started with a deliberately small Dataset/DataLoader slice.
- `citrus_prepared_dataset.py` defines `CitrusPreparedDataset`, a loader for prepared Citrus split manifests.
- The loader supports target-only samples by default and same-split temporal triplets when `frame_ids=[0, -1, 1]` is requested.
- `inspect_citrus_prepared_dataset.py` smoke-tests target-only or temporal loading through a PyTorch `DataLoader`.
- `inspect_temporal_neighbors.py` checks whether prepared targets have same-split, same-session previous/next RGB neighbors for self-supervised training.
- `dry_run_lite_mono_temporal_batch.py` checks one metadata-free temporal Citrus batch against Lite-Mono's depth, pose, projection, and reprojection-shape path.
- `smoke_depth_metric_guard.py` checks the root trainer's depth-metric guard for KITTI and Citrus-shaped labels.
- `smoke_root_citrus_trainer_wiring.py` checks that root `Trainer` can select Citrus, build train/val DataLoaders, process one batch, and use the Citrus-safe depth metric mode.
- `smoke_root_citrus_one_step_train.py` checks one full root Citrus forward/backward/optimizer update.
- `smoke_citrus_color_augmentation.py` checks that train samples use `color_aug` jitter and validation samples stay unaugmented.
- Milestone 2 core integration is complete, including a CUDA one-step smoke. No real Citrus fine-tuning experiment has started yet.

Current data contract:

- reads `prepared_training_dataset/splits/<split>_pairs.txt`
- joins split entries with `prepared_training_dataset/metrics/all_samples.csv`
- loads RGB images from `extracted_rgbd/zed2i_zed_node_left_image_rect_color/`
- loads dense LiDAR labels from `prepared_training_dataset/dense_lidar_npz/`
- loads valid masks from `prepared_training_dataset/dense_lidar_valid_mask_npz/`
- returns Citrus ZED-left camera intrinsics as `K`, `inv_K`, and `K_normalized`
- returns model-sized RGB tensors by default (`3 x 192 x 640`) while keeping depth labels and masks at native `1 x 720 x 1280`
- temporal mode returns Lite-Mono-style keys such as `("color", -1, 0)`, `("color", 0, 0)`, `("color", 1, 0)`, `("K", 0)`, and `("inv_K", 0)`
- `include_metadata=False` can be used later for trainer-facing batches where every value must be tensor-like

Intrinsics note:

- The loader currently provides a pinhole `K` matrix derived from the ZED-left calibration used by the dataset pipeline.
- Distortion coefficients are not passed through the training sample because Lite-Mono's image-warping code expects a pinhole camera matrix, and the active RGB topic is `/zed2i/zed_node/left/image_rect_color`.
- This should be revisited if Citrus photometric warps show systematic edge or alignment artifacts.

Smoke command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/inspect_citrus_prepared_dataset.py --samples_per_split 2 --batch_size 2
```

Temporal DataLoader smoke command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/inspect_citrus_prepared_dataset.py --temporal --samples_per_split 2 --batch_size 2 --splits train val
```

Temporal-neighbor diagnostic command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/inspect_temporal_neighbors.py
```

Trainer-compatibility dry-run command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/dry_run_lite_mono_temporal_batch.py --batch_size 2 --no_cuda
```

Citrus-safe depth-metric guard smoke command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_depth_metric_guard.py
```

Root Citrus trainer wiring smoke command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_root_citrus_trainer_wiring.py
```

Root Citrus one-step training smoke command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_root_citrus_one_step_train.py
```

CUDA version:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_root_citrus_one_step_train.py --use_cuda
```

Citrus color augmentation smoke command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_citrus_color_augmentation.py
```

Latest smoke result:

- train split loaded with 4311 samples
- validation split loaded with 564 samples
- default RGB batch shape: `2 x 3 x 192 x 640`
- native depth/mask batch shape: `2 x 1 x 720 x 1280`
- resized Citrus K for 640 x 192 RGB begins with `fx=263.77954`, `fy=140.94998`, `cx=323.59875`, `cy=95.26605`
- temporal DataLoader smoke loaded train as 4275 safe triplet targets and validation as 560 safe triplet targets
- temporal RGB tensors for frame `0`, `-1`, and `1` each batch as `2 x 3 x 192 x 640`

Latest temporal-neighbor result with the default 200 ms cap:

- all prepared samples inspected: 5282
- train safe triplets: 4275 / 4311 (99.16%)
- validation safe triplets: 560 / 564 (99.29%)
- test safe triplets: 399 / 407 (98.03%)
- same-split neighbor deltas are about 100 ms median in all splits
- some boundary samples lack one neighbor, and a few nearest global neighbors cross split boundaries, so trainer integration should use same-split neighbors and explicitly skip or handle boundary samples

Latest trainer-compatibility dry-run result:

- CPU dry runs passed with batch sizes 1 and 2
- the batch-size-2 run used 4275 train temporal samples and 45 tensor-like batch values
- frame `0`, `-1`, and `1` RGB tensors each had shape `2 x 3 x 192 x 640`
- `depth_gt` and `valid_mask` kept native Citrus shape `2 x 1 x 720 x 1280`
- Lite-Mono depth outputs, pose transforms, projection grids, and warped source RGB tensors were produced successfully
- the batch-size-2 reprojection smoke loss was `0.076165`
- this is a shape/key contract check only; it does not update weights and does not edit root `trainer.py`

Latest depth-metric guard result:

- `--depth_metric_crop auto` is the CLI default
- root trainer setup resolves `auto` to `kitti_eigen` for KITTI and `none` for Citrus
- `kitti_eigen` still works for KITTI-shaped `375 x 1242` depth labels
- Citrus-shaped `720 x 1280` labels now raise a clear error if `kitti_eigen` is used accidentally
- `--depth_metric_crop none` works with Citrus-shaped labels and `valid_mask`
- predicted depth is resized to the actual `depth_gt` shape before monitoring metrics are computed
- `smoke_depth_metric_guard.py` passed

Latest root Citrus trainer wiring result:

- `train.py --help` exposes `--dataset citrus`, `--split citrus_prepared`, `--citrus_prepared_name`, `--citrus_max_neighbor_delta_ms`, and `--depth_metric_crop {auto,kitti_eigen,none}`
- the smoke rejected explicit `--dataset citrus --depth_metric_crop kitti_eigen`
- root trainer auto-resolved Citrus to `split=citrus_prepared`, `data_path=citrus_project/dataset_workspace`, and `depth_metric_crop=none`
- train DataLoader loaded 4275 safe temporal Citrus samples
- validation DataLoader loaded 560 safe temporal Citrus samples
- one CPU batch passed through root `Trainer.process_batch`
- one-batch photometric loss and depth-monitor `abs_rel` were finite
- the smoke script uses a no-op TensorBoard writer because this sandbox blocks TensorBoardX multiprocessing pipes; real training still uses the normal writer
- the smoke did not perform an optimizer update

Latest root Citrus one-step training smoke result:

- one CPU Citrus batch passed through root `Trainer.process_batch`
- latest training loss was finite before backward: `0.154858`
- gradients were finite
- depth and pose AdamW optimizers completed one update
- a checked encoder parameter changed by max absolute delta `0.0000050217`
- the smoke did not save a checkpoint or start a real epoch

Latest Citrus color augmentation smoke result:

- train-mode Citrus samples apply ColorJitter-style `color_aug` when selected
- validation samples keep `color_aug` identical to `color`
- with forced train augmentation, mean absolute `color_aug - color` difference was `0.069748`
- with forced validation augmentation probability, mean absolute difference stayed `0.000000`
- root trainer passes `is_train=True` for Citrus train and `is_train=False` for Citrus validation
- `--citrus_color_aug_probability` defaults to `0.5`
- CUDA one-step smoke passed after the laptop GPU became visible:
  - device: `cuda`
  - GPU: NVIDIA GeForce RTX 4060 Laptop GPU
  - loss before update: `0.198368`
  - max checked encoder parameter delta after update: `0.0000050217`

Next technical decision:

- Milestone 2 core is complete. Next stage is Milestone 3: plan a short, controlled Citrus self-supervised adaptation run before launching longer fine-tuning.
