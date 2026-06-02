# Milestones Workspace

These folders are reserved for milestone-specific work as the project progresses.

Use them to keep new code, experiment helpers, notes, plots, and milestone-scoped artifacts grouped by stage instead of scattering them across the whole repo.

## Folder Map

- `00_dataset_audit/` - dataset construction, calibration checks, label-route validation (complete through full dataset build)
- `01_original_lite_mono_baseline/` - original Lite-Mono baseline runs and evaluation helpers (core baseline evidence complete; optional polish deferred)
- `02_citrus_integration/` - Citrus Dataset/DataLoader and evaluation integration
- `03_self_supervised_adaptation/` - self-supervised Citrus fine-tuning/adaptation work (documented as weak/negative baseline evidence)
- `04_lightweight_vegetation_improvement/` - lightweight vegetation-focused model/loss improvements (next active planning stage)
- `05_optional_supervised_or_hybrid/` - optional supervised or hybrid training additions
- `06_paper_package/` - paper tables, figures, writing support, and final packaging

Current milestone state:

- Milestone 0 is complete through the full dataset build.
- Milestone 1 has full original Lite-Mono validation/test metrics, validation/test good-typical-bad visuals, and first written interpretation.
- Optional Milestone 1 polish is deferred for now.
- Milestone 2 core integration is complete: Citrus prepared Dataset/DataLoader, temporal-neighbor diagnostics, temporal triplet batch smoke checks, trainer-compatibility dry run, root depth-metric guard, root `--dataset citrus` trainer wiring, one-step optimizer smoke, CUDA one-step smoke, and train-only Citrus color augmentation are in place.
- Milestone 3 standard self-supervised Citrus adaptation is documented as a weak/negative adapted-baseline result. The tested recipe family runs technically but fails to beat the untouched baseline and can damage relative depth structure.
- Milestone 4 is the next planning stage: choose one lightweight vegetation-focused improvement and compare it against both original Lite-Mono and the documented Milestone 3 adapted-baseline failure.

These folders are the intended home for milestone-specific code, notes, helpers, and outputs as each stage becomes active.
