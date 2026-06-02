# Milestone 3: Self-Supervised Adaptation

Use this folder for milestone-specific helpers, notes, or experiment files related to:

- self-supervised Citrus training
- adaptation experiments
- comparison notes against the untouched baseline

Closeout verdict:

- Milestone 3 standard self-supervised Citrus adaptation is technically working but not useful as an improvement under the tested recipe family.
- Training runs, checkpoint saving, resume-style loading, diagnostics, and evaluation all work.
- The adapted checkpoints did not beat the untouched Milestone 1 original Lite-Mono baseline on first-100 validation relative-depth metrics.
- Longer or more conservative versions still showed relative-depth drift: the adapted model became smoother and less structurally specific.
- Use this milestone as a weak/negative adapted-baseline result and motivation for Milestone 4, not as the final improved model.

What this milestone proves:

- The Citrus self-supervised training path is operational on the laptop RTX 4060 GPU.
- Standard photometric self-supervision can reduce the image-warping game while worsening LiDAR-valid depth quality.
- Depth updates, not pose-only learning, are where the damaging behavior appears.
- Disabling color augmentation reduces the damage but does not solve it.
- A long run of this recipe family should not be launched without a new technical reason.

Next handoff:

- Move to Milestone 4 planning.
- Treat the Milestone 3 evidence as the baseline-adaptation failure case that Milestone 4 must improve on.
- Keep comparisons fair by using the same prepared Citrus split, input size, model family, and first-100/full-split evaluation protocol where practical.

Beginner-friendly companion:

- `beginner_progress_summary.md` explains the current Milestone 3 finding in plain language for student/professor discussion.

What this milestone is not:

- It is not a from-scratch training stage for the main result.
- It is not the vegetation-specific improvement yet.
- It should not launch a long training run until the exact settings are reviewed.

Safety guard:

- `train.py` now supports `--max_train_steps`.
- The default is `0`, which preserves the normal full-epoch behavior.
- Passing a positive value stops training after that many optimizer steps, even if `--num_epochs` is larger.
- Use this for smoke runs and first controlled short runs so accidental long training is harder.

Output hygiene:

- Training runs/checkpoints should go under `citrus_project/milestones/03_self_supervised_adaptation/runs/`.
- Smoke-test or short-test folders in `runs/` are disposable and can be removed or summarized later.
- The original `weights/lite-mono/` checkpoint folder is an input only; Milestone 3 should not overwrite it.

Validated tiny save-smoke command pattern:

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py `
  --dataset citrus `
  --load_weights_folder weights/lite-mono `
  --models_to_load encoder depth `
  --weights_init scratch `
  --batch_size 1 `
  --num_workers 0 `
  --num_epochs 1 `
  --max_train_steps 2 `
  --save_frequency 1 `
  --log_frequency 1 `
  --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs `
  --model_name citrus_ss_finetune_smoke_2steps_retry
```

Notes:

- Loading only `encoder depth` is intentional for the current original Lite-Mono checkpoint folder, which has depth weights but not pose weights.
- The pose network is still trained as a helper for self-supervised photometric warping.
- Runtime inference remains RGB-only depth inference through encoder + depth decoder.

Latest smoke result:

- A first attempt exposed an old validation iterator bug in `trainer.py`; `trainer.val()` now uses `next(self.val_iter)` for Python 3 / current PyTorch compatibility.
- A 2-step CUDA smoke run passed with `--max_train_steps 2`.
- That run loaded original `weights/lite-mono` `encoder` and `depth` weights only.
- It saved a new checkpoint under `runs/citrus_ss_finetune_smoke_2steps_retry/models/weights_0/`.
- Saved checkpoint files include `encoder.pth`, `depth.pth`, `pose_encoder.pth`, `pose.pth`, `adam.pth`, and `adam_pose.pth`.
- A 1-step CUDA continuation smoke then loaded that saved `weights_0` folder with `encoder depth pose_encoder pose` plus Adam states and ran one more optimizer update.
- This proves basic checkpoint loading/continuation works for disposable Milestone 3 smoke runs.
- It does not prove perfect resume of epoch/step counters, and it is not a meaningful adaptation result.

Latest 10-step smoke result:

- Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py `
  --dataset citrus `
  --load_weights_folder weights/lite-mono `
  --models_to_load encoder depth `
  --weights_init scratch `
  --batch_size 1 `
  --num_workers 0 `
  --num_epochs 1 `
  --max_train_steps 10 `
  --save_frequency 1 `
  --log_frequency 1 `
  --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs `
  --model_name citrus_ss_finetune_smoke_10steps
```

- Device: `cuda`
- Train samples: 4275
- Validation samples: 560
- Observed training losses: `0.15332`, `0.14692`, `0.17813`, `0.15330`, `0.13782`, `0.11917`, `0.10576`, `0.18068`, `0.12975`, `0.14577`
- Checkpoint saved under `runs/citrus_ss_finetune_smoke_10steps/models/weights_0/`
- Saved checkpoint files: `encoder.pth`, `depth.pth`, `pose_encoder.pth`, `pose.pth`, `adam.pth`, `adam_pose.pth`
- This is stronger smoke evidence than 1-2 steps, but still not a paper/result checkpoint.

10-step checkpoint evaluation smoke:

- Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py `
  --split val `
  --max_samples 20 `
  --run_model `
  --summary_only `
  --progress_interval 5 `
  --weights_folder citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_finetune_smoke_10steps/models/weights_0 `
  --output_dir citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_finetune_smoke_10steps/eval_smoke
```

- Evaluated 20/20 first validation samples on CUDA.
- 10-step checkpoint median-scaled metrics: `abs_rel=0.3550`, `sq_rel=0.9909`, `rmse=3.5276`, `rmse_log=0.5675`, `a1=0.4378`, `a2=0.6772`, `a3=0.7769`
- Untouched original baseline on the same first 20 validation rows: `abs_rel=0.3270`, `sq_rel=0.9529`, `rmse=3.5018`, `rmse_log=0.5294`, `a1=0.5353`, `a2=0.6953`, `a3=0.7651`
- Interpretation: evaluator plumbing works for Milestone 3 checkpoints, but the 10-step checkpoint is not improved and should stay disposable smoke evidence.

100-step pilot result:

- Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py `
  --dataset citrus `
  --load_weights_folder weights/lite-mono `
  --models_to_load encoder depth `
  --weights_init scratch `
  --batch_size 1 `
  --num_workers 0 `
  --num_epochs 1 `
  --max_train_steps 100 `
  --save_frequency 1 `
  --log_frequency 10 `
  --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs `
  --model_name citrus_ss_finetune_pilot_100steps
```

- Device: `cuda`
- Train samples: 4275
- Validation samples: 560
- Logged training losses at steps 0/10/.../90: `0.22202`, `0.11025`, `0.12028`, `0.19162`, `0.13532`, `0.13936`, `0.13084`, `0.13037`, `0.15102`, `0.17046`
- Checkpoint saved under `runs/citrus_ss_finetune_pilot_100steps/models/weights_0/`

100-step validation subset evaluation:

- Evaluated the first 100 validation samples.
- 100-step checkpoint raw metrics: `abs_rel=0.6997`, `sq_rel=2.1040`, `rmse=4.4417`, `rmse_log=1.3506`, `a1=0.0101`, `a2=0.0300`, `a3=0.0960`
- Untouched baseline raw metrics on the same first 100 samples: `abs_rel=0.7289`, `sq_rel=2.4188`, `rmse=4.8283`, `rmse_log=1.4808`, `a1=0.0131`, `a2=0.0240`, `a3=0.0399`
- 100-step checkpoint median-scaled metrics: `abs_rel=0.4713`, `sq_rel=1.9500`, `rmse=3.4260`, `rmse_log=0.6038`, `a1=0.3998`, `a2=0.6300`, `a3=0.7843`
- Untouched baseline median-scaled metrics on the same first 100 samples: `abs_rel=0.3680`, `sq_rel=0.9802`, `rmse=3.4817`, `rmse_log=0.4933`, `a1=0.4807`, `a2=0.6926`, `a3=0.8216`
- Interpretation: the checkpoint may be nudging raw absolute scale, but relative-depth quality after median scaling is worse. This is useful pilot evidence, not a usable adapted baseline.

500-step low-learning-rate pilot result:

- Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py `
  --dataset citrus `
  --load_weights_folder weights/lite-mono `
  --models_to_load encoder depth `
  --weights_init scratch `
  --batch_size 1 `
  --num_workers 0 `
  --num_epochs 1 `
  --max_train_steps 500 `
  --save_frequency 1 `
  --log_frequency 50 `
  --lr 0.00001 0.000001 31 0.00001 0.000001 31 `
  --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs `
  --model_name citrus_ss_finetune_pilot_500steps_lr1e-5
```

- Device: `cuda`
- Train samples: 4275
- Validation samples: 560
- Logged training losses at steps 0/50/.../450: `0.17496`, `0.14733`, `0.14092`, `0.11833`, `0.16756`, `0.17099`, `0.12122`, `0.13047`, `0.12928`, `0.11762`
- Checkpoint saved under `runs/citrus_ss_finetune_pilot_500steps_lr1e-5/models/weights_0/`

500-step validation subset evaluation:

- Evaluated the first 100 validation samples.
- 500-step low-LR checkpoint raw metrics: `abs_rel=0.8391`, `sq_rel=2.9672`, `rmse=5.1609`, `rmse_log=2.0988`, `a1=0.0000`, `a2=0.0004`, `a3=0.0031`
- Untouched baseline raw metrics on the same first 100 samples: `abs_rel=0.7289`, `sq_rel=2.4188`, `rmse=4.8283`, `rmse_log=1.4808`, `a1=0.0131`, `a2=0.0240`, `a3=0.0399`
- 500-step low-LR checkpoint median-scaled metrics: `abs_rel=0.4670`, `sq_rel=1.3756`, `rmse=3.9584`, `rmse_log=0.6431`, `a1=0.4340`, `a2=0.6165`, `a3=0.7104`
- Untouched baseline median-scaled metrics on the same first 100 samples: `abs_rel=0.3680`, `sq_rel=0.9802`, `rmse=3.4817`, `rmse_log=0.4933`, `a1=0.4807`, `a2=0.6926`, `a3=0.8216`
- Interpretation: lowering the learning rate and running longer did not fix the early-adaptation problem. This setup should be diagnosed before any longer training run.

Diagnostic helper:

- Script: `diagnose_self_supervised_batch.py`
- Purpose: inspect a few fixed-order train/val batches without optimizer updates.
- Reports:
  - photometric loss
  - LiDAR-valid depth-monitor metrics
  - predicted depth median
  - automask reprojection fraction
  - pose translation norm
  - warp out-of-bounds fraction

Key diagnostic findings:

- The original `weights/lite-mono/` folder has no pose checkpoint files, so Milestone 3 pilots used original depth weights but scratch pose.
- The old ImageNet pose-pretrain path currently fails with torch `2.0.1` / torchvision `0.15.2` because `torchvision.models.resnet.model_urls` is gone.
- Temporal triplets and Citrus camera intrinsics still look sane:
  - train safe triplets: `4275/4311`
  - val safe triplets: `560/564`
  - median neighboring-frame gap is about 100 ms
  - resized K starts with `fx=263.77954`, `fy=140.94998`, `cx=323.59875`, `cy=95.26605`
- The model has training-stability risks for small-batch fine-tuning:
  - depth encoder: 18 BatchNorm layers and 23 DropPath-like modules at default `--drop_path 0.2`
  - pose encoder: 20 BatchNorm layers
  - batch size 1 may make BatchNorm statistics noisy
- CUDA batch-size checks:
  - batch size 2 forward diagnostic passed
  - batch size 4 forward diagnostic passed
  - batch size 4 one-step backward/update fit check passed
- Fixed-order diagnostics show photometric loss can decrease while LiDAR-valid depth metrics get worse, so the current self-supervised loss is not yet a reliable sign that Citrus depth is improving.

Current next-step recommendation:

- Do not run a longer version of the same 500-step setup.
- First diagnose or control the likely failure points:
  - pose initialization / pose warmup
  - batch size 4 instead of batch size 1
  - BatchNorm behavior during fine-tuning
  - `--drop_path 0` for adaptation
  - possibly freezing depth briefly while pose learns motion, or freezing parts of depth to avoid damaging the pretrained geometry too quickly

Batch-size-4/drop_path-0 pilot:

- Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py `
  --dataset citrus `
  --load_weights_folder weights/lite-mono `
  --models_to_load encoder depth `
  --weights_init scratch `
  --batch_size 4 `
  --num_workers 0 `
  --num_epochs 1 `
  --max_train_steps 125 `
  --save_frequency 1 `
  --log_frequency 25 `
  --drop_path 0 `
  --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs `
  --model_name citrus_ss_finetune_pilot_bs4_dp0_125steps
```

- Intent: use existing settings only, with larger batch and no DropPath. At batch size 4, 125 optimizer steps sees about 500 training images.
- Device: `cuda`
- Logged training losses at steps 0/25/50/75/100: `0.16866`, `0.15581`, `0.11837`, `0.15694`, `0.13407`
- Checkpoint saved under `runs/citrus_ss_finetune_pilot_bs4_dp0_125steps/models/weights_0/`

Batch-size-4/drop_path-0 validation subset evaluation:

- Evaluated the first 100 validation samples.
- Raw metrics improved versus the untouched baseline: `abs_rel=0.6906`, `rmse=3.5818`, `a1=0.0993`
- Untouched baseline raw metrics on the same first 100 samples: `abs_rel=0.7289`, `rmse=4.8283`, `a1=0.0131`
- Median-scaled metrics collapsed versus the untouched baseline: `abs_rel=0.8251`, `rmse=5.8311`, `a1=0.2108`
- Untouched baseline median-scaled metrics on the same first 100 samples: `abs_rel=0.3680`, `rmse=3.4817`, `a1=0.4807`
- Interpretation: this recipe improves broad absolute-scale behavior but damages relative depth structure badly. Batch size and DropPath controls alone are not enough.

## Milestone 3 Depth-Freeze Smoke

Date: 2026-05-06

Paper relevance: engineering control only. This is not an adapted model result.

Purpose: add and verify a small pose-warmup lever. In plain terms, this lets the pose network learn camera motion for a few steps while the pretrained depth weights are protected from optimizer updates.

### New Option

- `--freeze_depth_steps N`
- Default: `0`, which preserves the existing training behavior.
- When `N > 0`, `trainer.py` skips depth optimizer updates for the first `N` training steps.
- Pose optimizer updates still run during those frozen steps.

### Smoke Command

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init scratch --batch_size 4 --num_workers 0 --num_epochs 1 --max_train_steps 2 --freeze_depth_steps 2 --save_frequency 1 --log_frequency 1 --drop_path 0 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name citrus_ss_freeze_depth_smoke_2steps
```

### Result

- Device: `cuda`
- Logged losses at steps 0 and 1: `0.16873`, `0.15694`
- Checkpoint saved under `runs/citrus_ss_freeze_depth_smoke_2steps/models/weights_0/`
- Encoder/depth trainable tensors changed `0` versus original `weights/lite-mono`.
- Depth Adam state entries: `0`
- Pose Adam state entries: `68`, max step: `2`
- Encoder BatchNorm running-stat buffers changed, which is expected because the model still ran forward in train mode.

### Interpretation

The switch works: it protects trainable depth parameters while pose updates. It does not prove adaptation improves yet. The next controlled pilot can test whether a short pose warmup plus batch size 4 and `--drop_path 0` avoids damaging relative depth structure, but that should be confirmed before running.

## Pose Pretraining Compatibility Fix

Date: 2026-05-06

Paper relevance: engineering unblocker only. This is not an adapted model result.

Purpose: repair the ImageNet-pretrained pose encoder path before testing whether pose starts better than scratch.

### Problem

The old Lite-Mono code used:

```text
torchvision.models.resnet.model_urls
```

The local environment uses torch `2.0.1` and torchvision `0.15.2`, where that old `model_urls` attribute no longer exists.

### Fix

`networks/resnet_encoder.py` now:

- uses modern torchvision ResNet weight enums when available
- keeps the old `model_urls` path as fallback for older torchvision versions
- still supports scratch ResNet construction

The standard ResNet-18 ImageNet checkpoint was downloaded after approval to:

```text
C:/Users/user/.cache/torch/hub/checkpoints/resnet18-f37072fd.pth
```

### Smoke Checks

No Citrus training was run in this slice.

- `ResnetEncoder(18, True, num_input_images=2)` built and forwarded a fake `[1, 6, 192, 640]` tensor.
- `ResnetEncoder(18, True, num_input_images=1)` built and forwarded a fake `[1, 3, 192, 640]` tensor.
- Both produced the expected feature pyramid shapes:

```text
[(1, 64, 96, 320), (1, 64, 48, 160), (1, 128, 24, 80), (1, 256, 12, 40), (1, 512, 6, 20)]
```

### Interpretation

The pose-pretrain API crash is fixed at the encoder level. The root trainer smoke below now verifies the repaired path inside the full Citrus trainer before any longer pilot.

## Root Trainer Pretrained-Pose Smoke

Date: 2026-05-06

Paper relevance: engineering smoke only. This is not an adapted model result.

Purpose: verify that the repaired pose-pretrain path works inside the full Citrus `train.py` route.

### Command

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init pretrained --batch_size 4 --num_workers 0 --num_epochs 1 --max_train_steps 1 --save_frequency 1 --log_frequency 1 --drop_path 0 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name citrus_ss_pretrained_pose_smoke_1step
```

### Result

- Device: `cuda`
- Train samples: `4275`
- Validation samples: `560`
- Step-0 loss: `0.16363`
- `--max_train_steps=1` stopped training as intended.
- Checkpoint saved under `runs/citrus_ss_pretrained_pose_smoke_1step/models/weights_0/`
- Saved checkpoint files include `encoder.pth`, `depth.pth`, `pose_encoder.pth`, `pose.pth`, `adam.pth`, and `adam_pose.pth`.
- `models/opt.json` records `weights_init=pretrained`, `batch_size=4`, `drop_path=0.0`, and `depth_metric_crop=none`.
- Depth optimizer state entries: `197`, max step `1`
- Pose optimizer state entries: `68`, max step `1`

### Interpretation

The full trainer can now use ImageNet-pretrained pose ResNet weights with Citrus. This only proves the route works technically; it does not prove better adaptation yet.

## Pretrained-Pose Depth-Frozen Warmup Pilot

Date: 2026-05-06

Paper relevance: tiny pilot evidence only. This is not a final adapted model.

Purpose: test whether pretrained pose can warm up for a few steps without damaging the original depth model. Depth optimizer updates were frozen for the whole 25-step run.

### Training Command

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init pretrained --batch_size 4 --num_workers 0 --num_epochs 1 --max_train_steps 25 --freeze_depth_steps 25 --save_frequency 1 --log_frequency 5 --drop_path 0 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name citrus_ss_pretrained_pose_warmup_25steps
```

### Training Result

- Device: `cuda`
- Batch size: `4`
- Training images seen: about `100`
- Logged losses at steps 0/5/10/15/20: `0.17810`, `0.13715`, `0.14609`, `0.14938`, `0.14692`
- Checkpoint saved under `runs/citrus_ss_pretrained_pose_warmup_25steps/models/weights_0/`
- Encoder/depth trainable tensors changed `0` versus original `weights/lite-mono`.
- Depth Adam state entries: `0`
- Pose Adam state entries: `68`, max step: `25`
- Encoder BatchNorm running-stat buffers changed, because the depth encoder still ran in train mode.

### First-100 Validation Evaluation

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 100 --run_model --summary_only --progress_interval 25 --weights_folder citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_pretrained_pose_warmup_25steps/models/weights_0 --output_dir citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_pretrained_pose_warmup_25steps/eval_val100
```

Same first 100 validation samples:

- untouched original baseline median-scaled: `abs_rel=0.3680`, `sq_rel=0.9802`, `rmse=3.4817`, `rmse_log=0.4933`, `a1=0.4807`, `a2=0.6926`, `a3=0.8216`
- 25-step depth-frozen warmup median-scaled: `abs_rel=0.3777`, `sq_rel=1.2055`, `rmse=3.4646`, `rmse_log=0.4792`, `a1=0.4773`, `a2=0.7158`, `a3=0.8536`
- untouched original baseline raw-scale: `abs_rel=0.7289`, `sq_rel=2.4188`, `rmse=4.8283`, `rmse_log=1.4808`, `a1=0.0131`, `a2=0.0240`, `a3=0.0399`
- 25-step depth-frozen warmup raw-scale: `abs_rel=0.7280`, `sq_rel=2.3298`, `rmse=4.7374`, `rmse_log=1.4305`, `a1=0.0084`, `a2=0.0193`, `a3=0.0379`

### Interpretation

This tiny run did not collapse relative depth the way the earlier depth-updating batch-size-4/drop_path-0 pilot did. Because depth trainable weights were frozen, this is not an adaptation improvement yet. It mainly suggests the next controlled pilot can allow depth to update after a short pretrained-pose warmup.

## Pretrained-Pose Warmup Then Depth-Update Pilot

Date: 2026-05-06

Paper relevance: tiny pilot evidence only. This is not a final adapted baseline.

Purpose: test the next small step after the depth-frozen warmup: protect depth for 25 steps, then allow depth and pose to update together for 25 steps.

### Training Command

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init pretrained --batch_size 4 --num_workers 0 --num_epochs 1 --max_train_steps 50 --freeze_depth_steps 25 --save_frequency 1 --log_frequency 10 --drop_path 0 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name citrus_ss_pretrained_pose_warmup25_depth25_50steps
```

### Training Result

- Device: `cuda`
- Batch size: `4`
- Training images seen: about `200`
- Logged losses at steps 0/10/20/30/40: `0.16001`, `0.14923`, `0.16219`, `0.14194`, `0.13426`
- Checkpoint saved under `runs/citrus_ss_pretrained_pose_warmup25_depth25_50steps/models/weights_0/`
- Encoder trainable tensors changed: `179`, max trainable diff `0.0021548`
- Depth decoder trainable tensors changed: `18`, max trainable diff `0.0020552`
- Depth Adam state entries: `197`, max step `25`
- Pose Adam state entries: `68`, max step `50`

### First-100 Validation Evaluation

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 100 --run_model --summary_only --progress_interval 25 --weights_folder citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_pretrained_pose_warmup25_depth25_50steps/models/weights_0 --output_dir citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_pretrained_pose_warmup25_depth25_50steps/eval_val100
```

Same first 100 validation samples:

- untouched original baseline median-scaled: `abs_rel=0.3680`, `sq_rel=0.9802`, `rmse=3.4817`, `rmse_log=0.4933`, `a1=0.4807`, `a2=0.6926`, `a3=0.8216`
- 50-step warmup-then-depth median-scaled: `abs_rel=0.5766`, `sq_rel=3.2984`, `rmse=4.3728`, `rmse_log=0.6083`, `a1=0.3135`, `a2=0.5977`, `a3=0.7692`
- untouched original baseline raw-scale: `abs_rel=0.7289`, `sq_rel=2.4188`, `rmse=4.8283`, `rmse_log=1.4808`, `a1=0.0131`, `a2=0.0240`, `a3=0.0399`
- 50-step warmup-then-depth raw-scale: `abs_rel=0.4946`, `sq_rel=1.5059`, `rmse=4.0153`, `rmse_log=0.8167`, `a1=0.1872`, `a2=0.3402`, `a3=0.5300`
- median scale ratio changed from `3.836987` for the untouched first-100 baseline to `1.678844` after this run.

### Interpretation

This run improved broad raw-scale alignment but worsened median-scaled relative-depth structure. In plain terms, the model moved toward better overall distance scale but damaged the inside-image depth pattern we care about for vegetation. This recipe should not be scaled directly to a longer run without another control for relative-structure damage.

## Low-Depth-LR Warmup Then Depth-Update Pilot

Date: 2026-05-06

Paper relevance: tiny pilot evidence only. This is not a final adapted baseline.

Purpose: test whether the previous run damaged relative structure because depth was updating too aggressively. This repeats the 50-step structure but lowers depth LR from `1e-4` to `1e-5`; pose LR stays `1e-4`.

### Training Command

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init pretrained --batch_size 4 --num_workers 0 --num_epochs 1 --max_train_steps 50 --freeze_depth_steps 25 --save_frequency 1 --log_frequency 10 --drop_path 0 --lr 0.00001 0.0000005 31 0.0001 0.00001 31 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name citrus_ss_pretrained_pose_warmup25_depth25_50steps_depthlr1e-5
```

### Training Result

- Device: `cuda`
- Batch size: `4`
- Training images seen: about `200`
- Logged losses at steps 0/10/20/30/40: `0.13880`, `0.14841`, `0.13287`, `0.14273`, `0.16145`
- Checkpoint saved under `runs/citrus_ss_pretrained_pose_warmup25_depth25_50steps_depthlr1e-5/models/weights_0/`
- Encoder trainable tensors changed: `179`, max trainable diff `0.0002324`
- Depth decoder trainable tensors changed: `18`, max trainable diff `0.0002227`
- Depth Adam state entries: `197`, max step `25`
- Pose Adam state entries: `68`, max step `50`

### First-100 Validation Evaluation

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 100 --run_model --summary_only --progress_interval 25 --weights_folder citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_pretrained_pose_warmup25_depth25_50steps_depthlr1e-5/models/weights_0 --output_dir citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_pretrained_pose_warmup25_depth25_50steps_depthlr1e-5/eval_val100
```

Same first 100 validation samples:

- untouched original baseline median-scaled: `abs_rel=0.3680`, `sq_rel=0.9802`, `rmse=3.4817`, `rmse_log=0.4933`, `a1=0.4807`, `a2=0.6926`, `a3=0.8216`
- low-depth-LR 50-step median-scaled: `abs_rel=0.4271`, `sq_rel=1.1995`, `rmse=3.5924`, `rmse_log=0.5483`, `a1=0.4526`, `a2=0.6394`, `a3=0.7698`
- untouched original baseline raw-scale: `abs_rel=0.7289`, `sq_rel=2.4188`, `rmse=4.8283`, `rmse_log=1.4808`, `a1=0.0131`, `a2=0.0240`, `a3=0.0399`
- low-depth-LR 50-step raw-scale: `abs_rel=0.7790`, `sq_rel=2.6595`, `rmse=4.9690`, `rmse_log=1.7249`, `a1=0.0099`, `a2=0.0172`, `a3=0.0243`
- median scale ratio changed to `5.129785`, compared with `3.836987` for the untouched first-100 baseline.

### Interpretation

Lowering depth LR reduced weight movement and avoided the severe median-scaled collapse of the normal-depth-LR 50-step pilot, but it also lost the raw-scale improvement. It still trails the untouched baseline on the first 100 validation samples, so low depth LR alone is not enough.

## Fixed-Batch Internal Diagnostics

Date: 2026-05-06

Paper relevance: diagnostic evidence only. This helps choose the next recipe; it is not a final comparison.

Purpose: inspect the same fixed train/validation batches across recent checkpoints to see what changed inside training.

### Compared Checkpoints

- original `weights/lite-mono`
- `citrus_ss_pretrained_pose_warmup_25steps`
- `citrus_ss_pretrained_pose_warmup25_depth25_50steps`
- `citrus_ss_pretrained_pose_warmup25_depth25_50steps_depthlr1e-5`

Diagnostic outputs were saved under:

```text
runs/diagnostics_fixed_m3_internal_compare/
```

### Validation Batch Summary

Fixed first 5 validation batches:

| checkpoint | photo loss | LiDAR abs_rel | LiDAR a1 | depth median | pose trans |
|---|---:|---:|---:|---:|---:|
| original | 0.170072 | 0.219713 | 0.676611 | 0.540391 | 0.000517 |
| 25-step depth frozen | 0.151223 | 0.231445 | 0.631453 | 0.535836 | 0.007553 |
| 50-step normal depth LR | 0.146895 | 0.430942 | 0.198302 | 1.132429 | 0.007778 |
| 50-step low depth LR | 0.145763 | 0.267062 | 0.542943 | 0.407042 | 0.003881 |

### Interpretation

The self-supervised photo loss improves in every adapted checkpoint, even when LiDAR-valid depth metrics get worse. The normal-depth-LR run strongly shifts predicted depth median and damages relative depth quality. The low-depth-LR run reduces the damage but still does not beat the untouched baseline.

Practical conclusion: do not scale these recipes yet. The next controlled recipe should preserve pretrained depth structure more explicitly, likely by freezing the depth encoder/BatchNorm and only updating the depth decoder after pose warmup.

## Depth-Encoder Freeze And Decoder-Only Pilot

Date: 2026-05-06

Paper relevance: tiny pilot evidence only. This is not a final adapted baseline.

Purpose: test whether protecting the pretrained depth encoder and BatchNorm running statistics prevents the relative-depth damage seen when all depth parameters update.

### New Option

- `--freeze_depth_encoder`
- Default: off
- When enabled:
  - depth encoder weights are removed from the depth optimizer
  - depth encoder parameters have `requires_grad=False`
  - depth encoder is forced back to eval mode during training so BatchNorm running statistics do not change
  - depth decoder remains trainable after any `--freeze_depth_steps` warmup

The diagnostic helper also accepts `--freeze_depth_encoder` so decoder-only checkpoints can be inspected with the matching optimizer shape.

### Training Command

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init pretrained --batch_size 4 --num_workers 0 --num_epochs 1 --max_train_steps 50 --freeze_depth_steps 25 --freeze_depth_encoder --save_frequency 1 --log_frequency 10 --drop_path 0 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name citrus_ss_pretrained_pose_warmup25_decoder25_50steps
```

### Training Result

- Device: `cuda`
- Batch size: `4`
- Training images seen: about `200`
- Logged losses at steps 0/10/20/30/40: `0.14691`, `0.13939`, `0.15326`, `0.12439`, `0.13115`
- Checkpoint saved under `runs/citrus_ss_pretrained_pose_warmup25_decoder25_50steps/models/weights_0/`
- Encoder trainable tensors changed: `0`
- Encoder BatchNorm buffers changed: `0`
- Depth decoder trainable tensors changed: `18`, max diff `0.0022011`
- Depth Adam state entries: `18`, max step `25`
- Pose Adam state entries: `68`, max step `50`

### First-100 Validation Evaluation

Same first 100 validation samples:

- untouched original baseline median-scaled: `abs_rel=0.3680`, `sq_rel=0.9802`, `rmse=3.4817`, `rmse_log=0.4933`, `a1=0.4807`, `a2=0.6926`, `a3=0.8216`
- decoder-only 50-step median-scaled: `abs_rel=0.4700`, `sq_rel=1.3546`, `rmse=3.8739`, `rmse_log=0.6242`, `a1=0.4195`, `a2=0.6140`, `a3=0.7202`
- untouched original baseline raw-scale: `abs_rel=0.7289`, `sq_rel=2.4188`, `rmse=4.8283`, `rmse_log=1.4808`, `a1=0.0131`, `a2=0.0240`, `a3=0.0399`
- decoder-only 50-step raw-scale: `abs_rel=0.7373`, `sq_rel=2.5788`, `rmse=4.9783`, `rmse_log=1.6191`, `a1=0.0035`, `a2=0.0133`, `a3=0.0410`

### Fixed-Batch Diagnostics

Fixed first 5 validation batches:

| checkpoint | photo loss | LiDAR abs_rel | LiDAR a1 | depth median | pose trans |
|---|---:|---:|---:|---:|---:|
| original | 0.170072 | 0.219713 | 0.676611 | 0.540391 | 0.000517 |
| 50-step normal depth LR | 0.146895 | 0.430942 | 0.198302 | 1.132429 | 0.007778 |
| 50-step low depth LR | 0.145763 | 0.267062 | 0.542943 | 0.407042 | 0.003881 |
| decoder-only encoder frozen | 0.147945 | 0.300943 | 0.464280 | 0.491805 | 0.002778 |

### Interpretation

The encoder freeze worked mechanically: no encoder weights or BatchNorm buffers changed. The result still worsened on the first 100 validation samples, so encoder/BatchNorm drift is not the only problem. Decoder-only adaptation looks less bad than full-depth normal LR on tiny fixed diagnostics, but it is still not enough for a usable adapted baseline.

## Previous-Only Temporal Source Pilot

Date: 2026-05-06

Paper relevance: tiny pilot evidence only. This is not a final adapted baseline.

Purpose: test whether the next temporal frame was hurting self-supervised training. Diagnostics showed the next frame often had higher warp out-of-bounds and weaker photo margin in the hardest-failing runs.

### Direction Diagnostic Clue

For the 50-step normal-depth-LR validation diagnostics:

```text
previous frame margin: 0.006716
next frame margin:     0.001326
previous frame OOB:    0.034774
next frame OOB:        0.073470
```

So the next frame looked suspicious enough to test previous-only training.

### Training Command

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init pretrained --batch_size 4 --num_workers 0 --num_epochs 1 --max_train_steps 50 --freeze_depth_steps 25 --save_frequency 1 --log_frequency 10 --drop_path 0 --frame_ids 0 -1 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name citrus_ss_prev_only_warmup25_depth25_50steps
```

### Training Result

- Device: `cuda`
- Frame ids: `[0, -1]`
- Train samples: `4293`
- Validation samples: `562`
- Logged losses at steps 0/10/20/30/40: `0.20427`, `0.17235`, `0.16810`, `0.19260`, `0.18150`
- Depth Adam max step: `25`
- Pose Adam max step: `50`

### First-100 Validation Evaluation

Same first 100 validation samples:

- untouched original baseline median-scaled: `abs_rel=0.3680`, `sq_rel=0.9802`, `rmse=3.4817`, `rmse_log=0.4933`, `a1=0.4807`, `a2=0.6926`, `a3=0.8216`
- previous-only 50-step median-scaled: `abs_rel=0.4809`, `sq_rel=1.3094`, `rmse=3.8513`, `rmse_log=0.6302`, `a1=0.3632`, `a2=0.5712`, `a3=0.7016`
- untouched original baseline raw-scale: `abs_rel=0.7289`, `sq_rel=2.4188`, `rmse=4.8283`, `rmse_log=1.4808`, `a1=0.0131`, `a2=0.0240`, `a3=0.0399`
- previous-only 50-step raw-scale: `abs_rel=0.7537`, `sq_rel=2.6378`, `rmse=4.9996`, `rmse_log=1.6835`, `a1=0.0064`, `a2=0.0133`, `a3=0.0331`

### Interpretation

Dropping the next frame did not fix the problem. Previous-only self-supervision worsened both raw and median-scaled first-100 validation metrics versus the untouched baseline. Temporal source direction alone is not the missing ingredient.

## Loss-Decomposition Diagnostic

Date: 2026-05-06

Paper relevance: diagnostic evidence only. This does not add a new loss or train a new model.

Purpose: inspect why photo loss can improve while LiDAR-valid depth metrics get worse. The diagnostic helper now recomputes existing Lite-Mono loss pieces without optimizer updates:

- selected photo loss
- weighted smoothness loss
- smoothness fraction of scale-0 loss
- identity-image minimum loss
- warped-image reprojection minimum loss
- automask selected-warp fraction
- previous-vs-next source selection fraction

The helper also now supports:

- `--weights_init`, so original depth weights can be diagnosed with the same pretrained-pose construction used by later pilots
- `--frame_ids`, so previous-only checkpoints can be diagnosed with their matching source-frame setup
- deterministic `--seed`, default `0`
- no-op `Trainer.save_opts()` monkeypatch, so diagnostics do not create Trainer option folders unless `--output_dir` is explicitly requested

Saved outputs:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/diagnostics_loss_decomposition_2026-05-06/
```

Fixed first 5 validation batches:

| checkpoint | selected photo | smooth weighted | automask warp frac | reproj min | depth median | LiDAR abs_rel | LiDAR a1 | prev/next selected |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| original depth + pretrained pose init | 0.180666 | 0.000012 | 0.702305 | 0.187102 | 0.540391 | 0.219713 | 0.676611 | 0.501 / 0.499 |
| 25-step depth-frozen warmup | 0.151193 | 0.000014 | 0.450563 | 0.199916 | 0.535836 | 0.231445 | 0.631453 | 0.507 / 0.493 |
| 50-step normal depth LR | 0.146830 | 0.000023 | 0.513703 | 0.188075 | 1.132429 | 0.430942 | 0.198302 | 0.505 / 0.495 |
| 50-step low depth LR | 0.145735 | 0.000012 | 0.517715 | 0.187017 | 0.407042 | 0.267062 | 0.542943 | 0.506 / 0.494 |
| 50-step decoder-only | 0.147996 | 0.000010 | 0.524753 | 0.191255 | 0.491805 | 0.300943 | 0.464280 | 0.502 / 0.498 |
| 50-step previous-only | 0.192904 | 0.000011 | 0.501976 | 0.251292 | 0.507625 | 0.332617 | 0.463598 | 1.000 / n/a |

Interpretation:

- Smoothness is tiny compared with selected photo loss, so the immediate failure is not smoothness overpowering the objective.
- Previous and next source selection is balanced in normal two-frame runs, so source direction alone is not the explanation.
- The 25-step depth-frozen warmup lowers selected photo loss mainly by changing pose/mask behavior while depth stays near the original median.
- Once depth updates, similar photo-loss improvements can come with very different depth medians. Normal depth LR shifts the depth median high (`1.132429`), while low depth LR shifts it low (`0.407042`).
- This supports the current failure hypothesis: the self-supervised photo objective has scale/structure freedom on Citrus. It can find warps that reduce image mismatch without preserving LiDAR-valid vegetation depth quality.

Next technical direction:

- Do not scale these recipes into longer training.
- Before inventing a new method, inspect whether a Milestone 3 adaptation baseline can use a conservative, standard control such as freezing depth longer or monitoring early-stop depth drift.
- If the only working fix requires a new structure-preserving term, treat that as a Milestone 4 improvement rather than the core Milestone 3 adapted-baseline recipe.

## Pose-Only / Depth-Frozen Controls

Date: 2026-05-06

Paper relevance: diagnostic control evidence only. These are not final adapted depth models because pose is not used during RGB-only depth inference.

Purpose: test whether the bad Milestone 3 pilots are caused by depth updates, BatchNorm drift, or pose-only learning.

### Control A: Depth Optimizer Frozen, Encoder BatchNorm Allowed To Drift

Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init pretrained --batch_size 4 --num_workers 0 --num_epochs 1 --max_train_steps 50 --freeze_depth_steps 50 --save_frequency 1 --log_frequency 10 --drop_path 0 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name citrus_ss_pretrained_pose_depthfrozen_50steps
```

Result:

- 50 CUDA optimizer steps completed.
- Depth optimizer updates were frozen until step 50, then `--max_train_steps=50` stopped the run.
- Encoder trainable tensors changed: `0`.
- Depth decoder tensors changed: `0`.
- Encoder BatchNorm buffers changed: `54`, because the encoder still ran in train mode.

First 100 validation samples:

- untouched original baseline median-scaled: `abs_rel=0.3680`, `rmse=3.4817`, `a1=0.4807`
- depth-frozen 50-step median-scaled: `abs_rel=0.3810`, `rmse=3.4595`, `a1=0.4691`
- untouched original baseline raw-scale: `abs_rel=0.7289`, `rmse=4.8283`, `a1=0.0131`
- depth-frozen 50-step raw-scale: `abs_rel=0.7283`, `rmse=4.7322`, `a1=0.0079`

### Control B: Depth Encoder/BatchNorm Frozen And Depth Optimizer Frozen

Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init pretrained --batch_size 4 --num_workers 0 --num_epochs 1 --max_train_steps 50 --freeze_depth_steps 50 --freeze_depth_encoder --save_frequency 1 --log_frequency 10 --drop_path 0 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name citrus_ss_pretrained_pose_depthencoderfrozen_depthfrozen_50steps
```

Result:

- 50 CUDA optimizer steps completed.
- Encoder tensors changed: `0`.
- Depth decoder tensors changed: `0`.
- First-100 validation metrics matched the untouched baseline exactly.

First 100 validation samples:

- fully depth-frozen control median-scaled: `abs_rel=0.3680`, `rmse=3.4817`, `a1=0.4807`
- fully depth-frozen control raw-scale: `abs_rel=0.7289`, `rmse=4.8283`, `a1=0.0131`

### Fixed-Batch Diagnostic Comparison

Additional saved diagnostics:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/diagnostics_loss_decomposition_2026-05-06/
```

Fixed first 5 validation batches:

| checkpoint | selected photo | depth median | LiDAR abs_rel | LiDAR a1 | pose trans | next OOB |
|---|---:|---:|---:|---:|---:|---:|
| original depth + pretrained pose init | 0.180666 | 0.540391 | 0.219713 | 0.676611 | 0.000318 | 0.007679 |
| depth frozen 50, BN drift allowed | 0.148836 | 0.533799 | 0.236576 | 0.620472 | 0.006516 | 0.084202 |
| depth encoder frozen + depth frozen 50 | 0.143025 | 0.540391 | 0.219713 | 0.676611 | 0.010937 | 0.128975 |
| 50-step normal depth LR | 0.146830 | 1.132429 | 0.430942 | 0.198302 | 0.007778 | 0.073470 |
| 50-step low depth LR | 0.145735 | 0.407042 | 0.267062 | 0.542943 | 0.003881 | 0.046489 |
| 50-step decoder-only | 0.147996 | 0.491805 | 0.300943 | 0.464280 | 0.002778 | 0.020229 |

Interpretation:

- Pose-only training can reduce selected photo loss substantially.
- If the entire depth path is frozen, RGB-only depth inference is unchanged, so validation metrics exactly match the original baseline.
- If only depth optimizer steps are frozen but encoder BatchNorm is allowed to drift, validation changes slightly but does not collapse.
- The larger failures appear when trainable depth parameters update.
- This strengthens the current diagnosis: Milestone 3's hard part is not pose learning by itself; it is finding a depth adaptation recipe that improves Citrus without letting photo-loss-driven scale/structure drift damage LiDAR-valid depth quality.

## Seeded Warmup-Then-Depth Trajectory

Date: 2026-05-06

Paper relevance: diagnostic trajectory evidence only. This is not a final adapted baseline.

Purpose: test whether the bad direction appears only because previous runs were too short or whether it starts soon after depth updates begin.

Code/config note:

- Added default-off `--seed` to `options.py`.
- `trainer.py` seeds Python, NumPy, Torch, and CUDA when `--seed` is provided.
- Default behavior is unchanged when `--seed` is not used.

Shared trajectory settings:

- `--seed 0`
- `--weights_init pretrained`
- `--batch_size 4`
- `--drop_path 0`
- `--freeze_depth_steps 25`
- first-100 validation evaluation after each checkpoint

Commands used the same pattern, varying only `--max_train_steps` and `--model_name`:

```powershell
D:/Conda_Envs/lite-mono/python.exe train.py --dataset citrus --load_weights_folder weights/lite-mono --models_to_load encoder depth --weights_init pretrained --batch_size 4 --num_workers 0 --num_epochs 1 --seed 0 --max_train_steps <25|30|40|50> --freeze_depth_steps 25 --save_frequency 1 --log_frequency <5|10> --drop_path 0 --log_dir citrus_project/milestones/03_self_supervised_adaptation/runs --model_name <run_name>
```

Saved runs:

- `citrus_ss_seed0_warmup25_depth0_25steps`
- `citrus_ss_seed0_warmup25_depth5_30steps`
- `citrus_ss_seed0_warmup25_depth15_40steps`
- `citrus_ss_seed0_warmup25_depth25_50steps`

Saved diagnostics:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/diagnostics_seed0_warmup25_trajectory_2026-05-06/
```

First 100 validation samples:

| checkpoint | depth update steps | raw abs_rel | median-scaled abs_rel | median-scaled a1 | median scale ratio | diagnostic photo | diagnostic depth median |
|---|---:|---:|---:|---:|---:|---:|---:|
| untouched baseline | n/a | 0.7289 | 0.3680 | 0.4807 | 3.944117 | n/a | n/a |
| seed0 depth0/25 | 0 | 0.7274 | 0.3758 | 0.4797 | 3.885954 | 0.150719 | 0.531425 |
| seed0 depth5/30 | 5 | 0.6781 | 0.3902 | 0.4484 | 3.400892 | 0.148396 | 0.618594 |
| seed0 depth15/40 | 15 | 0.6697 | 0.4409 | 0.3908 | 3.271431 | 0.147801 | 0.694628 |
| seed0 depth25/50 | 25 | 0.7901 | 0.6354 | 0.2280 | 5.559390 | 0.150593 | 0.416658 |

Interpretation:

- The 25-step pose-warmup-only point stayed close to the untouched baseline.
- After only 5 depth-update steps, raw `abs_rel` improved but median-scaled relative-depth metrics already worsened.
- After 15 depth-update steps, the same tradeoff became stronger.
- After 25 depth-update steps, both raw and median-scaled metrics were much worse in this seeded trajectory.
- This does not prove a long run can never recover, but it does show that the harmful direction begins quickly after depth updates start. A longer run with the same recipe is therefore risky unless it includes monitoring and early stopping or a better depth-preservation control.

Current conclusion:

Milestone 3 has not yet found a useful standard self-supervised adaptation baseline. The strongest evidence now points to depth-update instability under the Citrus self-supervised photo objective, not a simple pose-only, smoothness, source-frame, or BatchNorm issue.

## Terminal-Controlled Conservative 1-Epoch Probe

Date prepared: 2026-05-06

Purpose: let the user run the next controlled probe from a normal PowerShell terminal, so the GPU job does not depend on the chat session staying connected.

This is not the full 30-epoch training plan. It is one monitored Citrus epoch capped at 1000 optimizer steps. The goal is to answer a narrower question: if we use the most conservative standard recipe tried so far, does a longer run begin to recover, or does the depth metric drift continue?

Runner scripts:

- `run_controlled_decoderonly_lowdepthlr_1epoch.ps1`
- `evaluate_controlled_decoderonly_lowdepthlr.ps1`

Shared training recipe:

```powershell
powershell -ExecutionPolicy Bypass -File citrus_project/milestones/03_self_supervised_adaptation/run_controlled_decoderonly_lowdepthlr_1epoch.ps1
```

What the recipe does:

- starts from original `weights/lite-mono` encoder/depth weights
- keeps the original checkpoint folder input-only
- uses pretrained pose initialization
- uses batch size 4, seed 0, and drop path 0
- freezes depth optimizer updates for the first 25 steps while pose adapts
- freezes the depth encoder and its BatchNorm statistics
- only lets the depth decoder update after the warmup
- uses low depth learning rate: `1e-5` to `5e-7`
- keeps pose learning rate at the normal scale: `1e-4` to `1e-5`
- caps the run at 1000 steps within one epoch
- saves step checkpoints every 250 steps with `--save_step_frequency 250`

Expected checkpoint folders:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/models/step_250/
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/models/step_500/
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/models/step_750/
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/models/step_1000/
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/models/weights_0/
```

Evaluation after training:

```powershell
powershell -ExecutionPolicy Bypass -File citrus_project/milestones/03_self_supervised_adaptation/evaluate_controlled_decoderonly_lowdepthlr.ps1
```

To evaluate a mid-run checkpoint instead of the final checkpoint:

```powershell
powershell -ExecutionPolicy Bypass -File citrus_project/milestones/03_self_supervised_adaptation/evaluate_controlled_decoderonly_lowdepthlr.ps1 -CheckpointName step_250
```

Interruption note:

- If the chat disconnects, the terminal training process can continue independently.
- If the terminal/PC is stopped after a step checkpoint is written, that checkpoint can still be evaluated.
- Exact resume of optimizer/scheduler position is still approximate in the current root trainer; for this probe, the step checkpoints are mainly for safety and intermediate evidence, not a promise of bit-exact continuation.

Result checked: 2026-05-07

Training status:

- The terminal run finished cleanly on CUDA.
- It stopped because it reached the planned `--max_train_steps=1000` limit.
- Runtime from the training log was about 16.5 minutes to the last logged step.
- Checkpoints were saved at `step_250`, `step_500`, `step_750`, `step_1000`, and final `weights_0`.
- `step_1000` and `weights_0` have identical `encoder.pth`, `depth.pth`, `pose_encoder.pth`, and `pose.pth` hashes, so `weights_0` is the final 1000-step model.

Saved first-100 validation evaluations:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/eval_val100_step_250/
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/eval_val100_step_500/
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/eval_val100_step_750/
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/eval_val100_weights_0/
```

First 100 validation samples:

| checkpoint | raw abs_rel | median-scaled abs_rel | median-scaled a1 | median scale ratio |
|---|---:|---:|---:|---:|
| untouched baseline | 0.7289 | 0.3680 | 0.4807 | 3.944117 |
| conservative step 250 | 0.7331 | 0.4542 | 0.4290 | 4.339389 |
| conservative step 500 | 0.7458 | 0.6325 | 0.2445 | 4.897573 |
| conservative step 750 | 0.7332 | 0.6152 | 0.2366 | 4.618348 |
| conservative final/1000 | 0.7448 | 0.6615 | 0.1827 | 4.860058 |

Interpretation:

- This conservative near-epoch probe did not recover.
- Step 250 was already worse than the untouched baseline on median-scaled relative-depth metrics.
- By step 500 and later, relative-depth quality was much worse.
- Raw-scale metrics also did not beat the untouched baseline.
- This strengthens the current Milestone 3 diagnosis: even with frozen encoder/BatchNorm, low depth LR, and decoder-only depth updates, the standard Citrus self-supervised objective still moves the depth decoder in a direction that hurts LiDAR-valid depth quality.

## Original-Versus-Adapted Visual Comparison

Date: 2026-05-07

Purpose: inspect what the 1000-step adapted checkpoint gets wrong visually, instead of relying only on aggregate metrics.

Helper added:

```text
citrus_project/milestones/03_self_supervised_adaptation/compare_original_vs_adapted_visuals.py
```

Command:

```powershell
D:/Conda_Envs/lite-mono/python.exe -u citrus_project/milestones/03_self_supervised_adaptation/compare_original_vs_adapted_visuals.py
```

Saved outputs:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/visual_compare_original_vs_adapted_val100_weights_0/
```

Panels generated:

- `adapted_good_index_0012_comparison.png`
- `adapted_typical_index_0036_comparison.png`
- `adapted_bad_index_0075_comparison.png`
- `largest_drop_vs_original_index_0048_comparison.png`
- `original_vs_adapted_selection_summary.csv`
- `original_vs_adapted_selection_summary.json`

Selected examples:

| role | index | original median-scaled abs_rel | original median-scaled a1 | adapted median-scaled abs_rel | adapted median-scaled a1 |
|---|---:|---:|---:|---:|---:|
| adapted good | 12 | 0.3424 | 0.5276 | 0.4066 | 0.3181 |
| adapted typical | 36 | 0.4123 | 0.3953 | 0.8670 | 0.1783 |
| adapted bad | 75 | 0.5360 | 0.2625 | 1.0535 | 0.0323 |
| largest drop vs original | 48 | 0.1887 | 0.7302 | 0.4930 | 0.1568 |

Visual interpretation:

- Even the "adapted good" example is worse than the original model on the same image.
- The adapted raw predictions look flatter and less detailed.
- After median scaling, the adapted model often loses tree/canopy/ground separation that the original model still weakly preserved.
- Error maps show larger valid-pixel errors around orchard structure and ground boundaries.
- This supports the metric conclusion: the adapted decoder is not just at the wrong global scale; it is also damaging relative depth structure.

## No-Color-Augmentation 250-Step Control

Date: 2026-05-07

Purpose: test whether Citrus train-time ColorJitter is making the self-supervised photo-loss game less stable. This is a standard training-setting control, not a new method.

Run:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_noaug_250steps/
```

Recipe:

- same conservative decoder-only recipe as the 1000-step probe
- `--max_train_steps 250`
- `--freeze_depth_steps 25`
- `--freeze_depth_encoder`
- low depth learning rate: `1e-5` to `5e-7`
- `--citrus_color_aug_probability 0`

Training status:

- Finished cleanly on CUDA.
- Stopped at the intended `--max_train_steps=250` limit.
- Saved `step_250` and `weights_0`; the checkpoint files are identical, so `weights_0` is the final 250-step model.

First 100 validation samples:

| checkpoint | raw abs_rel | median-scaled abs_rel | median-scaled a1 | median scale ratio |
|---|---:|---:|---:|---:|
| untouched baseline | 0.7289 | 0.3680 | 0.4807 | 3.944117 |
| conservative 250 with color aug | 0.7331 | 0.4542 | 0.4290 | 4.339389 |
| conservative 250 no color aug | 0.7192 | 0.4108 | 0.4568 | 4.057223 |

Interpretation:

- Disabling color augmentation helped compared with the color-augmented 250-step run.
- The no-augmentation control slightly improved raw-scale `abs_rel` versus the untouched baseline, but it still did not beat the untouched baseline on median-scaled relative-depth quality.
- This suggests train-time color jitter may worsen the drift, but it is not the whole explanation.
- Do not scale this to a long run automatically. A modest next check could evaluate whether 500 no-augmentation steps continues to improve or starts degrading, but that should be explicitly confirmed before running.

## No-Color-Augmentation 500-Step Control

Date: 2026-05-07

Purpose: test whether the 250-step no-color-augmentation improvement trend continues or degrades with more steps.

Run:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_noaug_500steps/
```

Recipe:

- same as the 250-step no-color-augmentation control
- `--max_train_steps 500`
- `--save_step_frequency 250`
- `--citrus_color_aug_probability 0`

Training status:

- Started as a background process and finished cleanly on CUDA.
- Stopped at the intended `--max_train_steps=500` limit.
- Saved `step_250`, `step_500`, and `weights_0`.
- `step_500` and `weights_0` have identical checkpoint hashes, so `weights_0` is the final 500-step model.

Saved evaluation:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_noaug_500steps/eval_val100_weights_0/
```

First 100 validation samples:

| checkpoint | raw abs_rel | median-scaled abs_rel | median-scaled a1 | median scale ratio |
|---|---:|---:|---:|---:|
| untouched baseline | 0.7289 | 0.3680 | 0.4807 | 3.944117 |
| no color aug, 250 steps | 0.7192 | 0.4108 | 0.4568 | 4.057223 |
| no color aug, 500 steps | 0.7235 | 0.5300 | 0.3513 | 4.322919 |
| color aug, 500 steps | 0.7458 | 0.6325 | 0.2445 | 4.897573 |

Interpretation:

- No color augmentation is still better than color augmentation at the same 500-step point.
- But the 500-step no-augmentation checkpoint is worse than the 250-step no-augmentation checkpoint.
- This means disabling color augmentation reduces the damage but does not make the recipe stable.
- The current Milestone 3 recipe family should not be scaled into a long run. The best current adapted control remains weak/negative evidence, not an improved model.
