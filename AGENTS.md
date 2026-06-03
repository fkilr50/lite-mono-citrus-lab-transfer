# AGENTS.md

## Purpose

This file is the shared project context for the Lite-Mono + Citrus Farm research project.
The project is not only a dataset-preparation task: the end goal is a publishable research paper on improving lightweight monocular depth estimation for vegetation-dense agricultural environments, with Citrus Farm used as the current main benchmark/domain and a pest-killing robot deployment motivation.
All new chats should read this file first.

## Mandatory Context Workflow

1. Read this file before starting any task.
2. Treat this file as source of truth for project status, decisions, and next steps.
3. If any code, config, data pipeline, or experiment setting changes, update this file in the same turn.
4. Do not mark a task complete until this file is updated when required.
5. In every final response, include:
   - Context file updated: Yes
   - Short summary of what was updated in this file
6. If no update is required, include:
   - Context file updated: No
   - Reason no update was required

## Startup Instruction For New Chats

Always read AGENTS.md first, then continue work.
If project changes are made, update AGENTS.md before finishing.

## Context Document Roles

Use the project documents with clear roles:

1. `AGENTS.md` is the source of truth for project goal, current status, milestone progress, pipeline decisions, commands, and repo-impacting changes.
2. `citrus_project/research/student_qna.md` is the beginner-friendly companion note for recurring questions, plain-language explanations, folder meanings, and stable definitions.
3. `citrus_project/research/` notes such as dataset-audit summaries and baseline notes are paper-facing research records, not general onboarding notes.
4. `citrus_project/milestones/*/README.md` files should be teammate-facing milestone handoffs: explain what the milestone tried to answer, what workflow happened, what decisions were made, what beginner questions shaped the work, and where to look for deeper evidence.

Update policy:

1. Update `AGENTS.md` whenever code, config, data-pipeline behavior, experiment defaults, milestone status, important paths, or research decisions change.
2. Update `citrus_project/research/student_qna.md` whenever a new recurring confusion is explained in a way that future students will likely need again.
3. If a change affects both project status and beginner understanding, update both files in the same turn.
4. Keep `citrus_project/research/student_qna.md` simple and stable; do not use it as a scratchpad or temporary log.

Living-notes rule:

1. Treat project notes as living documents, not append-only logs.
2. Keep `AGENTS.md` compact and source-of-truth oriented: current status, active decisions, important commands/paths, and next actions.
3. When experiments accumulate, consolidate old detail into readable tables or summaries instead of continually appending full command/output narratives.
4. Keep detailed evidence in the appropriate milestone README or research note, and let `AGENTS.md` link or point there.
5. When a newer result supersedes an older temporary result, update the older wording or mark it as superseded instead of leaving conflicting notes.
6. Prefer clarity for future chats over preserving every intermediate line in `AGENTS.md`.

## Workspace Layout

The repository now has a deliberate split between upstream Lite-Mono code and project-owned Citrus research work.

1. Original/upstream-style Lite-Mono code remains at the repo root.
2. Project-owned Citrus work lives under `citrus_project/`.
3. `citrus_project/dataset_workspace/` is the active Citrus dataset pipeline workspace.
4. `citrus_project/research/` stores project notes, paper shortlist material, and beginner-facing explanations.
5. `citrus_project/milestones/` is reserved for milestone-specific code, notes, helpers, and outputs as milestone work begins.
6. `citrus_project/README.md` and `citrus_project/milestones/README.md` describe this custom workspace layout.

Team collaboration files:

1. `citrus_project/TEAM_WORKFLOW.md` is the collaboration/onboarding guide for teammates and their AI assistants.
2. `citrus_project/TASK_BOARD.md` is the short current-work board with owners, status, and next actions.
3. `citrus_project/research/literature_tracker.md` is the working file for model-improvement scouting and related-work intake.
4. `citrus_project/research/scene_taxonomy.md` is the working file for scene categories, example selection, and qualitative-support notes.
5. `citrus_project/milestones/00_dataset_audit/sample_pack/` is the low-storage collaboration area for a small shared sample pack.
6. `citrus_project/research/advisor_notes.md` stores professor/advisor questions, recommendations, and later follow-up directions.

Research-note workflow for future chats:

1. If a result is mainly evidence for dataset quality or label generation, write or update `citrus_project/research/dataset_notes.md`.
2. If a result is mainly evidence for model behavior or comparison, write or update `citrus_project/research/baseline_notes.md`.
3. If a result might later appear in the paper, add or refresh a short entry in `citrus_project/research/paper_shortlist.md`.
4. If a professor/advisor question or recommendation should be tracked for later, add it to `citrus_project/research/advisor_notes.md`.
5. If the result changes project status, milestones, defaults, commands, or decisions, also update `AGENTS.md`.
6. If the result answers a recurring beginner question, also update `citrus_project/research/student_qna.md`.

Team-collaboration workflow for future chats:

1. Tell teammates and their AI assistants to read `AGENTS.md`, then `citrus_project/TEAM_WORKFLOW.md`, then `citrus_project/TASK_BOARD.md`.
2. Keep the active ownership list current in `citrus_project/TASK_BOARD.md`.
3. Prefer low-overlap work division: one main integrator for fragile core code, bounded parallel work for research support.
4. For low-storage collaborators, prefer `citrus_project/milestones/00_dataset_audit/sample_pack/` plus notes instead of requiring the full dataset workspace.
5. When a teammate finishes meaningful work, update the task board and the relevant note file in the same turn if possible.

Milestone workspace rule:

1. If new code or notes belong clearly to one milestone, prefer placing them under the matching folder in `citrus_project/milestones/`.
2. Keep cross-cutting dataset pipeline scripts in `citrus_project/dataset_workspace/`.
3. Keep cross-cutting paper/support notes in `citrus_project/research/`.
4. Keep milestone README files readable for teammates who have similar background knowledge to the user; they should bridge between the short global status in `AGENTS.md` and the detailed evidence notes in `citrus_project/research/`.

Current collaboration stance:

1. The user is currently the main integrator for core Citrus pipeline and likely early baseline-code work.
2. Teammates should avoid editing fragile shared pipeline/model code in parallel unless explicitly coordinated.
3. Friend A is a good fit for literature scouting, improvement-idea ranking, and related-work intake.
4. Friend B is a good fit for scene taxonomy, example selection, figure support, and paper/dataset communication support.
5. The collaboration setup should reduce merge chaos, not create parallel overlapping implementations.

## User Collaboration Preference

When the user is talking about the codebase, be careful and verify details before answering.

1. Do not assume file importance, workflow relevance, or implementation behavior without checking the actual files or recent project context first.
2. Look for edge cases and mismatches before speaking confidently about code, tests, scripts, folders, or pipeline behavior.
3. If something is only a guess, say clearly that it is a guess.
4. For ideas, brainstorming, or non-code discussion, it is okay to propose possibilities as long as assumptions are clearly labeled.
5. Do not treat legacy or sidecar files as important to the active workflow unless that relevance is confirmed from the repository or current project notes.
6. When explaining AI/PyTorch/image-processing concepts to the user, prefer concrete mental hooks over broad definitions:
   - say what a value represents in plain words, such as "per-pixel closeness level," before giving formulas
   - explain why an intermediate value exists, not only its shape or file format
   - connect each value to the exact project artifact or code step it affects
   - use small numeric examples when a value is not intuitive
   - proactively explain nearby terms that are likely to confuse a beginner, instead of waiting for a perfect follow-up question
7. For deep AI/model-algorithm work, use an active mutual-understanding workflow:
   - ask the user frequent concept-check questions about the mathematical idea, tensor operation, and code mapping before rushing into implementation
   - expect the user's first mental model to be incomplete or wrong, and treat that as the normal teaching/debugging path
   - correct misunderstandings gently but explicitly with concrete examples from this repository
   - invite the user to challenge the assistant's interpretation too, because the assistant may also misread code or context
   - do not move past core concepts such as loss, disparity/depth conversion, pose, masks, scaling, tensor shapes, and metrics until both the formula-level and code-level meaning are clear enough to explain back

## Project Goal

Publish an improved Lite-Mono-style monocular depth estimation method for vegetation-dense agricultural environments, validated first on Citrus Farm and motivated by a lightweight RGB-only pest-killing robot perception stack.

Research objective:

1. Use original Lite-Mono as the lightweight monocular depth baseline.
2. Show and measure the domain gap between urban/KITTI-style Lite-Mono behavior and vegetation-dense agricultural scenes, using Citrus Farm as the first main benchmark.
3. Build a reliable Citrus Farm RGB + depth-label evaluation/training pipeline as the first validated domain-specific pipeline.
4. Improve Lite-Mono or its training objective for dense vegetation while keeping runtime inference monocular RGB-only and lightweight.
5. Compare original Lite-Mono, Citrus-adapted Lite-Mono, and the proposed improved variant under the same Citrus data budget and splits.
6. Frame Citrus Farm as the current validation domain, not the only intended deployment domain; other agricultural users should be able to adapt the approach with their own RGB sequences and optional depth-label pipeline through fine-tuning or retraining.

Dataset-preparation objective:

1. Download correctly aligned Citrus Farm ROS bag files.
2. Extract ZED RGB/depth and Velodyne LiDAR point cloud data.
3. Match RGB frames with LiDAR by timestamp.
4. Project and densify LiDAR depth for evaluation labels and optional supervised/hybrid training.
5. Export reproducible train/val/test split manifests, metrics, and quality diagnostics.

## Pipeline Overview

1. Download base (LiDAR) bags.
2. Download zed bags using overlap window from selected base bags.
3. Extract zed RGB and depth from zed bags.
4. Extract LiDAR point clouds from base bags.
5. Audit LiDAR-to-ZED projection alignment on a small sample before trusting dense labels.
6. Densify LiDAR into image-aligned depth.
7. Build train/val/test-ready dataset artifacts.

## Citrus Farm Dataset Source Understanding

Official dataset intent:

1. CitrusFarm is a multimodal agricultural robotics dataset for localization, mapping, and crop monitoring in citrus tree farms.
2. It includes seven sequences from three citrus fields, multiple tree species/growth stages, different planting patterns, and varying daylight conditions.
3. It provides nine sensing modalities: stereo RGB, ZED depth, monochrome, near-infrared, thermal, wheel odometry, LiDAR, IMU, and GPS-RTK.
4. Raw data is released as modality-split ROS bag blocks. The authors state users can play bags from the same folder together and ROS will sequence messages by timestamps.
5. Official tooling includes download_citrusfarm.py and bag2files.py. bag2files.py is a generic extractor to images, PCD, CSV, and text files; it is not a monocular-depth training pipeline.

How our pipeline relates to author intent:

1. Download filtering by folder/modality is consistent with the official download script design.
2. Selecting only Sequence 01, base bags, ZED bags, calibration, and ground truth is a research-scope reduction, not an official fixed split.
3. Extracting `/zed2i/zed_node/left/image_rect_color`, `/zed2i/zed_node/depth/depth_registered`, and `/velodyne_points` is consistent with the official topic list.
4. Saving RGB as PNG and arrays as NPZ differs from the official bag2files.py output format, but it is reasonable for lossless ML preprocessing.
5. Projecting and densifying LiDAR into ZED image space is our own derived-label pipeline. It must be validated; it should not be assumed to be an official Citrus Farm ground-truth product.
6. Citrus Farm is being used because it is a strong available multimodal agricultural dataset for this research stage, not because the intended method should only work in citrus orchards.

## Canonical Script Order

1. citrus_project/dataset_workspace/download_citrusfarm_seq_01_lidar.py
2. citrus_project/dataset_workspace/download_citrusfarm_seq_01_rgb_depth.py
3. citrus_project/dataset_workspace/extract_left_rgbd_from_raw.py
4. citrus_project/dataset_workspace/extract_lidar_from_raw.py
5. citrus_project/dataset_workspace/audit_projection_alignment.py
6. citrus_project/dataset_workspace/densify_lidar.py
7. citrus_project/dataset_workspace/build_training_dataset.py

## Current Status Snapshot (2026-03-31)

Implemented:

1. Overlap-window bag selection for zed download based on selected base bag time window.
2. Timestamp-ordered base bag selection.
3. Safer RGB-LiDAR pairing and diagnostics in densification flow.
4. Batch builder script to generate dense depth targets and split manifests.
5. Pairing logic now supports same-session preference with optional cross-session fallback under the same max timestamp delta.

Validated:

1. Overlap-window selection behavior was tested against official YAML list.
2. build_training_dataset.py was tested with --max_samples 5 and produced expected outputs.

## Current Dataset Processing Review Verdict (2026-04-15)

High-level verdict:

1. Download and extraction are broadly aligned with the official dataset structure and topic intent.
2. The processing layer that turns RGB + LiDAR into dense monocular depth labels is project-specific and needs stronger validation before paper experiments.
3. The previous code is useful as a prototype, but it should not yet be treated as publication-grade without fixing reproducibility and calibration-quality gates.

Current concerns:

1. The LiDAR-to-ZED transform convention in densify_lidar.py should be independently verified against calibration files and visual overlays.
2. Dense interpolation can create plausible but unsupported depth in vegetation gaps; builder now saves valid masks, but confidence/distance handling still needs visual review.
3. Extracted ZED depth is now available as optional builder sanity-check metrics, but actual full-run statistics have not been reviewed yet.
4. build_training_dataset.py now rebuilds manifest rows for reused dense files, but reused rows only contain full projection/sparse metrics when dense labels are regenerated.

Fixes completed on 2026-04-15:

1. build_training_dataset.py now returns manifest/metrics rows when dense files already exist instead of exiting with "No new samples."
2. Added `--no_skip_existing` so dense outputs can be force-regenerated when build parameters change.
3. Added grouped split support with default `--split_strategy time_block` to reduce adjacent-frame train/val/test leakage; legacy random splitting remains available with `--split_strategy random`.
4. Added `dense_lidar_valid_mask_npz/` outputs so downstream evaluation/training can use a valid-label mask.
5. Added optional nearest ZED-depth sanity-check metrics in `all_samples.csv`.
6. Added regression tests for pairing fallback, grouped split behavior, reused dense manifest rows, and ZED-depth metric computation.
7. Added audit_projection_alignment.py to generate small RGB/LiDAR/ZED projection overlay panels before running full dense dataset generation.
8. Added selectable LiDAR-to-ZED transform modes in densify_lidar.py: `production_current` and `exact_lidar_parent_child_inverted`.
9. build*training_dataset.py now accepts `--transform_mode`; alternate transform runs default to a separate output folder named `prepared_training_dataset*<transform_mode>`unless`--output_dir` is explicitly provided.
10. Builder metrics now record `transform_mode`, and regression tests cover transform availability plus manifest tagging.
11. The default dense-label interpolation is now `local_idw`, a conservative local inverse-distance weighted fill that rejects candidate pixels when nearby LiDAR depths disagree too much. This replaced `linear` grid interpolation as the default because full 2D linear triangulation produced visually implausible surfaces in vegetation scenes.

Manual projection-audit observation (2026-04-15):

1. `production_current` and `exact_lidar_parent_child_inverted` both visually align well with vegetation/scene structure in the generated 3-sample audit.
2. `current_chain_no_invert` and `exact_lidar_parent_child_direct` look clearly wrong; projected points form near-vertical bands and do not land on plants/scene structure.
3. User observed little difference between the two plausible candidates, except `exact_lidar_parent_child_inverted` has slightly narrower purple scanline spacing than `production_current`.
4. Historical decision at that point: keep `production_current` as the active/default densify_lidar transform, but make `exact_lidar_parent_child_inverted` runnable as an alternate comparison dataset because it may concentrate projected LiDAR more tightly on plant structures.
5. The old mixed projection-audit output folder was removed and a clean 12-sample projection audit was regenerated under `projection_alignment_audit/`.
6. User inspected the clean 12-sample audit and judged `production_current` versus `exact_lidar_parent_child_inverted` as mostly tied; the main visible difference remains narrower purple projected scanline spacing in `exact_lidar_parent_child_inverted`.
7. Historical interpretation at that point: because the larger visual audit was a tie, keep `production_current` as the default label-generation transform unless later quantitative checks against ZED depth or model-evaluation behavior showed a clear advantage for the alternate transform.
8. Superseded on 2026-04-17 by the final route decision: `exact_lidar_parent_child_inverted` is now the default/final label route.

Legacy linear metrics probe result (2026-04-15):

1. Generated two 50-sample metrics probes using the older `linear` interpolation method, not full datasets:
   - `prepared_training_dataset_metrics_probe_50/` using `production_current`
   - `prepared_training_dataset_metrics_probe_50_exact/` using `exact_lidar_parent_child_inverted`
2. These probe outputs were later removed during workspace cleanup, but their summary numbers remain here as historical context for the older `linear` interpolation route comparison.
3. Both probes used the first 50 matched RGB-LiDAR samples, so split validation is not meaningful yet: all 50 samples fall into one time block and therefore train=50, val=0, test=0.
4. `production_current` legacy-linear probe summary:
   - median RGB-LiDAR delta: 39.211 ms
   - median dense fill ratio: 0.541213
   - median sparse fill ratio: 0.009131
   - median valid projected ratio: 0.402153
   - median dense depth: 3.084715 m
   - median ZED/LiDAR overlap ratio: 0.355920
   - median ZED-vs-LiDAR absolute difference: 0.631544 m
   - median ZED-vs-LiDAR relative difference: 0.379210
5. `exact_lidar_parent_child_inverted` legacy-linear probe summary:
   - median RGB-LiDAR delta: 39.211 ms
   - median dense fill ratio: 0.439080
   - median sparse fill ratio: 0.009071
   - median valid projected ratio: 0.399315
   - median dense depth: 3.400844 m
   - median ZED/LiDAR overlap ratio: 0.297551
   - median ZED-vs-LiDAR absolute difference: 0.205901 m
   - median ZED-vs-LiDAR relative difference: 0.084877
6. Initial interpretation from the legacy-linear probe: `exact_lidar_parent_child_inverted` appeared quantitatively closer to ZED depth on overlapping pixels, but produced lower dense fill/overlap. Treat this as old supporting evidence only; current decisions should prioritize `local_idw` audit/probe results.
7. Observed risk in the legacy-linear probe: dense max values remained around 95-109 m because `max_interp_depth_m=28.0` clamped only interpolated pixels while preserving far measured LiDAR points. This may be acceptable for raw labels but should be capped or masked consistently for model evaluation.

## Current local_idw projection audit result (2026-04-15)

1. Regenerated the normal ignored `projection_alignment_audit/` with 12 samples using `interpolation_method=local_idw`.
2. Audit parameters recorded in `projection_alignment_audit/audit_summary.json`:
   - `distance_mask_px=25`
   - `local_idw_k=4`
   - `local_idw_power=2.0`
   - `local_idw_max_depth_spread_m=1.25`
   - `local_idw_max_relative_depth_spread=0.35`
3. 12-sample median result for `production_current`:
   - dense fill ratio: 0.433060
   - ZED/LiDAR overlap ratio: 0.219531
   - ZED-vs-LiDAR absolute difference: 0.569570 m
   - ZED-vs-LiDAR relative difference: 0.278299
4. 12-sample median result for `exact_lidar_parent_child_inverted`:
   - dense fill ratio: 0.365558
   - ZED/LiDAR overlap ratio: 0.214457
   - ZED-vs-LiDAR absolute difference: 0.193937 m
   - ZED-vs-LiDAR relative difference: 0.074806
5. Current interpretation: `local_idw` intentionally creates more holes than linear interpolation because it refuses uncertain fills. This is preferable to fake dense vegetation surfaces for evaluation/training labels.

## Time-spread local_idw metrics probe (2026-04-16)

1. Added `--metrics_only` to `audit_projection_alignment.py` so larger route-comparison probes can write CSV/JSON metrics without generating hundreds of overlay/detail PNG panels.
2. Hardened sparse and dense projection loops to skip non-finite projected points instead of crashing when a candidate transform produces infinite pixel coordinates.
3. Ran a 200-sample time-spread metrics-only probe:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/dataset_workspace/audit_projection_alignment.py --max_samples 200 --metrics_only --output_dir projection_alignment_audit/time_spread_metrics_200`
4. Probe scope:
   - 200 samples selected across 5282 matched RGB-LiDAR pairs
   - first sampled RGB: `zed_2023-07-18-14-26-49_0_bag_1689715609331936216.png`
   - last sampled RGB: `zed_2023-07-18-14-35-27_18_bag_1689716137437974008.png`
   - median RGB-LiDAR delta: 27.873 ms
   - median RGB-ZED-depth delta: 12.710 ms
5. `production_current` 200-sample median results:
   - dense fill ratio: 0.424624
   - ZED/LiDAR overlap ratio: 0.231256
   - ZED-vs-LiDAR absolute difference: 0.538049 m
   - ZED-vs-LiDAR relative difference: 0.221197
   - valid projected ratio: 0.328247
6. `exact_lidar_parent_child_inverted` 200-sample median results:
   - dense fill ratio: 0.366310
   - ZED/LiDAR overlap ratio: 0.212465
   - ZED-vs-LiDAR absolute difference: 0.191620 m
   - ZED-vs-LiDAR relative difference: 0.069013
   - valid projected ratio: 0.329068
7. Pairwise result across all 200 samples:
   - `production_current` had higher dense fill on 198/200 samples.
   - `exact_lidar_parent_child_inverted` had lower ZED absolute error on 200/200 samples.
   - `exact_lidar_parent_child_inverted` had lower ZED relative error on 200/200 samples.
8. Interpretation: the time-spread probe strongly supports `exact_lidar_parent_child_inverted` as the cleaner label route despite lower dense coverage.

## Final label route decision (2026-04-17)

1. Ran a final 12-sample time-spread visual spot-check:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/dataset_workspace/audit_projection_alignment.py --max_samples 12 --output_dir projection_alignment_audit/time_spread_visual_12`
2. Visual outputs are local ignored diagnostics:
   - `citrus_project/dataset_workspace/projection_alignment_audit/time_spread_visual_12/overlays/`
   - `citrus_project/dataset_workspace/projection_alignment_audit/time_spread_visual_12/details_production_current/`
   - `citrus_project/dataset_workspace/projection_alignment_audit/time_spread_visual_12/details_exact_lidar_parent_child_inverted/`
3. Visual spot-check result:
   - `exact_lidar_parent_child_inverted` remains visually plausible across time-spread samples.
   - the two rejected direct/no-invert candidates remain visibly wrong.
4. Final/default dense-label transform is now `exact_lidar_parent_child_inverted`.
5. `production_current` remains available as an alternate comparison route via `--transform_mode production_current`.
6. One-sample smoke build verified that build_training_dataset.py now uses `exact_lidar_parent_child_inverted` by default; the throwaway output folder was removed after validation.
7. Research note:
   - `citrus_project/research/dataset_notes.md`

## Original Lite-Mono Citrus Sanity Run (2026-04-16)

1. Ran original pretrained `weights/lite-mono` on one copied Citrus RGB image using `test_simple.py`.
2. Keep Lite-Mono demo outputs out of extracted dataset folders. The RGB image should be copied to an ignored demo/output folder before running `test_simple.py`, because `test_simple.py` writes `*_disp.jpeg` and `*_disp.npy` next to the input image.
3. Command used:
   - `D:/Conda_Envs/lite-mono/python.exe test_simple.py --load_weights_folder weights/lite-mono --image_path citrus_project/research/generated/lite_mono_single_image_demo/zed_2023-07-18-14-26-49_0_bag_1689715609331936216.png --model lite-mono --no_cuda`
4. Output files were generated under ignored `citrus_project/research/generated/lite_mono_single_image_demo/`, not under the dataset folder:
   - `citrus_project/research/generated/lite_mono_single_image_demo/zed_2023-07-18-14-26-49_0_bag_1689715609331936216_disp.jpeg`
   - `citrus_project/research/generated/lite_mono_single_image_demo/zed_2023-07-18-14-26-49_0_bag_1689715609331936216_disp.npy`
5. Interpretation: this is a qualitative baseline sanity/demo run only. It started the Citrus baseline milestone but did not complete it. The later full validation/test baseline run on 2026-04-28 supersedes this demo for quantitative claims; keep this one-image run only as qualitative context.

## Original Lite-Mono Citrus Full Baseline Run (2026-04-28)

1. Ran original pretrained `weights/lite-mono` on the full Citrus validation and test splits using the Milestone 1 evaluator:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 0 --run_model --summary_only --progress_interval 50 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results`
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split test --max_samples 0 --run_model --summary_only --progress_interval 50 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results`
2. Run environment:
   - device: `cuda`
   - GPU: NVIDIA GeForce RTX 4060 Laptop GPU
   - weights: `weights/lite-mono`
   - model input size: 640 x 192
   - model depth conversion range: 0.1 m to 100.0 m
   - evaluation label cap: 0.001 m to 80.0 m
   - averaging rule: per-image metric mean
3. Saved full-result files:
   - `citrus_project/milestones/01_original_lite_mono_baseline/results/val_lite-mono_full_summary.json`
   - `citrus_project/milestones/01_original_lite_mono_baseline/results/val_lite-mono_full_per_sample.csv`
   - `citrus_project/milestones/01_original_lite_mono_baseline/results/test_lite-mono_full_summary.json`
   - `citrus_project/milestones/01_original_lite_mono_baseline/results/test_lite-mono_full_per_sample.csv`
4. Validation split result:
   - samples evaluated: 564 / 564
   - mean valid-label coverage: 37.2272%
   - median scale ratio: 3.582965
   - mean raw-scale metrics: abs_rel=0.7128, sq_rel=2.1823, rmse=4.1009, rmse_log=1.3642, a1=0.0195, a2=0.0382, a3=0.0669
   - mean median-scaled metrics: abs_rel=0.4176, sq_rel=1.7692, rmse=3.1642, rmse_log=0.4834, a1=0.4629, a2=0.7103, a3=0.8494
   - total run time: 83.274 s
   - model-forward FPS: 28.478
5. Test split result:
   - samples evaluated: 407 / 407
   - mean valid-label coverage: 36.7190%
   - median scale ratio: 4.374715
   - mean raw-scale metrics: abs_rel=0.7273, sq_rel=2.3440, rmse=4.4517, rmse_log=1.4325, a1=0.0149, a2=0.0288, a3=0.0472
   - mean median-scaled metrics: abs_rel=0.3836, sq_rel=1.5175, rmse=3.1451, rmse_log=0.4664, a1=0.4989, a2=0.7264, a3=0.8700
   - total run time: 60.805 s
   - model-forward FPS: 29.529
6. Model efficiency metadata from the same evaluator path:
   - total depth-inference parameters: 3,074,747
   - encoder parameters: 2,848,120
   - depth-decoder parameters: 226,627
   - total checkpoint size: about 11.94 MiB
   - pose network is not counted because it is training-only and not used for RGB-only depth inference
7. First qualitative-analysis helper:
   - added `citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py`
   - default behavior reads the full per-sample CSV, selects good/typical/bad validation examples by `median_scaled_a1`, reruns inference only for those selected images, and saves visual panels under `citrus_project/milestones/01_original_lite_mono_baseline/visuals/`
   - validation command used: `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py --split val`
   - selected validation examples:
     - good: index 420, median-scaled a1=0.8264, median-scaled abs_rel=0.1510
     - typical: index 82, median-scaled a1=0.4784, median-scaled abs_rel=0.3405
     - bad: index 442, median-scaled a1=0.0468, median-scaled abs_rel=0.7835
   - output files include:
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/good_index_0420_median_scaled_a1_0.826.png`
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/typical_index_0082_median_scaled_a1_0.478.png`
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/bad_index_0442_median_scaled_a1_0.047.png`
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/val_lite-mono_median_scaled_a1_selection_summary.json`
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/val_lite-mono_median_scaled_a1_selection_summary.csv`
8. Test qualitative-analysis run:
   - ran `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py --split test`
   - selected test examples:
     - good: index 24, median-scaled a1=0.7709, median-scaled abs_rel=0.1821
     - typical: index 7, median-scaled a1=0.5301, median-scaled abs_rel=0.3168
     - bad: index 46, median-scaled a1=0.0761, median-scaled abs_rel=0.6204
   - output files include:
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/good_index_0024_median_scaled_a1_0.771.png`
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/typical_index_0007_median_scaled_a1_0.530.png`
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/bad_index_0046_median_scaled_a1_0.076.png`
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/test_lite-mono_median_scaled_a1_selection_summary.json`
     - `citrus_project/milestones/01_original_lite_mono_baseline/visuals/test_lite-mono_median_scaled_a1_selection_summary.csv`
9. Interpretation:
   - raw-scale metrics are poor because the pretrained KITTI-style Lite-Mono baseline predicts Citrus depths at the wrong absolute scale
   - median scaling improves the scores by aligning the prediction's median depth with the label median per image, so the median-scaled result is a better read of relative depth structure
   - even after median scaling, a1 is only about 0.46 on validation and 0.50 on test, so the original model still has a clear Citrus/vegetation domain gap
10. Milestone 1 is close to complete for baseline evidence:
   - full val/test metric files now exist
   - validation and test good/typical/bad visual panels now exist
   - first beginner-friendly visual interpretation note now exists at `citrus_project/milestones/01_original_lite_mono_baseline/visual_interpretation.md`
   - remaining work is optional depth: broader failure taxonomy and optional FLOPs/dedicated deployment benchmark if the paper needs a cleaner efficiency claim

## Current Local Data Snapshot (2026-04-01)

Observed after recent local script/data changes:

1. Download scope set to one base block (max_blocks=1), with overlap-window zed download yielding 21 zed bag chunks for that base time window.
2. Extracted outputs increased substantially:
   - extracted_rgbd RGB frames: 6047 PNG
   - extracted_rgbd depth dataset: 6049 NPZ
   - extracted_lidar scans: 5235 NPZ
3. Local storage footprint now reflects this larger pull:
   - extracted_rgbd: ~16.42 GB
   - extracted_lidar: ~1.46 GB
4. Unique extracted bag prefixes currently indicate expected ratio:
   - zed prefixes: 21
   - base prefixes: 1
5. Full prepared dataset output now exists under `citrus_project/dataset_workspace/prepared_training_dataset/` with:
   - 5282 dense LiDAR labels
   - 5282 valid masks
   - split files and metrics summary
6. build_training_dataset.py includes parallel processing and optimized timestamp pairing (find_closest_optimized) for faster conversion runs.

## Important Pairing Rule

Do not pair modalities by filename order only.
Use this two-stage rule:

1. Bag level: overlap-window selection (coarse filtering).
2. Frame level: nearest timestamp matching with max delta and same-session preference, then fallback-to-any-session when enabled.

## Key Data Locations

1. Raw/extracted workspace: citrus_project/dataset_workspace/
2. Extracted RGB: citrus_project/dataset_workspace/extracted_rgbd/zed2i_zed_node_left_image_rect_color/
3. Extracted LiDAR: citrus_project/dataset_workspace/extracted_lidar/velodyne_points/
4. Dense outputs: citrus_project/dataset_workspace/extracted_dense_lidar/
5. Prepared dataset output: citrus_project/dataset_workspace/prepared_training_dataset/
6. Projection audit output: citrus_project/dataset_workspace/projection_alignment_audit/ (generated diagnostics; ignored by git)

## Prepared Dataset Artifacts

Generated by build_training_dataset.py:

1. prepared_training_dataset/dense_lidar_npz/
2. prepared_training_dataset/dense_lidar_valid_mask_npz/
3. prepared_training_dataset/metrics/all_samples.csv
4. prepared_training_dataset/metrics/summary.json
5. prepared_training_dataset/splits/train_pairs.txt
6. prepared_training_dataset/splits/val_pairs.txt
7. prepared_training_dataset/splits/test_pairs.txt

Depth-label storage versus visualization:

1. The actual LiDAR-densified labels are numeric `.npz` arrays, not PNG/JPG images. Each stored value represents depth in meters, and invalid/untrusted pixels are represented as 0 or excluded by the valid mask.
2. The valid masks are numeric `.npz` arrays with 1 for trusted depth pixels and 0 for pixels that should not be scored/trained as valid depth.
3. PNG panels generated by audit_projection_alignment.py or densify_lidar.py are visual diagnostics only. They are useful for human inspection and paper figures, but they are not the source labels used for metric computation.
4. Paper-style depth images should be generated later from numeric predictions and numeric labels using a consistent colormap and depth range.
5. In audit detail panels, "LiDAR label visual (near bright)" is the human-facing depth-label visualization. "Support distance, not depth" is only a confidence/support-distance diagnostic and must not be interpreted as the depth label.
6. In audit detail panels, the "Sparse LiDAR depth" subplot uses display-only brightening and light dilation for visibility. It does not change the sparse LiDAR depth array, dense labels, valid masks, or metrics.
7. Current `projection_alignment_audit/overlays/` panels compare all transform candidates. Current detail panels are split by the two plausible dense-label routes:
   - `projection_alignment_audit/details_production_current/`
   - `projection_alignment_audit/details_exact_lidar_parent_child_inverted/`
     These detail folders provide human-facing dense-label visuals for both candidate routes.

## Full prepared dataset build (2026-04-23)

1. Ran the full dataset builder successfully from `citrus_project/dataset_workspace/`:
   - `D:/Conda_Envs/lite-mono/python.exe build_training_dataset.py --workers 10`
2. Output directory used by the current defaults:
   - `citrus_project/dataset_workspace/prepared_training_dataset/`
3. Effective build defaults:
   - `transform_mode=exact_lidar_parent_child_inverted`
   - `interpolation_method=local_idw`
   - `split_strategy=time_block`
   - `enable_zed_depth_metrics=true`
4. Build summary:
   - paired samples: 5282
   - total built samples: 5282
   - train: 4311
   - val: 564
   - test: 407
   - total time-block groups: 28
   - split groups: train=22, val=2, test=4
5. Dense artifacts created:
   - `dense_lidar_npz/`: 5282 files
   - `dense_lidar_valid_mask_npz/`: 5282 files
   - `metrics/all_samples.csv`
   - `metrics/summary.json`
   - `splits/train_pairs.txt`
   - `splits/val_pairs.txt`
   - `splits/test_pairs.txt`
6. Runtime note:
   - the worker-processing stage completed in about 657.71 seconds with 10 workers on the user's current machine
   - this build path is CPU-parallel, not GPU-accelerated
7. Environment note:
   - an initial sandboxed run failed on Windows when `ProcessPoolExecutor` tried to spawn worker processes (`WinError 5: Access is denied`)
   - the same command succeeded when rerun outside the sandbox, so treat that as an execution-environment constraint rather than a dataset-script logic failure

Alternate transform comparison:

1. `exact_lidar_parent_child_inverted` is now the default/final transform and writes to `prepared_training_dataset/` when no explicit `--output_dir` is provided.
2. Running build_training_dataset.py with `--transform_mode production_current` and no explicit `--output_dir` writes to `prepared_training_dataset_production_current/`.
3. Metrics and summary files include `transform_mode` so final and alternate-transform dense labels can be compared without relying only on folder names.

## Research Artifacts And Communication Notes

Paper/research notes:

1. citrus_project/research/README.md
2. citrus_project/research/student_qna.md
3. citrus_project/research/paper_shortlist.md
4. citrus_project/research/dataset_notes.md
5. citrus_project/research/baseline_notes.md
6. citrus_project/research/literature_tracker.md
7. citrus_project/research/scene_taxonomy.md
8. citrus_project/research/advisor_notes.md

Generated local research artifacts:

1. citrus_project/research/generated/ (ignored by git)

Current communication stance:

1. The old reports/professor folder was removed because the research structure is being refreshed.
2. The reports/ presentation folder was removed after the presentation was completed.
3. Keep paper-useful evidence, experiment summaries, and paper content candidates under citrus_project/research/.
4. Keep bulky generated images/NPY artifacts under ignored citrus_project/research/generated/.
5. Explain interpolation as a useful initial gap-filling method, not as perfect ground truth. Use "LiDAR-densified depth labels with valid masks" for paper-facing language.
6. Keep project-scoped `.codex/` config local/ignored. It may contain MCP connector settings or API keys and should not be committed to the repository.
7. Frame the paper and notes carefully: Citrus Farm is the current benchmark and validation dataset, while the broader intended contribution is lightweight monocular depth estimation for vegetation-dense agricultural environments that can later be adapted to other farms with domain-specific data and fine-tuning/retraining.

Research workspace map:

1. `citrus_project/research/paper_shortlist.md` = shortlist of results that may later appear in the paper.
2. `citrus_project/research/dataset_notes.md` = evidence and decisions about dataset building, alignment, and label quality.
3. `citrus_project/research/baseline_notes.md` = evidence and notes about original-model and baseline runs.
4. `citrus_project/research/student_qna.md` = simple recurring explanations for students/team members.
5. `citrus_project/research/literature_tracker.md` = Friend A working file for paper reading and idea scouting.
6. `citrus_project/research/scene_taxonomy.md` = Friend B working file for scene categories and qualitative-support preparation.
7. `citrus_project/research/advisor_notes.md` = professor/advisor questions, recommendations, and follow-up ideas.
8. `citrus_project/research/generated/` = ignored local outputs such as images, NPY files, and quick demo artifacts.

Team workspace map:

1. `citrus_project/TEAM_WORKFLOW.md` = teammate and AI onboarding guide plus edit-boundary rules.
2. `citrus_project/TASK_BOARD.md` = short owner/status/next-action board.
3. `citrus_project/milestones/00_dataset_audit/sample_pack/` = small shared sample area for low-storage collaborators.

## Core Tunables

Download and pairing:

1. max_blocks in download scripts.
2. max_time_delta_sec for frame-level matching.
3. require_same_session preference.
4. fallback_to_any_session (keep preference behavior but recover coverage when session IDs differ).

Densification quality:

1. transform_mode (`exact_lidar_parent_child_inverted` default/final route; `production_current` for alternate comparison)
2. interpolation_method (`local_idw` default; `linear`, `nearest`, and `cubic` remain available for comparison)
3. distance_mask_px
4. local_idw_k
5. local_idw_power
6. local_idw_max_depth_spread_m
7. local_idw_max_relative_depth_spread
8. enable_sparse_morph
9. sparse_morph_kernel
10. sparse_morph_iters
11. max_interp_depth_m
12. clamp_only_interpolated

Builder filters and split:

1. min_dense_fill_ratio
2. train_ratio / val_ratio / test remainder
3. seed
4. split_strategy (default: time_block; random keeps legacy frame-shuffle behavior)
5. time_block_sec
6. max_zed_depth_delta_sec and zed_uint16_scale for ZED-depth sanity metrics

## Known Risks

1. Bag filename timestamp is chunk start time only, not all frame timestamps inside.
2. base and zed chunk durations differ; exact filename timestamp equality is not expected.
3. Calibration misuse can create projection artifacts that look like interpolation problems.
4. The official dataset does not define our dense LiDAR label generation procedure; this is a derived research artifact and needs documentation.
5. Random frame-level splits can overestimate performance if adjacent frames from the same robot pass appear in different splits.
6. ZED rolling shutter, vegetation motion, lighting shifts, and software timestamp synchronization can all affect RGB/depth/LiDAR alignment.
7. LiDAR-densified labels should be evaluated with valid/support masks; dense pixels far from true LiDAR support should not be blindly trusted.

## Terminology For This Project

Use these names consistently in notes and reports:

1. dense LiDAR labels / LiDAR-densified depth labels: LiDAR-derived dense depth labels produced in prepared_training_dataset/dense_lidar_npz.
2. depth dataset: extracted ZED depth maps produced from /zed2i/zed_node/depth/depth_registered.

Important clarification:

1. Current repository contains LiDAR densification only (densify_lidar.py).
2. There is no implemented ZED-depth densification pipeline in the current scripts.
3. Older notes may say "densed lidar dataset"; prefer "dense LiDAR labels" or "LiDAR-densified depth labels" in new paper-facing text.

## Training Strategy Notes (Research Discussion)

1. Current Lite-Mono training path in this repository is self-supervised RGB photometric optimization.
2. depth_gt is currently used for monitoring metrics/logging in trainer.py, not as the primary optimization loss.
3. Current working preference is self-supervised-first with architecture exploration to reduce over-specialization risk and preserve broader cross-farm deployment potential.
4. Dense LiDAR labels are the preferred supervision source when adding supervised or hybrid training for Citrus Farm.
5. For publication fairness, compare methods under the same Citrus data budget and splits:
   - self-supervised baseline (RGB-only)
   - self-supervised variant with architecture improvements
   - optional stage-2 supervised variant using dense LiDAR labels
   - optional stage-2 hybrid variant (self-supervised + supervised depth)
6. Deployment note: LiDAR is required for label creation during training pipeline only; runtime inference remains RGB-only.
7. Strategy is still discussion-stage and not finalized; professor feedback is pending before locking implementation order.

## Verification Checklist

Before declaring dataset ready:

1. Timestamp overlap exists between extracted RGB and LiDAR.
2. Pairing delta statistics are acceptable.
3. Projection alignment looks correct on random visual samples.
4. Dense fill ratio and roughness metrics are stable across many frames.
5. train/val/test splits are generated and non-empty.
6. LiDAR-to-ZED transform convention is verified using calibration files and overlay panels.
7. Split policy is sequence/block/time-aware enough to avoid adjacent-frame leakage.
8. Existing dense outputs can be rerun or reused without losing split/metrics reproducibility.
9. ZED depth is used at least as a sanity-check reference against LiDAR-derived labels where valid.

## Research Reframing Snapshot (2026-04-15)

Working paper direction:

1. Target contribution should be framed as lightweight monocular depth estimation for vegetation-dense agricultural environments, validated first on Citrus Farm, not as a broad global SOTA monocular depth claim.
2. Lite-Mono remains the main efficiency baseline because it is a compact CVPR 2023 self-supervised monocular depth model originally validated mostly around urban/KITTI-style driving data.
3. The research gap is domain shift: vegetation, repetitive canopy texture, thin branches/leaves, partial occlusion, non-planar ground, lighting variation, and robot-scale agricultural navigation needs.
4. Runtime requirement remains RGB-only monocular inference for a pest-killing robot; LiDAR and ZED depth are offline training/evaluation assets only.
5. Paper-facing terminology should prefer "LiDAR-densified depth labels" or "dense LiDAR depth labels"; legacy project notes may still refer to the "densed lidar dataset" for continuity.
6. Advisor-suggested side questions, such as frame-motion sensitivity during self-supervised training, are worth tracking as later analysis candidates, but should not displace the current main milestone path unless later evidence or advisor feedback says otherwise.

## Codebase Review Snapshot (2026-04-15)

Observed from current repository review:

1. Citrus data preparation is mostly separate from the original Lite-Mono training stack.
2. trainer.py and evaluate_depth.py are still KITTI-centered; no Citrus Dataset class, Citrus evaluation script, or supervised/hybrid depth loss is wired into training yet.
3. Current `prepared_training_dataset/` output now exists locally with 5282 samples, so baseline evaluation and later Citrus integration can depend on a real built split instead of only audit/probe artifacts.
4. build_training_dataset.py now rebuilds manifest rows when dense files already exist and can force-regenerate dense outputs with `--no_skip_existing`.
5. Current builder default uses time-block grouped splitting; paper experiments should still confirm the split does not leak near-duplicate frames across train/val/test.
6. Densification quality must be treated as a first-class validation target before supervised/hybrid training, especially calibration correctness, support masks, fill ratio, and visual projection alignment.
7. Training-time depth metric logging now has a guard: default `--depth_metric_crop kitti_eigen` preserves KITTI behavior, but non-KITTI label shapes raise unless `--depth_metric_crop none` is used; `valid_mask` is also used when present.

## Proposed Paper Milestones (Quality Targets)

Milestone 0 - Dataset and calibration audit:

1. Regenerate prepared_training_dataset/ from the current extracted RGB/LiDAR data.
2. Produce pairing delta statistics, dense-label quality histograms, and random visual alignment panels.
3. Lock dataset version, build parameters, and split policy.

Milestone 1 - Baseline on Citrus:

1. Run original Lite-Mono pretrained weights on Citrus validation/test frames.
2. Evaluate against LiDAR-densified depth labels with Citrus-specific masks and metrics.
3. Record runtime, parameter count, FLOPs, and failure cases in vegetation-heavy scenes.

Milestone 2 - Citrus training integration:

1. Add a Citrus Dataset/DataLoader path that consumes prepared split manifests.
2. Add Citrus-specific evaluation independent of KITTI crops and file formats.
3. Keep original KITTI behavior available for comparison and regression safety.

Milestone 3 - Self-supervised Citrus adaptation:

1. Train/fine-tune Lite-Mono self-supervised on Citrus RGB sequences under fixed splits.
2. Compare against untouched original Lite-Mono using the same evaluation budget.
3. Analyze whether adaptation improves vegetation geometry without overfitting to one field/session.

Milestone 4 - Lightweight vegetation-focused architecture improvement:

1. Add one clearly motivated lightweight module or loss targeted at vegetation-dense failure modes.
2. Keep parameter/FLOP/runtime changes small enough to support the robot deployment story.
3. Run ablations against original Lite-Mono and self-supervised Citrus adaptation.

Milestone 5 - Optional supervised/hybrid extension:

1. Add LiDAR-densified depth supervision or a hybrid photometric + depth loss.
2. Treat this as stage-2 evidence unless professor feedback changes the paper direction.
3. Compare under the same split and data budget as self-supervised variants.

Milestone 6 - Paper package:

1. Report accuracy, robustness/failure cases, efficiency, and deployment relevance.
2. Include qualitative examples in canopy, aisle, trunk, ground, and high-occlusion scenes.
3. Document dataset construction enough for reproducibility.

## Timeline Snapshot (2026-05-05)

Done:

1. Extracted the current local Citrus RGB, ZED depth, and LiDAR subset.
2. Verified timestamp-based RGB-LiDAR pairing logic with same-session preference and optional fallback.
3. Audited four LiDAR-to-camera transform candidates and rejected the two clearly wrong routes.
4. Replaced the old default linear fill with conservative `local_idw` densification.
5. Ran small visual audits plus a 200-sample time-spread metrics probe.
6. Locked `exact_lidar_parent_child_inverted` as the final/default dense-label route.
7. Ran one original Lite-Mono qualitative sanity prediction on a Citrus RGB image.
8. Ran the full `prepared_training_dataset/` build and produced 5282 dense labels plus train/val/test split manifests.
9. Implemented the Milestone 1 evaluator through data loading, original Lite-Mono inference, valid-mask-aware metrics, aggregation, result saving, timing, and parameter metadata.
10. Ran the full original Lite-Mono baseline on the Citrus validation and test splits and saved full CSV/JSON result files.
11. Added the Milestone 1 result-analysis helper and generated first good/typical/bad validation visual panels.
12. Added a beginner-friendly visual interpretation note explaining what the good/typical/bad panels show about the original model's behavior.
13. Generated matching good/typical/bad visual panels for the test split.
14. Started Milestone 2 with a milestone-local Citrus prepared Dataset/DataLoader smoke slice.
15. Added a Milestone 2 temporal-neighbor diagnostic for self-supervised training readiness.
16. Added a Milestone 2 trainer-compatibility dry run for metadata-free temporal Citrus batches.
17. Added a Citrus-safe training-time depth-metric guard so KITTI crop assumptions cannot be silently applied to Citrus-shaped labels.
18. Wired Citrus into the root trainer dataset option path and verified one root `Trainer` Citrus batch smoke.
19. Verified one root Citrus optimizer-step smoke with finite loss, finite gradients, and an actual parameter update.
20. Added train-only Citrus color augmentation and reran the root Citrus one-step smoke successfully.

Current:

1. Milestone 0 is now complete through the full dataset build, with the final/default route and split policy materialized under `prepared_training_dataset/`.
2. Milestone 1 core baseline evidence is complete; optional broader failure taxonomy and FLOPs/deployment benchmarking are deferred for now.
3. `citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py` currently implements Slice 1 data inspection, Slice 2 optional Lite-Mono inference, Slice 3 valid-mask-aware metric comparison, Slice 4 aggregate metric summaries, Slice 5 optional CSV/JSON result saving, Slice 6 runtime/FPS metadata, and Slice 7 model parameter/checkpoint metadata.
4. `citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py` implements Slice 8 result interpretation support by selecting and rendering good/typical/bad samples from saved per-sample metrics.
5. Full validation/test baseline result files are saved under `citrus_project/milestones/01_original_lite_mono_baseline/results/`.
6. Validation/test visual panels are saved under `citrus_project/milestones/01_original_lite_mono_baseline/visuals/`.
7. `citrus_project/milestones/02_citrus_integration/citrus_prepared_dataset.py` now defines `CitrusPreparedDataset` for prepared split manifests, with target-only loading by default and optional same-split temporal triplets via `frame_ids=[0, -1, 1]`.
8. `citrus_project/milestones/02_citrus_integration/inspect_citrus_prepared_dataset.py` smoke-tests target-only or temporal loading through a PyTorch `DataLoader`.
9. `citrus_project/milestones/02_citrus_integration/inspect_temporal_neighbors.py` checks whether each prepared target frame has same-split, same-session previous/next RGB neighbors.
10. `citrus_project/milestones/02_citrus_integration/dry_run_lite_mono_temporal_batch.py` runs one metadata-free temporal Citrus batch through Lite-Mono depth, pose, projection, and reprojection-shape logic without editing root training code.
11. `trainer.py` and `options.py` now include the narrow Citrus-safe depth-metric guard: KITTI keeps the default `kitti_eigen` monitoring crop, while Citrus/non-KITTI labels must use `--depth_metric_crop none`.
12. `options.py` now accepts `--dataset citrus`, `--split citrus_prepared`, `--citrus_prepared_name`, and `--citrus_max_neighbor_delta_ms`.
13. `--depth_metric_crop auto` is now the CLI default: root trainer setup resolves it to `kitti_eigen` for KITTI and `none` for Citrus.
14. `trainer.py` can now build Citrus train/val loaders from `CitrusPreparedDataset` with metadata-free same-split temporal batches.
15. `citrus_project/milestones/02_citrus_integration/smoke_root_citrus_one_step_train.py` verifies one Citrus optimizer step through the root trainer path.
16. `CitrusPreparedDataset` now supports train-only ColorJitter-style augmentation for `color_aug`; validation/test samples keep `color_aug == color`.
17. Milestone 2 core integration is complete: Dataset/DataLoader, temporal triplets, root trainer selection, Citrus-safe depth metrics, color augmentation, forward/backward, and one optimizer step all pass, including a CUDA one-step smoke.
18. Milestone 3 standard self-supervised Citrus adaptation is now documented as a weak/negative adapted-baseline result, not an improvement. Full long training was not launched because short and near-epoch gates showed damaging relative-depth drift.
19. Milestone 3 run logs/checkpoints go under ignored `citrus_project/milestones/03_self_supervised_adaptation/runs/`; original `weights/lite-mono/` remains input-only.
20. Root trainer safety and compatibility changes now include:
   - default-off `--seed` reproducibility option for controlled short-run comparisons
   - `--max_train_steps` safety brake
   - Python 3-compatible `trainer.val()` iterator handling
   - modern torchvision ResNet pretrained-weight loading in `networks/resnet_encoder.py`
   - default-off `--freeze_depth_steps`
   - default-off `--freeze_depth_encoder`
   - default-off `--save_step_frequency` for optional step checkpoints during monitored runs
21. Milestone 3 short-run evidence so far:
   - smoke/checkpoint/resume path works on CUDA
   - pretrained pose construction and root trainer use now work
   - batch size 4 fits on the laptop RTX 4060 GPU
   - `diagnose_self_supervised_batch.py` records fixed-batch photo loss, loss decomposition, depth metrics, depth median, pose motion, automask, source selection, and warp OOB signals
22. Milestone 3 recipe search verdict so far:
   - naive self-supervised adaptation has not beaten the untouched baseline on the first 100 validation samples
   - photo loss can improve while LiDAR-valid depth metrics get worse
   - pose-only training can reduce photo loss, but if the full depth path is frozen, RGB-only depth inference is unchanged and first-100 validation metrics match the untouched baseline exactly
   - depth encoder BatchNorm drift alone causes only small metric movement in the current 50-step control
   - seeded warmup/depth trajectory shows median-scaled relative-depth quality worsens after as few as 5 depth-update steps
   - normal depth LR can improve raw scale while damaging median-scaled relative structure
   - lower depth LR, frozen depth encoder/BatchNorm, decoder-only updates, and previous-only temporal source have not fixed the issue
   - the terminal-controlled conservative 1000-step near-epoch probe also failed to recover: final first-100 median-scaled `abs_rel=0.6615`, `a1=0.1827`, worse than the untouched baseline `abs_rel=0.3680`, `a1=0.4807`
   - disabling Citrus color augmentation in a 250-step conservative control helped versus the color-augmented 250-step run, but still trailed the untouched baseline on median-scaled relative-depth quality: no-aug `abs_rel=0.4108`, `a1=0.4568`
   - extending no-color augmentation to 500 steps degraded again: first-100 median-scaled `abs_rel=0.5300`, `a1=0.3513`
23. Current likely failure pattern:
   - the self-supervised objective is changing predicted scale/structure in ways that are not aligned with Citrus LiDAR-valid depth quality
   - smoothness loss is tiny relative to photo loss in the fixed validation diagnostics
   - source-frame direction and encoder BatchNorm drift are not sufficient explanations by themselves
   - "just train longer with the same recipe" is not supported: the 1000-step conservative probe was already worse at step 250 and degraded further by step 500-1000
24. Detailed Milestone 3 command/result history lives in:
   - `citrus_project/milestones/03_self_supervised_adaptation/README.md`
   - `citrus_project/milestones/03_self_supervised_adaptation/beginner_progress_summary.md`
   - `citrus_project/research/baseline_notes.md`
   - ignored run folders under `citrus_project/milestones/03_self_supervised_adaptation/runs/`
25. The terminal-controlled conservative monitored probe has now been run by the user and checked:
   - `citrus_project/milestones/03_self_supervised_adaptation/run_controlled_decoderonly_lowdepthlr_1epoch.ps1`
   - `citrus_project/milestones/03_self_supervised_adaptation/evaluate_controlled_decoderonly_lowdepthlr.ps1`
   - recipe: original encoder/depth weights, pretrained pose, batch size 4, seed 0, drop path 0, 25-step depth optimizer warmup, frozen depth encoder/BatchNorm, low depth LR, 1000-step cap, and 250-step checkpoints
   - training stopped cleanly at `--max_train_steps=1000`
   - saved checkpoints: `step_250`, `step_500`, `step_750`, `step_1000`, and `weights_0`; `step_1000` and `weights_0` are identical
   - first-100 validation evaluations are saved under the run folder's `eval_val100_*` directories
   - result table: baseline median-scaled `abs_rel=0.3680`/`a1=0.4807`; step250 `0.4542`/`0.4290`; step500 `0.6325`/`0.2445`; step750 `0.6152`/`0.2366`; final1000 `0.6615`/`0.1827`
26. Milestone 3 visual comparison after the 1000-step probe:
   - helper: `citrus_project/milestones/03_self_supervised_adaptation/compare_original_vs_adapted_visuals.py`
   - outputs: `citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/visual_compare_original_vs_adapted_val100_weights_0/`
   - selected panels: adapted good index 12, adapted typical index 36, adapted bad index 75, and largest drop versus original index 48
   - visual verdict: the adapted checkpoint is smoother and less structurally specific; it loses tree/canopy/ground separation that the original baseline weakly preserved after median scaling, so the failure is relative-depth structure damage, not only global scale
27. Milestone 3 no-color-augmentation control:
   - run: `citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_noaug_250steps/`
   - recipe: original encoder/depth weights, pretrained pose, batch size 4, seed 0, drop path 0, 25-step depth optimizer warmup, frozen depth encoder/BatchNorm, low depth LR, `--citrus_color_aug_probability 0`, 250-step cap
   - training stopped cleanly at `--max_train_steps=250`; `step_250` and `weights_0` are identical
   - first-100 validation: raw `abs_rel=0.7192`, median-scaled `abs_rel=0.4108`, median-scaled `a1=0.4568`, median scale ratio `4.057223`
   - interpretation: no color augmentation helped compared with the color-augmented 250-step conservative run, but still did not beat the untouched baseline on relative depth; color jitter is likely a contributor, not the whole root cause
28. Milestone 3 no-color-augmentation 500-step control:
   - run: `citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_noaug_500steps/`
   - recipe: same as no-aug 250-step control, but `--max_train_steps 500` and `--save_step_frequency 250`
   - training stopped cleanly at `--max_train_steps=500`; saved `step_250`, `step_500`, and `weights_0`; `step_500` and `weights_0` are identical
   - first-100 validation: raw `abs_rel=0.7235`, median-scaled `abs_rel=0.5300`, median-scaled `a1=0.3513`, median scale ratio `4.322919`
   - interpretation: no color augmentation is still better than color augmentation at 500 steps, but it worsens from 250 to 500 and still does not beat the untouched baseline; this recipe should not be scaled further without a new method/technical reason
29. Milestone 3 closeout decision:
   - the tested standard self-supervised adaptation recipe family is closed as negative/weak baseline evidence
   - do not keep searching this same recipe family by running longer jobs
   - Milestone 4 should start from the documented failure target: preserve or improve Citrus relative depth structure while adapting to vegetation scenes
   - from-scratch training remains a possible later larger-data branch, not the immediate fix with the current 4275-triplet Citrus train split
30. Milestone 4 phase order decision:
   - Milestone 4 is planned as two method phases: Phase 1 occlusion masking and Phase 2 boundary-aware loss
   - the user chose to start with Phase 2 boundary-aware loss first, even though Phase 1 occlusion masking has not yet been implemented
   - future implementation should treat the existing Phase 2 documents as a boundary-awareness plan, but should not assume an M4a occlusion checkpoint already exists
31. Milestone 4 immediate work stance:
   - the user's current group role is to retrain/improve Lite-Mono using the Phase 2 boundary-aware loss plan
   - broader evaluation and comparison against later retrained models or expanded/new datasets is expected in the future, but the near-term focus is implementation, smoke testing, and controlled retraining for Phase 2

Next:

1. Treat Milestone 2 as core complete.
2. Start Milestone 4 implementation planning with Phase 2 boundary-aware loss as the first tested improvement, then compare against original Lite-Mono and the weak/negative Milestone 3 adapted baseline.
3. Do not launch another longer/full Milestone 3 training run without a new technical reason and explicit confirmation.
4. Prefer same-split, same-session `[-1, 0, 1]` RGB triplets with a 200 ms neighbor-gap cap for any future self-supervised runs; current temporal mode drops boundary samples that cannot form a full safe triplet.
5. Consider expanding Citrus Farm sequences before final Milestone 4/paper comparison if the current 4275 train triplets look too limited.
6. Prepare and share a small curated sample pack for Friend B's scene-taxonomy and qualitative-support work.

Later:

1. Propose and test one lightweight vegetation-focused improvement against original Lite-Mono and the documented Milestone 3 weak/negative adaptation baseline.
2. Optionally test supervised or hybrid training with dense LiDAR labels.
3. Assemble the paper package.

## Quick Commands

From citrus_project/dataset_workspace directory:

Download:

1. D:/Conda_Envs/lite-mono/python.exe download_citrusfarm_seq_01_lidar.py
2. D:/Conda_Envs/lite-mono/python.exe download_citrusfarm_seq_01_rgb_depth.py

Extract:

1. D:/Conda_Envs/lite-mono/python.exe extract_left_rgbd_from_raw.py 01_13B_Jackal extracted_rgbd
2. D:/Conda_Envs/lite-mono/python.exe extract_lidar_from_raw.py 01_13B_Jackal extracted_lidar

Build:

1. D:/Conda_Envs/lite-mono/python.exe build_training_dataset.py
2. Optional debug run: D:/Conda_Envs/lite-mono/python.exe build_training_dataset.py --max_samples 5
3. Alternate production-current debug run: D:/Conda_Envs/lite-mono/python.exe build_training_dataset.py --transform_mode production_current --max_samples 5 --no_skip_existing

Audit:

1. D:/Conda_Envs/lite-mono/python.exe audit_projection_alignment.py --max_samples 3
2. Inspect generated overlays/details under projection_alignment_audit/ before trusting LiDAR-densified labels.
3. D:/Conda_Envs/lite-mono/python.exe densify_lidar.py --compare_transform_modes
4. Time-spread metrics-only route probe: D:/Conda_Envs/lite-mono/python.exe audit_projection_alignment.py --max_samples 200 --metrics_only --output_dir projection_alignment_audit/time_spread_metrics_200
5. Final time-spread visual spot-check: D:/Conda_Envs/lite-mono/python.exe audit_projection_alignment.py --max_samples 12 --output_dir projection_alignment_audit/time_spread_visual_12

One-image original Lite-Mono Citrus sanity run:

1. Copy the selected RGB image into `citrus_project/research/generated/lite_mono_single_image_demo/` first, because this folder is ignored and not part of the dataset.
2. D:/Conda_Envs/lite-mono/python.exe test_simple.py --load_weights_folder weights/lite-mono --image_path citrus_project/research/generated/lite_mono_single_image_demo/zed_2023-07-18-14-26-49_0_bag_1689715609331936216.png --model lite-mono --no_cuda
3. Output appears next to the copied input image as `*_disp.jpeg` and `*_disp.npy`.

Milestone 1 Citrus evaluator:

1. Slice 1 data inspection from repo root:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 3`
2. Slice 2 and Slice 3 limited-sample model inference plus one-sample valid-mask-aware metrics from repo root:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 1 --run_model --no_cuda`
3. Slice 4 aggregate summary smoke run:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 3 --run_model --summary_only --progress_interval 1 --no_cuda`
4. Slice 4 full-split aggregate command pattern:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 0 --run_model --summary_only`
5. Slice 5 saved-result smoke run:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 3 --run_model --summary_only --progress_interval 1 --no_cuda --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results`
6. Slice 6 GPU timing smoke run:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 3 --run_model --summary_only --progress_interval 1 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results`
7. Slice 7 parameter-metadata smoke run:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 2 --run_model --summary_only --progress_interval 1 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results`
8. Full validation/test baseline runs:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split val --max_samples 0 --run_model --summary_only --progress_interval 50 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results`
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/evaluate_lite_mono_citrus.py --split test --max_samples 0 --run_model --summary_only --progress_interval 50 --output_dir citrus_project/milestones/01_original_lite_mono_baseline/results`
9. Slice 8 validation visual-analysis run:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py --split val`
10. Slice 10 test visual-analysis run:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py --split test`
11. Current Slice 1 behavior:
   - reads `prepared_training_dataset/splits/<split>_pairs.txt`
   - joins split entries with `prepared_training_dataset/metrics/all_samples.csv`
   - prints RGB size, dense-label shape/stats, valid-mask shape/stats, valid-pixel ratio, and pairing diagnostics
12. Current Slice 2 behavior:
   - loads `weights/lite-mono`
   - runs original Lite-Mono on selected RGB samples
   - prints input tensor, raw closeness level, scaled disparity, predicted depth, and resized depth summaries
13. Current Slice 3 behavior:
   - compares resized predicted depth against LiDAR-densified labels only on valid-mask pixels
   - uses evaluation label depth cap `eval_min_depth=0.001` and `eval_max_depth=80.0` by default, matching the original Lite-Mono/KITTI evaluation convention
   - prints raw-scale and median-scaled one-sample metrics: `abs_rel`, `sq_rel`, `rmse`, `rmse_log`, `a1`, `a2`, and `a3`
14. Current Slice 4 behavior:
   - uses per-image metric means for aggregate summaries, matching original Lite-Mono evaluation style
   - supports `--summary_only` to suppress per-sample details during multi-sample runs
   - supports `--max_samples 0` or less to evaluate the full selected split
15. Current Slice 5 behavior:
   - supports `--output_dir` to save one aggregate `*_summary.json` file and one `*_per_sample.csv` file
   - stores result outputs under `citrus_project/milestones/01_original_lite_mono_baseline/results/` when that folder is passed as `--output_dir`
   - ignores `maxN` smoke-result JSON/CSV files by default so they are not mistaken for official full-split results
16. Current Slice 6 behavior:
   - summary JSON includes timing metadata: model load seconds, evaluation-loop seconds, total run seconds, sample throughput, model-forward seconds, and model-forward FPS
   - per-sample CSV includes `sample_wall_seconds`, `model_forward_seconds`, and `model_forward_fps`
   - timing is evaluator timing, not a final optimized deployment benchmark; small GPU smoke runs include warmup overhead
17. Current Slice 7 behavior:
   - prints encoder, depth-decoder, and total depth-inference parameter counts when model inference is enabled
   - summary JSON includes `model_info` with encoder/depth-decoder parameter counts, trainable counts, checkpoint file sizes, and a note that the training-only pose network is not included
   - current `lite-mono` depth-inference path reports 3,074,747 parameters total: 2,848,120 encoder parameters and 226,627 depth-decoder parameters
18. Current Slice 8 behavior:
   - reads `*_full_per_sample.csv` result files
   - selects good, typical, and bad samples by a metric, defaulting to `median_scaled_a1`
   - reruns inference only for selected samples
   - saves RGB/prediction/label/mask/error visual panels plus selection summary CSV/JSON files under the Milestone 1 `visuals/` folder
19. Current Slice 9 behavior:
   - adds `citrus_project/milestones/01_original_lite_mono_baseline/visual_interpretation.md`
   - explains how to read the visual panels in plain language
   - records the first qualitative interpretation: original Lite-Mono can recover broad layout in some Citrus scenes, but often smooths over or misrepresents vegetation, row gaps, canopy shapes, and tree/ground boundaries even after median scaling
20. Current Slice 10 behavior:
   - runs the same good/typical/bad visual selection on the test split
   - confirms the validation qualitative interpretation is also visible in held-out test examples

Milestone 2 Citrus prepared Dataset/DataLoader smoke:

1. From repo root:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/inspect_citrus_prepared_dataset.py --samples_per_split 2 --batch_size 2`
2. Current Slice 1 behavior:
   - reads `prepared_training_dataset/splits/<split>_pairs.txt`
   - joins split entries with `prepared_training_dataset/metrics/all_samples.csv`
   - loads RGB, dense LiDAR labels, valid masks, timestamps, session tokens, and manifest metadata
   - returns model-sized RGB tensors by default (`3 x 192 x 640`)
   - keeps dense labels and valid masks at native size (`1 x 720 x 1280`)
   - returns Citrus ZED-left camera intrinsics as `K`, `inv_K`, and `K_normalized`
   - provides pinhole intrinsics only; distortion coefficients are not passed through because Lite-Mono warping expects a pinhole camera matrix and the active RGB topic is `/zed2i/zed_node/left/image_rect_color`
   - supports temporal mode with same-split, same-session `frame_ids=[0, -1, 1]`
   - temporal mode exposes Lite-Mono-style keys such as `("color", -1, 0)`, `("color", 0, 0)`, `("color", 1, 0)`, `("K", 0)`, and `("inv_K", 0)`
   - `include_metadata=False` can be used later for trainer-facing batches where every value must support `.to(device)`
3. Latest smoke result:
   - train split loaded: 4311 samples
   - validation split loaded: 564 samples
   - default DataLoader smoke batch size: 2
   - resized 640 x 192 Citrus K starts with `fx=263.77954`, `fy=140.94998`, `cx=323.59875`, `cy=95.26605`
4. Temporal DataLoader smoke command:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/inspect_citrus_prepared_dataset.py --temporal --samples_per_split 2 --batch_size 2 --splits train val`
5. Latest temporal DataLoader smoke result:
   - train temporal dataset length: 4275 safe triplet targets
   - validation temporal dataset length: 560 safe triplet targets
   - frame `0`, `-1`, and `1` RGB tensors each batch as `2 x 3 x 192 x 640`
   - target dense labels and valid masks remain native size, `2 x 1 x 720 x 1280`
6. Trainer-facing metadata check:
   - `CitrusPreparedDataset(frame_ids=[0, -1, 1], include_metadata=False)` produced one sample with 45 tensor-like values and no non-tensor values.

Milestone 2 temporal-neighbor diagnostic:

1. From repo root:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/inspect_temporal_neighbors.py`
2. Current Slice 2 behavior:
   - checks same-split, same-session previous and next neighbors for each prepared target frame
   - reports how many targets can form safe `previous/current/next` triplets under `--max_neighbor_delta_ms`, default `200.0`
   - reports when the nearest global neighbor would cross a train/val/test boundary, so trainer integration can avoid split leakage
3. Latest default-threshold result:
   - all prepared samples inspected: 5282
   - train safe triplets: 4275 / 4311 (99.16%)
   - validation safe triplets: 560 / 564 (99.29%)
   - test safe triplets: 399 / 407 (98.03%)
   - same-split neighbor deltas are about 100 ms median in all splits; max same-split delta was 159.911 ms in train, 137.273 ms in validation, and 128.504 ms in test
4. Current interpretation:
   - Citrus has enough same-split temporal neighbors for self-supervised training, but boundary samples and cross-split global neighbors must be handled explicitly.

Milestone 2 trainer-compatibility dry run:

1. From repo root:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/dry_run_lite_mono_temporal_batch.py --batch_size 2 --no_cuda`
2. Current Slice 3 behavior:
   - consumes a metadata-free temporal Citrus batch from `CitrusPreparedDataset(frame_ids=[0, -1, 1], include_metadata=False)`
   - builds the Lite-Mono depth encoder/decoder plus the ResNet pose encoder/decoder
   - runs the current RGB frame through the depth path
   - predicts relative poses for previous and next RGB frames
   - uses `BackprojectDepth`, `Project3D`, and `grid_sample` to synthesize warped source images
   - computes a small L1 reprojection smoke loss
   - does not load pretrained weights, update weights, or edit root `trainer.py`; it is a batch/key/shape contract check only
3. Latest CPU dry-run result:
   - syntax check passed
   - CPU dry runs passed with `--batch_size 1 --no_cuda` and `--batch_size 2 --no_cuda`
   - train temporal samples available: 4275
   - batch size 2 used 45 tensor-like batch values and no non-tensor metadata
   - frame `0`, `-1`, and `1` RGB tensors each had shape `2 x 3 x 192 x 640`
   - `depth_gt` and `valid_mask` had shape `2 x 1 x 720 x 1280`
   - disparity outputs were produced at scales 0, 1, and 2
   - warped source RGB tensors for frames `-1` and `1` had shape `2 x 3 x 192 x 640`
   - reprojection smoke loss was `0.076165` in the batch-size-2 CPU smoke run
4. Current interpretation:
   - the Citrus temporal batch is compatible with the core Lite-Mono depth, pose, projection, and reprojection shape path
   - wider root trainer integration is still pending, and Citrus training should use the later depth-metric guard with `--depth_metric_crop none`

Milestone 2 Citrus-safe depth-metric guard:

1. From repo root:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_depth_metric_guard.py`
2. Current Slice 4 behavior:
   - adds `--depth_metric_crop` to `options.py`
   - keeps the default as `kitti_eigen`, preserving original KITTI training-time depth metric behavior
   - adds `none` as the non-KITTI/Citrus mode so depth metrics use native label geometry instead of the KITTI crop
   - resizes predicted depth to the actual `depth_gt` shape before metric logging
   - uses `inputs["valid_mask"]` when present, so Citrus metrics can ignore invalid LiDAR-label pixels
   - raises a clear error if `kitti_eigen` is used with non-KITTI-shaped labels, instead of silently applying the wrong crop
3. Latest smoke result:
   - `smoke_depth_metric_guard.py` passed
   - syntax-only compile for `trainer.py`, `options.py`, and the smoke script passed
4. Current interpretation:
   - this is a safety guard for future Citrus training integration, not full Citrus root training wiring yet
   - future Citrus training commands should use `--depth_metric_crop none` unless the root integration automatically selects it for the Citrus dataset

Milestone 2 root Citrus trainer wiring:

1. From repo root:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_root_citrus_trainer_wiring.py`
2. Current Slice 5 behavior:
   - root `options.py` accepts `--dataset citrus`
   - root trainer auto-resolves Citrus defaults from `--dataset citrus`: `split=citrus_prepared`, `data_path=citrus_project/dataset_workspace`, and `depth_metric_crop=none`
   - explicit `--dataset citrus --depth_metric_crop kitti_eigen` is rejected before trainer setup
   - root trainer builds Citrus train/val DataLoaders from the Milestone 2 `CitrusPreparedDataset`
   - the smoke script monkeypatches TensorBoard with a no-op writer because the current sandbox blocks TensorBoardX multiprocessing pipes; real training still uses the normal `SummaryWriter`
   - the smoke uses `--weights_init scratch`, `--no_cuda`, `batch_size=1`, and one batch only; it does not perform an optimizer update
3. Latest smoke result:
   - syntax-only compile passed for `trainer.py`, `options.py`, `smoke_root_citrus_trainer_wiring.py`, and `smoke_depth_metric_guard.py`
   - `smoke_depth_metric_guard.py` passed
   - `train.py --help` shows `citrus`, `citrus_prepared`, and `depth_metric_crop {auto,kitti_eigen,none}`
   - root Citrus trainer wiring smoke passed
   - resolved `data_path`: `D:\IBPI\Image Proc-AI Assisted-SP1\Lite-Mono\citrus_project\dataset_workspace`
   - resolved `split`: `citrus_prepared`
   - resolved `depth_metric_crop`: `none`
   - train samples: 4275
   - validation samples: 560
   - latest one-batch photometric loss was finite: `0.161647`
   - latest one-batch depth `abs_rel` monitor was finite: `0.832625`
   - one-batch smoke loss values can change between runs because the root train DataLoader shuffles samples
4. Current interpretation:
   - root training can now select Citrus and consume one Citrus temporal batch through the normal trainer path
   - this is still a smoke-test slice, not an actual adaptation experiment
   - Citrus color augmentation is now handled in the later Slice 7 smoke section

Milestone 2 root Citrus one-step optimizer smoke:

1. From repo root:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_root_citrus_one_step_train.py`
   - Optional CUDA version: `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_root_citrus_one_step_train.py --use_cuda`
2. Current Slice 6 behavior:
   - builds the root `Trainer` with `--dataset citrus`, CPU, `batch_size=1`, `weights_init=scratch`, and no-op TensorBoard writer for the sandbox
   - loads one Citrus temporal training batch through the normal root train DataLoader
   - runs `Trainer.process_batch`
   - checks the training loss is finite
   - runs optimizer zero-grad, backward, finite-gradient check, and one AdamW step for depth and pose optimizers
   - verifies at least one encoder parameter changed after the optimizer step
   - does not save a checkpoint or start a real epoch/fine-tuning run
3. Latest smoke result:
   - syntax-only compile passed for root and Milestone 2 smoke scripts
   - `smoke_depth_metric_guard.py` passed
   - `smoke_root_citrus_trainer_wiring.py` passed
   - `smoke_root_citrus_one_step_train.py` passed
   - resolved `data_path`: `D:\IBPI\Image Proc-AI Assisted-SP1\Lite-Mono\citrus_project\dataset_workspace`
   - resolved `split`: `citrus_prepared`
   - resolved `depth_metric_crop`: `none`
   - train samples: 4275
   - validation samples: 560
   - one-step loss before update: `0.139443`
   - max checked encoder parameter delta after update: `0.0000050217`
4. Current interpretation:
   - root Citrus training wiring now supports forward pass, backward pass, finite gradients, and one optimizer update
   - this is still only a smoke test, not a meaningful adaptation result
   - color augmentation is now handled in the later Slice 7 smoke section

Milestone 2 Citrus color augmentation:

1. From repo root:
   - `D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/02_citrus_integration/smoke_citrus_color_augmentation.py`
2. Current Slice 7 behavior:
   - `CitrusPreparedDataset` accepts `is_train` and `color_augmentation_probability`
   - train-mode samples apply a fixed ColorJitter-style transform to all frames in one temporal sample when augmentation is selected
   - validation/test samples keep `color_aug` identical to `color`
   - root trainer passes `is_train=True` for Citrus train split and `is_train=False` for Citrus validation split
   - root trainer exposes `--citrus_color_aug_probability`, default `0.5`
3. Latest smoke result:
   - `smoke_citrus_color_augmentation.py` passed
   - train samples: 4275
   - validation samples: 560
   - forced train augmentation mean absolute `color_aug - color` difference: `0.069748`
   - forced validation mean absolute `color_aug - color` difference: `0.000000`
   - root Citrus trainer wiring smoke passed after adding augmentation
   - root Citrus one-step training smoke passed after adding augmentation
   - one-step loss before update after augmentation change: `0.154858`
   - max checked encoder parameter delta after update: `0.0000050217`
   - CUDA one-step smoke later passed after the laptop GPU became visible:
     - device: `cuda`
     - GPU: NVIDIA GeForce RTX 4060 Laptop GPU
     - loss before update: `0.198368`
     - max checked encoder parameter delta after update: `0.0000050217`
4. Current interpretation:
   - Milestone 2 core integration is complete
   - the next milestone should be Milestone 3 controlled self-supervised Citrus adaptation, starting with a short run plan rather than a long training launch

Milestone 3 compact experiment status:

1. Scope:
   - Milestone 3 is searching for a fair Citrus self-supervised adaptation recipe for original Lite-Mono.
   - All runs so far are smoke/pilot scale; no long/full Citrus training run has started.
   - Detailed command/output history lives in `citrus_project/milestones/03_self_supervised_adaptation/README.md` and `citrus_project/research/baseline_notes.md`.
   - Beginner-friendly explanation lives in `citrus_project/milestones/03_self_supervised_adaptation/beginner_progress_summary.md`.
2. Active code/config additions:
   - `--seed`: default-off reproducibility option for controlled short-run comparisons.
   - `--max_train_steps`: default-off safety brake for short runs.
   - `trainer.val()` uses `next(self.val_iter)` for Python 3 iterator compatibility.
   - `networks/resnet_encoder.py` supports modern torchvision pretrained ResNet weights.
   - `--freeze_depth_steps`: default-off pose warmup/depth optimizer freeze.
   - `--freeze_depth_encoder`: default-off encoder/BatchNorm freeze; unsupported with `--pose_model_type shared`.
   - `--save_step_frequency`: default-off step checkpoint interval for monitored terminal runs.
   - `diagnose_self_supervised_batch.py`: fixed-batch diagnostic helper, including `--freeze_depth_encoder`, `--weights_init`, `--frame_ids`, deterministic `--seed`, and loss-decomposition fields.
3. Current pilot verdict:
   - Original first-100 validation reference: raw `abs_rel=0.7289`; median-scaled `abs_rel=0.3680`, `a1=0.4807`.
   - Seeded 25-step pose-warmup-only point stayed close to baseline: median-scaled `abs_rel=0.3758`, `a1=0.4797`.
   - Seeded 30-step point, after only 5 depth-update steps, improved raw `abs_rel=0.6781` but worsened median-scaled `abs_rel=0.3902`, `a1=0.4484`.
   - Seeded 40-step and 50-step points worsened median-scaled metrics further; the seeded 50-step point reached median-scaled `abs_rel=0.6354`, `a1=0.2280`.
   - Normal-depth-LR 50-step warmup/depth update improved raw `abs_rel=0.4946` but worsened median-scaled `abs_rel=0.5766`, `a1=0.3135`.
   - Low-depth-LR 50-step, decoder-only 50-step, and previous-only 50-step all still trailed the untouched baseline on first-100 validation.
   - The safest pilot was 25-step depth-frozen pose warmup, which stayed close to baseline but did not adapt trainable depth weights.
4. Diagnostic finding:
   - Fixed-batch diagnostics show photo loss can improve while LiDAR-valid depth metrics worsen.
   - Predicted-depth median/scale drift is a key failure signal.
   - Scale-0 smoothness is tiny compared with selected photo loss in the current fixed-batch diagnostics.
   - Pose-only controls indicate the larger failures appear when trainable depth parameters update, not when pose alone learns.
   - Source-frame direction and encoder BatchNorm drift are not sufficient explanations by themselves.
5. Current next technical direction:
   - Treat the tested Milestone 3 recipe family as closed negative/weak baseline evidence.
   - Do not scale existing recipes into a full long run.
   - The terminal-controlled conservative 1000-step probe completed but did not recover; final first-100 median-scaled `abs_rel=0.6615` and `a1=0.1827`, worse than the untouched baseline.
   - The no-color-augmentation 250-step control reduced the damage compared with color augmentation, but still did not beat the untouched baseline; the 500-step no-augmentation continuation worsened again.
   - Next work should move to Milestone 4 method planning. The method should target structure preservation or vegetation-aware depth cues without simply copying the weak original model.

Milestone 4 hybrid checkpoint scan result:

1. The required checkpoint scan was completed on 2026-05-22 for the hybrid supervised run `hybrid_supervised_b12_30ep_logl1_abs_w01_fresh_sched`.
2. All 30 checkpoints (`weights_0` through `weights_29`) were evaluated on the validation split.
3. The best validation checkpoint by raw abs_rel is `weights_13`, not the final `weights_29`.
4. Top validation candidates were then checked on the test split: `weights_13`, `weights_8`, and `weights_10`.
5. `weights_13` also won among those candidates on test raw abs_rel.
6. Corrected sweep files are saved under:
   - `C:/Proj/lite-Mono/citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/results/hybrid_supervised_b12_30ep_logl1_abs_w01_fresh_sched_checkpoint_sweep/`
7. Key metrics:
   - `weights_13` validation raw abs_rel/a1: `0.1716` / `0.8131`
   - `weights_13` validation median-scaled abs_rel/a1: `0.1746` / `0.8160`
   - `weights_13` test raw abs_rel/a1: `0.1620` / `0.8149`
   - `weights_13` test median-scaled abs_rel/a1: `0.1677` / `0.8159`
   - `weights_29` validation raw abs_rel/a1: `0.1913` / `0.7968`
   - `weights_29` validation median-scaled abs_rel/a1: `0.1933` / `0.7805`
8. Current recommendation: treat `weights_13` as the best hybrid supervised checkpoint from the fresh 30-epoch run, then generate visual comparisons for `weights_13` before preparing the LiDAR-aware edge-loss experiment.
9. Interpretation: the 30-epoch run was still useful, but the best checkpoint occurred mid-run. Do not automatically report the final epoch as best.
10. Visual comparisons for `weights_13` were generated on 2026-05-22:
   - `C:/Proj/lite-Mono/citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/results/hybrid_supervised_b12_30ep_logl1_abs_w01_fresh_sched_checkpoint_sweep/weights_13_visual_comparisons/`
11. Visual interpretation so far: `weights_13` is not better on every single selected sample, but it improves typical/good samples versus `weights_29`; the final epoch appears to have traded away some relative-depth fit in common cases rather than producing a catastrophic visual collapse.
12. Progress-presentation package for the user's 2026-05-26 presentation was prepared under:
   - `C:/Proj/lite-Mono/citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/presentation_2026_05_26_hybrid_progress/`
   - includes `PPT_BULLETS_AND_SCRIPT.md`, metric graphs, checkpoint-sweep graphs, Plain Citrus versus Hybrid `weights_13` panels, and `weights_29` versus `weights_13` panels.
13. The presentation script was updated to add a dedicated slide explaining why the project moved from pure self-supervised training to hybrid supervised training: pure photometric self-supervision improved image reconstruction signals but did not reliably improve Citrus depth metrics, while masked LiDAR depth supervision stabilizes absolute scale during training without changing RGB-only inference.
14. The same presentation package was copied into the active long-path workspace at:
   - `citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/presentation_2026_05_26_hybrid_progress/`
   - this copy also includes the new "Why We Switched From Pure Self-Supervised Training" slide.
15. The presentation script was condensed for group-slide contribution: the old Slides 7-13 were reduced to three slides covering checkpoint/visual evidence, LiDAR-aware edge-loss next plan, and closing summary.
16. The presentation script now explicitly explains the hybrid dataset arrangement: RGB frames and dense LiDAR labels are timestamp-paired in the prepared dataset, but they are not stacked side by side; RGB goes into Lite-Mono while dense LiDAR depth plus valid mask are separate tensors used only for supervised depth loss during training.
17. The presentation script also explains why Plain Citrus test raw a1 is `0.0077`: it is not a graph error, but a consequence of the Plain model's raw absolute scale being badly wrong; after median scaling, Plain Citrus a1 rises substantially, showing some relative structure but poor raw scale.
18. The presentation package now includes a median-scaled-only comparison graph, `graph_median_scaled_plain_vs_hybrid_w13.png`, and the script explicitly states the honest metric interpretation: the biggest win is raw absolute scale, but Hybrid `weights_13` still beats Plain Citrus after median scaling on test (`abs_rel 0.4889 -> 0.1677`, `a1 0.6582 -> 0.8159`), so relative depth quality also improved.
19. Added and ran `compare_plain_medianscaled_vs_weights13.py` to render Plain Citrus median-scaled visual panels against Hybrid `weights_13` raw predictions.
20. New Plain-median-scaled versus Hybrid-raw comparison outputs are saved under:
   - `C:/Proj/lite-Mono/citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/results/hybrid_supervised_b12_30ep_logl1_abs_w01_fresh_sched_checkpoint_sweep/weights_13_visual_comparisons/plain_medianscaled_vs_weights13_raw_val/`
   - `C:/Proj/lite-Mono/citrus_project/milestones/04_lightweight_vegetation_improvement/Marvel/results/hybrid_supervised_b12_30ep_logl1_abs_w01_fresh_sched_checkpoint_sweep/weights_13_visual_comparisons/plain_medianscaled_vs_weights13_raw_test/`
21. Presentation-friendly copies of all six new panels are in the `presentation_2026_05_26_hybrid_progress/assets/` folder using names like `visual_plain_medianscaled_vs_weights13_test_typical.png`; the slide script now points to these median-scaled comparison panels.
22. Presentation-friendly copies of all six existing epoch-29-versus-epoch-13 panels are also in the same assets folder using names like `visual_w29_vs_w13_test_typical.png`; these panels compare the final checkpoint against selected checkpoint `weights_13` after median scaling both predictions.
23. `graph_metric_summary_table.png` in the presentation assets was simplified to remove the Val Raw and Test Raw rows; it now shows only Val/Test median-scaled abs_rel and a1 for Plain Citrus versus Hybrid `weights_13`.
24. Added `PRESENTATION_6_MIN_SCRIPT.md` as a shorter presentation script with one compact speaking paragraph per slide, suggested visuals, and short backup answers for likely questions.
25. Added `PRESENTATION_6_MIN_SCRIPT_GOOGLE_DOCS.docx` as a Google-Docs-friendly document version of the concise 6-minute script; the file is present in both the active long-path workspace and the `C:/Proj/lite-Mono` presentation package.
26. Added `LAB_COMPUTER_SETUP.md` as a clean-transfer/lab-machine onboarding note covering tmux, environment setup, dataset download paths, dataset preparation order, and the reminder not to commit datasets/weights/runs.
27. Tightened `.gitignore` for lab-transfer safety so future weights/checkpoints, milestone runs/results/snapshots/logs, and log files do not flood source control after training or evaluation on the lab machine.
28. Lab computer dataset build status on 2026-06-03: the transfer repo build completed under `~/lite-mono-citrus-lab-transfer` using `build_training_dataset.py --workers 8`, final/default transform `exact_lidar_parent_child_inverted`, 5683 RGB frames found, 4918 RGB-LiDAR samples paired/built, and partial dense files were successfully reused after an interrupted first run.
29. Lab split verification on 2026-06-03: prepared dataset split counts are train=3947, val=564, test=407, total=4918. Planned first lab training gate is a hybrid supervised half-epoch run at batch size 12, approximately 164 optimizer steps, before any longer training.
30. Transfer repo fix on 2026-06-03: the first clean transfer repo copy missed the full `Marvel/hybrid_supervised_draft` code because the active long-path workspace only had part of the folder. The clean transfer repo was patched from `C:/Proj/lite-Mono` to include `train_hybrid_supervised.py`, milestone-local `trainer.py`, `options.py`, `layers.py`, and the hybrid run/postprocess scripts. The lab machine still needs `weights/lite-mono/lite-mono-pretrain.pth` copied/downloaded separately because weights are intentionally not committed.

## Change Log

- 2026-03-31: Created AGENTS.md with mandatory read/update workflow and Citrus pipeline context.
- 2026-03-31: Captured overlap-window pairing policy and prepared dataset artifact contract.
- 2026-03-31: Added terminology contract (densed lidar dataset vs depth dataset), clarified no ZED densification script, and documented research strategy/fair-comparison guidance.
- 2026-03-31: Added professor report package (strategy report, 90-second script, Q&A sheet) under reports/professor for structured advisor feedback.
- 2026-03-31: Updated strategy framing to self-supervised-first (discussion-stage), with supervised/hybrid positioned as optional stage-2 comparisons pending professor feedback; refreshed professor-facing report tone to casual update style.
- 2026-04-01: Updated context paths after citrus-farm-dataset rename pass (extract scripts, densify script, and prepared dense label folder naming).
- 2026-04-01: Synced renamed citrus paths in code artifacts (builder import now uses densify_lidar, builder output uses dense_lidar_npz, and prepared split/metrics manifests now reference dense_lidar_npz consistently).
- 2026-04-01: Added latest local data snapshot after one-base/21-zed pull; captured expanded extracted_rgbd/extracted_lidar counts and storage impact, plus note that prepared outputs are currently not present locally.
- 2026-04-11: Added .github/copilot-instructions.md with verified run commands, cross-file architecture overview, and repository-specific conventions for future Copilot sessions.
- 2026-04-14: Updated densify_lidar/build_training_dataset pairing policy to support same-session preference plus optional any-session fallback within max delta; added CLI toggles and regression tests for fallback behavior.
- 2026-04-15: Added paper-oriented research reframing, codebase review findings, and proposed quality-target milestones for Citrus/Lite-Mono publication planning.
- 2026-04-15: Reworked project context to state the publishable research-paper goal, document official Citrus Farm dataset intent, distinguish author-intended extraction from our derived LiDAR-densified label pipeline, and record dataset-processing quality concerns.
- 2026-04-15: Fixed build_training_dataset reproducibility issues: reused dense outputs now still generate manifest rows, added force-regeneration toggle, time-block grouped splitting, valid-mask artifacts, optional ZED-depth sanity metrics, and regression tests.
- 2026-04-15: Added projection alignment audit script and generated a 3-sample diagnostic audit for manual review; audit outputs are ignored by git.
- 2026-04-15: Recorded manual projection-audit result: production_current and exact_lidar_parent_child_inverted look visually plausible, while the other two transform candidates are clearly wrong; production_current remains active for now.
- 2026-04-15: Integrated exact_lidar_parent_child_inverted as a selectable densification/build transform mode for side-by-side dense-label comparison; alternate builder runs default to a separate prepared_training_dataset_exact_lidar_parent_child_inverted folder.
- 2026-04-15: Removed mixed old projection_alignment_audit outputs and regenerated a clean 12-sample projection alignment audit for manual comparison of production_current versus exact_lidar_parent_child_inverted before full dataset generation.
- 2026-04-15: Recorded user review of the clean 12-sample audit as a visual tie between production_current and exact_lidar_parent_child_inverted; production_current remains the default pending quantitative ZED/model checks.
- 2026-04-15: Clarified that LiDAR-densified labels and valid masks are numeric NPZ artifacts for training/evaluation, while PNG depth panels are human-facing diagnostics or future paper figures.
- 2026-04-15: Updated audit detail visualizations so LiDAR labels include a paper-style inverse-depth view ("near bright") and support-distance maps are clearly labeled as not depth; regenerated the 12-sample audit outputs.
- 2026-04-15: Ran 50-sample metrics probes for production_current and exact_lidar_parent_child_inverted; exact_inverted had much lower ZED-vs-LiDAR median error on overlap but lower dense fill/overlap, so transform choice remains open pending a time-spread probe.
- 2026-04-15: Added reports/professor/citrus_farm_projection_progress_script.md as a digestible presentation script and screen-share guide for explaining overlay checks, LiDAR-densified labels, interpolation risk, and metrics tradeoffs.
- 2026-04-15: Updated audit_projection_alignment.py so 12-sample audit outputs include separate dense-label detail folders for both plausible routes: details_production_current and details_exact_lidar_parent_child_inverted.
- 2026-04-15: Reworked reports/professor/citrus_farm_projection_progress_script.md into a slide-oriented, layman-friendly presentation guide with simpler terms and explicit visual assets to show.
- 2026-04-15: Removed the old reports/professor folder and replaced it with reports/citrus_farm_dataset_processing_presentation.md as the current slide/script guide for explaining calibration/line-up checks, densification, interpolation limits, metrics probes, and why the final dataset is not locked yet.
- 2026-04-15: Added reports/citrus_farm_dataset_processing_presentation_concise.md as a 2-3 slide version focused on calibration, densification, and the early route-selection decision; kept the longer script as a backup for deeper discussion.
- 2026-04-15: Fixed audit sparse-depth subplot visibility in audit_projection_alignment.py by using nearest-neighbor rendering and a non-transparent masked color (black) so projected sparse LiDAR scanlines no longer disappear against white panel backgrounds.
- 2026-04-15: Brightened sparse LiDAR depth scanline colors in audit_projection_alignment.py (display-only) by using a brightened turbo colormap for the sparse-depth subplot so projected lines are easier to see while preserving the same underlying depth values and metrics.
- 2026-04-15: Further enhanced sparse LiDAR depth readability in audit_projection_alignment.py by using percentile-normalized inverse-depth coloring plus light display-only line dilation so sparse scanlines appear visibly brighter/thicker on the black background.
- 2026-04-15: Replaced default dense-label interpolation from global `linear` grid interpolation to conservative `local_idw` in densify_lidar.py, build_training_dataset.py, and audit_projection_alignment.py; local_idw fills near sparse LiDAR support but rejects pixels where nearby measured depths disagree, reducing fake vegetation/ground surfaces at the cost of lower coverage.
- 2026-04-16: Verified AGENTS.md against current workspace after outside edits; marked the 50-sample metrics probes as legacy `linear` artifacts, added the current 12-sample `local_idw` audit metrics, and removed the stale current-artifact reference to the deleted concise presentation guide.
- 2026-04-16: Reworked reports/citrus_farm_dataset_processing_presentation.md into a 4-slide guide for the user's presentation section, with more slide-ready text and simple speaker notes covering line-up checks, sparse-to-semidense labels, valid masks, route metrics, and the next validation step.
- 2026-04-16: Added reports/slide4_route_comparison_table.html as a screenshot-friendly Route A versus Route B metrics table for Slide 4, and updated the presentation guide with simple explanations for each metric.
- 2026-04-16: Removed the temporary Slide 4 HTML screenshot helper after use; kept the slide guide's metric explanations and table guidance.
- 2026-04-16: Extended reports/citrus_farm_dataset_processing_presentation.md to a 5-slide guide with a closing "next stage" slide that links the dataset audit to the proposed research milestones and clarifies that milestones are proposed targets pending advisor feedback.
- 2026-04-16: Ran one original Lite-Mono pretrained sanity prediction on an extracted Citrus RGB frame, recorded the command/output files, and clarified that this starts but does not complete the Citrus baseline milestone.
- 2026-04-16: Removed the generated original Lite-Mono `*_disp` outputs from the extracted RGB dataset folder, reran the one-image demo from an ignored generated-artifact folder, and kept demo artifacts separate from dataset artifacts.
- 2026-04-16: Added metrics-only projection audit support, hardened projection against non-finite projected points, and ran a 200-sample time-spread local_idw route probe; `exact_lidar_parent_child_inverted` had lower ZED absolute and relative error on all 200 paired comparisons while `production_current` kept higher dense coverage.
- 2026-04-16: Added the readable Markdown summary for the 200-sample metrics-only route probe, because the raw output is CSV/JSON rather than paper-friendly Markdown.
- 2026-04-16: Tidied research artifacts by moving paper-useful notes out of reports/ into citrus_project/research/, adding citrus_project/research/paper_shortlist.md, and moving ignored Lite-Mono demo outputs to citrus_project/research/generated/.
- 2026-04-17: Ran a final 12-sample time-spread visual spot-check and locked `exact_lidar_parent_child_inverted` as the default/final dense-label transform route; `production_current` remains available as an alternate comparison route.
- 2026-04-17: Smoke-tested build_training_dataset.py with one sample to confirm the final/default transform is used by the builder; removed the throwaway smoke-check output afterward.
- 2026-04-17: Removed the completed presentation-only reports/ folder and GEMINI.md from the tracked workspace as part of research-focused cleanup.
- 2026-04-21: Added explicit document-role rules so AGENTS.md remains the project source of truth while `citrus_project/research/student_qna.md` stores recurring beginner-facing explanations; also added a clearer timeline snapshot for done/current/next work.
- 2026-04-21: Renamed research-note files to simpler names and added an explicit research-note workflow plus workspace map so future chats can place notes consistently.
- 2026-04-21: Simplified the research-note structure again by merging the small dataset-audit and baseline evidence files into `citrus_project/research/dataset_notes.md` and `citrus_project/research/baseline_notes.md`, keeping only the paper shortlist, student Q&A, and ignored generated outputs alongside them.
- 2026-04-21: Removed the legacy 50-sample prepared-dataset probe output folders from `citrus_project/dataset_workspace/` after their results were already captured in notes, to reduce workspace clutter.
- 2026-04-22: Added an explicit user-collaboration preference to verify codebase details before answering, check edge cases instead of assuming file/workflow importance, and label guesses clearly when discussing ideas versus confirmed repository behavior.
- 2026-04-22: Moved the project-owned Citrus dataset workspace and research notes under `citrus_project/`, separating them more clearly from the original Lite-Mono code at repo root.
- 2026-04-22: Added `citrus_project/milestones/` with per-milestone folders plus workspace README files so future milestone-specific work can live in one consistent place.
- 2026-04-22: Updated the Citrus download/extract/verify helper scripts so relative paths resolve from `citrus_project/dataset_workspace/`, making the moved workspace less dependent on the caller's current working directory.
- 2026-04-22: Added team-collaboration docs (`TEAM_WORKFLOW.md`, `TASK_BOARD.md`, `literature_tracker.md`, `scene_taxonomy.md`, and the Milestone 0 `sample_pack/` scaffold) so teammates and their AI assistants can stay aligned without needing the full dataset workspace.
- 2026-04-23: Ignored the project-scoped `.codex/` folder and documented that it may contain local MCP configuration plus API secrets, so it should remain untracked.
- 2026-04-23: Reframed the project goal more carefully as lightweight monocular depth for vegetation-dense agricultural environments, using Citrus Farm as the current benchmark/validation dataset rather than the only intended deployment domain.
- 2026-04-23: Ran the full `build_training_dataset.py` build with `exact_lidar_parent_child_inverted` and `local_idw`, producing `prepared_training_dataset/` with 5282 samples, 5282 valid masks, and time-block splits of train=4311, val=564, test=407.
- 2026-04-23: Added `citrus_project/research/advisor_notes.md` to track professor/advisor questions and recommendations, including the current later-stage motion-sensitivity side-question and the suggestion to check whether speed-detection literature has any useful connection.
- 2026-04-23: Synced the milestone workspace READMEs so the folder structure itself now reflects that Milestone 0 is complete through the full dataset build and Milestone 1 is the active next stage.
- 2026-04-27: Added the user's preferred explanation style for AI/PyTorch/image-processing concepts: concrete mental hooks, exact value meanings, numeric examples, and proactive beginner-facing clarification of adjacent terms.
- 2026-04-27: Added the user's preferred mutual-understanding workflow for deep AI/model-algorithm work: ask frequent concept checks, map formulas to tensor operations in the repository, and slow down until both the mathematical and code-level meanings are shared.
- 2026-04-27: Added the Milestone 1 Citrus evaluator entry point `evaluate_lite_mono_citrus.py` with Slice 1 data inspection for prepared split, manifest, RGB, dense LiDAR label, and valid mask loading; model inference and metrics remain next slices.
- 2026-04-27: Extended the Milestone 1 Citrus evaluator with Slice 2 optional limited-sample original Lite-Mono inference, printing tensor, raw closeness level, scaled disparity, predicted depth, and resized depth summaries while leaving metric computation for the next slice.
- 2026-04-28: Extended the Milestone 1 Citrus evaluator with Slice 3 one-sample valid-mask-aware depth metrics against dense LiDAR labels, reporting both raw-scale and median-scaled metric rows while leaving full split aggregation/output saving for the next slice.
- 2026-04-28: Clarified that milestone README files should serve as teammate-facing handoffs, and expanded the Milestone 0 README with a beginner-friendly workflow narrative, key decisions, artifact meanings, and hand-off guidance for Milestone 1.
- 2026-04-28: Extended the Milestone 1 Citrus evaluator with Slice 4 aggregate metric summaries over selected or full splits, using per-image metric means, `--summary_only`, progress logging, and `--max_samples 0` for full-split evaluation; result-file saving remains pending.
- 2026-04-28: Extended the Milestone 1 Citrus evaluator with Slice 5 optional saved outputs via `--output_dir`, writing aggregate summary JSON and per-sample CSV files; added a Milestone 1 results folder README and ignored `maxN` smoke outputs so full-split results can be reviewed separately.
- 2026-04-28: Extended the Milestone 1 Citrus evaluator with Slice 6 runtime/FPS metadata in printed summaries and saved JSON/CSV outputs, distinguishing evaluator-loop timing from synchronized model-forward timing; parameter reporting and final full-split runs remain pending.
- 2026-04-28: Extended the Milestone 1 Citrus evaluator with Slice 7 model parameter/checkpoint metadata for the original Lite-Mono depth-inference path, reporting 3.075M encoder+depth-decoder parameters and saving model-info fields to summary JSON outputs.
- 2026-04-28: Ran the full original Lite-Mono baseline on Citrus validation and test splits with GPU, saved full CSV/JSON result files, and recorded the first real baseline metrics: validation median-scaled abs_rel=0.4176/a1=0.4629 and test median-scaled abs_rel=0.3836/a1=0.4989.
- 2026-04-28: Added the Slice 8 result-analysis helper for selecting good/typical/bad baseline samples by `median_scaled_a1` and generated first validation visual panels under the Milestone 1 `visuals/` folder.
- 2026-04-29: Added Slice 9 visual interpretation notes, explaining the selected good/typical/bad panels in beginner-friendly language and recording the first qualitative baseline-failure interpretation for Milestone 1.
- 2026-04-29: Ran Slice 10 test-split visual selection, adding matching good/typical/bad test panels and summaries under the Milestone 1 `visuals/` folder.
- 2026-04-29: Started Milestone 2 with a milestone-local `CitrusPreparedDataset` plus a DataLoader smoke inspector; verified two train and two validation samples load with model-sized RGB tensors, native dense labels/masks, manifest metadata, and Citrus ZED-left camera intrinsics while leaving root Lite-Mono training code unchanged.
- 2026-05-05: Added the Milestone 2 temporal-neighbor diagnostic script and verified that same-split/same-session previous-current-next triplets are available for 4275/4311 train samples, 560/564 validation samples, and 399/407 test samples under a 200 ms neighbor-gap threshold; root Lite-Mono trainer code remains unchanged.
- 2026-05-05: Extended `CitrusPreparedDataset` with optional same-split temporal triplet loading, Lite-Mono-style color/K tuple keys, metadata-free trainer-facing samples, and a temporal DataLoader smoke path; verified train/validation temporal batches load frame `0`, `-1`, and `1` RGB tensors without touching root training code.
- 2026-05-05: Added the Milestone 2 trainer-compatibility dry run for metadata-free Citrus temporal batches; verified CPU batch-size-1 and batch-size-2 runs through Lite-Mono depth, pose, projection, and reprojection-shape logic while keeping root `trainer.py` unchanged.
- 2026-05-05: Added a Citrus-safe training-time depth-metric guard in `trainer.py` and `options.py`; default KITTI Eigen crop behavior is preserved, Citrus/non-KITTI labels must use `--depth_metric_crop none`, and valid masks are honored when present.
- 2026-05-05: Wired Citrus into root trainer option/dataset selection with `--dataset citrus`, auto-resolved Citrus split/data path/depth-metric behavior, and a root trainer wiring smoke that loads 4275 train and 560 validation temporal Citrus samples and runs one finite batch through the normal trainer path.
- 2026-05-05: Added and ran the root Citrus one-step optimizer smoke; one CPU batch completed forward, backward, finite-gradient checks, and an AdamW parameter update without starting a real fine-tuning experiment.
- 2026-05-05: Added train-only Citrus color augmentation for `color_aug`, verified validation remains unaugmented, reran root trainer wiring plus one-step optimizer smokes, and marked Milestone 2 core integration complete.
- 2026-05-05: After the laptop GPU became visible, reran the root Citrus one-step optimizer smoke with `--use_cuda`; it passed on the NVIDIA GeForce RTX 4060 Laptop GPU.
- 2026-05-05 to 2026-05-06: Milestone 3 moved through controlled CUDA smokes and pilot-scale self-supervised Citrus adaptation checks, with all run logs/checkpoints kept under the ignored Milestone 3 `runs/` folder.
- 2026-05-05 to 2026-05-06: Added Milestone 3 safety/diagnostic controls: `--max_train_steps`, Python 3 validation iterator compatibility, modern torchvision ResNet pretrain loading, `--freeze_depth_steps`, `--freeze_depth_encoder`, and the fixed-batch diagnostic helper.
- 2026-05-06: Milestone 3 pilot verdict is not to scale current recipes yet; photo loss can improve while LiDAR-valid depth metrics worsen, and lower LR, frozen encoder/BatchNorm, decoder-only updates, and previous-only temporal source did not beat the untouched baseline.
- 2026-05-06: Added the living-notes rule and compacted the duplicated Milestone 3 run-by-run AGENTS.md history into a source-of-truth status summary that points to the detailed milestone/research notes.
- 2026-05-06: Extended the Milestone 3 diagnostic helper with loss-decomposition, deterministic seed, frame-id, and weights-init controls; fixed validation diagnostics suggest smoothness is not the main driver and depth-scale freedom remains the key failure signal.
- 2026-05-06: Ran 50-step pose-only/depth-frozen controls; fully freezing the depth path preserved the original first-100 validation metrics exactly, while BatchNorm-only drift moved metrics slightly, confirming the larger failures start when trainable depth parameters update.
- 2026-05-06: Added default-off `--seed` for reproducible short-run comparisons and ran a seeded warmup-then-depth trajectory; median-scaled relative-depth quality worsened after 5 depth-update steps and degraded further by 15/25 depth-update steps.
- 2026-05-06: Added `citrus_project/milestones/03_self_supervised_adaptation/beginner_progress_summary.md` as a plain-language Milestone 3 explanation for student/professor discussion.
- 2026-05-06: Added default-off `--save_step_frequency` step checkpointing and prepared PowerShell runner/evaluation scripts for a user-launched conservative 1000-step Milestone 3 terminal probe; no training was launched by chat.
- 2026-05-07: Checked the user-launched conservative 1000-step Milestone 3 probe; training stopped cleanly at the planned step limit, step checkpoints were saved, first-100 validation evaluations were saved, the run failed to beat the untouched baseline at step 250/500/750/final, and the negative adapted-baseline evidence was added to the paper shortlist.
- 2026-05-07: Added and ran the Milestone 3 original-versus-adapted visual comparison helper; saved side-by-side panels for selected validation examples and recorded that the adapted checkpoint looks smoother and less structurally specific than the original baseline.
- 2026-05-07: Ran the approved 250-step no-color-augmentation Milestone 3 control; it improved over the color-augmented 250-step conservative run but still did not beat the untouched baseline on first-100 median-scaled relative-depth metrics. Added a student Q&A note explaining why from-scratch training should be treated as a later larger-data branch rather than the immediate Milestone 3 fix.
- 2026-05-07: Ran the approved 500-step no-color-augmentation Milestone 3 gate; it finished cleanly but worsened versus the 250-step no-augmentation checkpoint and still trailed the untouched baseline, supporting a stop to blind Milestone 3 recipe scaling.
- 2026-05-07: Closed Milestone 3 standard self-supervised adaptation as documented weak/negative baseline evidence and updated handoff notes so the next chat should start Milestone 4 planning rather than restart Milestone 3 recipe scaling.
- 2026-05-22: Added a Milestone 4 next-experiment reminder that checkpoint scanning/sweeping must happen before preparing or launching the next LiDAR-aware edge-loss training run.
- 2026-05-22: Completed the Milestone 4 hybrid checkpoint scan; `weights_13` beat final `weights_29` on validation and won the top-3 test confirmation, so it is now the selected hybrid checkpoint pending visual comparison.
- 2026-05-22: Generated `weights_13` visual comparisons against Plain Citrus and final `weights_29`; typical/good panels support the metric result, while some bad selected samples still favor `weights_29`.
- 2026-05-25: Prepared a progress-presentation package for the user's 2026-05-26 presentation, including slide bullets, speaker script, metric graphs, checkpoint-sweep graphs, and selected visual comparison panels for hybrid `weights_13` and the future LiDAR-aware edge-loss plan.
- 2026-05-25: Updated the progress-presentation script with a slide explaining the switch from pure self-supervised training to hybrid supervised training, including the photometric-loss failure mode and the role of masked LiDAR supervision during training only.
- 2026-05-25: Mirrored the progress-presentation package from `C:/Proj/lite-Mono` into the active long-path workspace so the user can see the updated PPT script and assets from the current VS Code folder.
- 2026-05-25: Condensed the progress-presentation back half by merging the checkpoint scan, top-3 confirmation, visual comparison, middle-epoch explanation, and roadmap content into a smaller group-presentation-friendly slide set.
- 2026-05-25: Updated the progress-presentation script to explain the actual hybrid data arrangement and to clarify that Plain Citrus test raw a1=`0.0077` is expected from raw-scale failure, not a graph mistake.
- 2026-05-25: Added the median-scaled-only Plain Citrus versus Hybrid `weights_13` graph and script wording, clarifying that Hybrid improves relative depth after scale correction as well as raw absolute-scale metrics.
- 2026-05-25: Added and ran `compare_plain_medianscaled_vs_weights13.py`, generating validation/test bad/typical/good PNG panels for Plain Citrus median-scaled versus Hybrid `weights_13` raw comparisons, and updated the presentation assets/script to use those panels.
- 2026-05-25: Copied all six epoch-29-versus-epoch-13 comparison PNGs into the presentation assets folder and updated the presentation asset list so bad/typical/good panels for both validation and test are easy to find.
- 2026-05-25: Regenerated `graph_metric_summary_table.png` for the progress presentation so it removes Val Raw/Test Raw rows and focuses on median-scaled validation/test metrics only.
- 2026-05-25: Added `PRESENTATION_6_MIN_SCRIPT.md` to the progress-presentation package as a concise 6-minute version of the full slide script.
- 2026-05-26: Generated `PRESENTATION_6_MIN_SCRIPT_GOOGLE_DOCS.docx` from the concise Markdown script so it can be opened or uploaded directly into Google Docs.
- 2026-06-02: Added `LAB_COMPUTER_SETUP.md` for the lab-computer transfer workflow and began preparing a clean GitHub-transfer repo that includes project code/docs/READMEs/AGENTS while excluding local datasets, weights, caches, and bulky run outputs.
- 2026-06-02: Tightened `.gitignore` for lab-machine use by ignoring checkpoint files, milestone runs/results/snapshots/log folders, and log files to prevent large generated artifacts from appearing in source control.
- 2026-06-03: Recorded lab-computer prepared dataset build completion: `build_training_dataset.py --workers 8` produced 4918 total samples with `exact_lidar_parent_child_inverted` after resuming from 1341 reused dense files; verify splits/metrics before starting training.
- 2026-06-03: Recorded lab prepared split counts (train=3947, val=564, test=407) and the planned first training gate: hybrid supervised half epoch, batch size 12, about 164 optimizer steps.
- 2026-06-03: Patched the clean transfer repo to add the missing full `Marvel/hybrid_supervised_draft` training code; lab users should pull this fix before launching the half-epoch hybrid run and still provide the Lite-Mono pretrain weight separately.

## Update Template (For Future Changes)

Date:
Changed files:
What changed:
Why:
Validation run:
Open risks:
Next step:

Note-maintenance action:
