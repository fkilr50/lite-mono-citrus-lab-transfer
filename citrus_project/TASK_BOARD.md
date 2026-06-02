# Task Board

Date: 2026-05-07

## Current Project Position

- Milestone 0 is complete through the full dataset build.
- The original Lite-Mono baseline evaluation has now produced full validation/test result files on Citrus.
- The Citrus evaluator entry point now supports Slice 1 data inspection, Slice 2 model inference, Slice 3 valid-mask-aware metrics, Slice 4 aggregate metric summaries, Slice 5 optional result-file saving, Slice 6 runtime/FPS metadata, and Slice 7 model parameter/checkpoint metadata.
- Slice 8 result-interpretation support now selects good/typical/bad validation samples and renders visual panels.
- The first written visual interpretation note now explains the good/typical/bad panels and the main baseline failure pattern.
- Test good/typical/bad visual panels are now generated too.
- Optional Milestone 1 polish is deferred for now: broader failure taxonomy and FLOPs/deployment benchmarking can wait unless the paper needs them sooner.
- Milestone 2 has started with a milestone-local Citrus prepared Dataset/DataLoader smoke slice.
- Milestone 2 temporal-neighbor diagnostics now show same-split/same-session safe triplets for 99.16% of train samples under a 200 ms neighbor-gap cap.
- Milestone 2 temporal DataLoader mode now returns same-split `[-1, 0, 1]` RGB triplets with Lite-Mono-style tuple keys.
- Milestone 2 trainer-compatibility dry runs pass metadata-free temporal Citrus batches through Lite-Mono depth, pose, projection, and reprojection-shape logic.
- Milestone 2 now has a root trainer depth-metric guard: KITTI keeps the default Eigen crop, while Citrus/non-KITTI labels must use `--depth_metric_crop none` and can use `valid_mask`.
- Milestone 2 root trainer wiring now exposes `--dataset citrus`; the root smoke resolves Citrus to `split=citrus_prepared`, `depth_metric_crop=none`, and loads 4275 train / 560 validation temporal samples.
- Milestone 2 one-step Citrus training smoke passed: one CPU batch completed forward, backward, finite-gradient checks, and an AdamW parameter update.
- Milestone 2 Citrus color augmentation now applies train-only `color_aug` jitter while validation stays unaugmented.
- Milestone 2 CUDA one-step Citrus smoke passed on the NVIDIA GeForce RTX 4060 Laptop GPU.
- Milestone 2 core integration is complete.
- Milestone 3 standard self-supervised Citrus adaptation is documented as weak/negative baseline evidence: the training path works, but tested recipes do not beat the untouched baseline and can damage relative-depth structure.
- Disabling Citrus color augmentation reduced the damage at 250 steps, but the 500-step no-augmentation continuation degraded again, so the current recipe family should not be scaled into a long run.
- Milestone 4 has selected its first implementation direction: start with Phase 2 boundary-aware loss before Phase 1 occlusion masking.
- The user's near-term group deliverable is to implement and retrain Lite-Mono with the Phase 2 boundary-loss plan; broader comparisons with later retrained/new-dataset models are future work.
- A small curated sample pack is still needed for Friend B's deeper work.

## Ownership

### Main Integrator (User)

Current focus:

1. maintain the core Citrus pipeline and repo-wide integration
2. begin Milestone 4 Phase 2 boundary-aware loss planning from the documented Milestone 3 failure pattern
3. implement and retrain the Phase 2 boundary-loss model before spending effort on broader future comparison studies

Near-term outputs:

- Milestone 4 Phase 2 boundary-aware loss implementation plan and smoke-test path
- final Milestone 3 closeout wording for the paper/results story
- optional broader failure taxonomy or FLOPs notes later if needed

### Friend A

Current focus:

1. literature scouting for lightweight monocular depth improvements
2. rank ideas for vegetation-dense scenes
3. identify ideas that are realistic for Milestone 4

Working file:

- `citrus_project/research/literature_tracker.md`

Expected near-term output:

- 5 to 10 candidate ideas with lightweight/risk judgment

### Friend B

Current focus:

1. define scene categories from a small shared sample pack
2. pick representative and difficult example frames
3. prepare qualitative-support notes for later results/paper writing

Working files:

- `citrus_project/research/scene_taxonomy.md`
- `citrus_project/milestones/00_dataset_audit/sample_pack/`

Expected near-term output:

- first-pass scene taxonomy
- example-frame shortlist
- notes on why certain scenes are hard for depth estimation

## Blocked / Waiting

1. Friend B’s deeper work depends on a small curated sample pack being prepared.
2. Baseline evaluation no longer needs final validation/test runs, validation/test visual selection, or first written interpretation; remaining Milestone 1 extras are optional depth, FLOPs, or broader taxonomy.
3. Full self-supervised Citrus training should not proceed under the current Milestone 3 recipe family without a new technical reason.

## Next Review Point

After:

1. the sample pack scaffold is ready for sharing
2. the Milestone 4 Phase 2 boundary-aware loss implementation and evaluation plan are reviewed
3. Friend A has an initial idea shortlist
