# Phase 1 Quick-Start Checklist

## Pre-Implementation

- [ ] Read `OCCLUSION_MASKING_EXPLAINED.md` (understand the concept)
- [ ] Read `PHASE_1_OCCLUSION_MASKING.md` (detailed roadmap)
- [ ] Verify `prepared_training_dataset/` exists (or run `build_training_dataset.py`)
- [ ] Verify original Lite-Mono baseline (M1) is complete
- [ ] Verify M3 (self-supervised Citrus adapt) results are recorded

---

## Implementation (75 lines of code)

### Step 1: Add Occlusion Detector to `layers.py`

- [ ] Copy `OcclusionDetector` class from PHASE_1_OCCLUSION_MASKING.md
- [ ] Verify class compiles without errors
- [ ] Test with dummy depth tensor: `detector = OcclusionDetector(); mask = detector(dummy_depth)`

### Step 2: Add to `trainer.py` Init

- [ ] Import `OcclusionDetector` from layers
- [ ] Create instance in `__init__`: `self.occlusion_detector = OcclusionDetector(...)`
- [ ] Verify trainer still initializes without errors

### Step 3: Modify Loss Function in `trainer.py`

- [ ] Add `depth=None, occlusion_aware=False` parameters to `compute_reprojection_loss`
- [ ] Add occlusion masking logic inside function
- [ ] Test with dummy tensors

### Step 4: Update Call Sites in `trainer.py`

- [ ] Find all calls to `compute_reprojection_loss` in `compute_losses`
- [ ] Add `depth=outputs[("depth", 0, scale)], occlusion_aware=True`
- [ ] Verify trainer runs without errors (training loop)

### Step 5: Add Debug Visualization (Optional)

- [ ] Add `visualize_occlusion_mask` method to trainer
- [ ] Call during training to inspect masks
- [ ] Save sample images for documentation

---

## Testing (Before Full Training)

### Quick Smoke Test

```powershell
# Run minimal training (5 steps on 1 batch)
python train.py \
  --model lite-mono \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --log_dir logs_debug \
  --num_epochs 1 \
  --num_steps 5 \
  --batch_size 1
```

- [ ] No crashes (shape mismatches, missing imports, etc.)
- [ ] Loss decreases on first epoch
- [ ] Occlusion mask visualizations save correctly

### Validation After Fix-Ups

- [ ] Trainer runs for 1 full epoch on subset
- [ ] Loss values are reasonable (not NaN/Inf)
- [ ] Occlusion masks look reasonable visually

---

## Full Training (Phase 1)

```powershell
python train.py \
  --model lite-mono \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --log_dir logs_phase1 \
  --model_name citrus_occlusion_aware \
  --num_epochs 20 \
  --batch_size 4 \
  --num_workers 4 \
  --height 320 \
  --width 1024
```

- [ ] Training completes without crashes
- [ ] Loss decreases over 20 epochs
- [ ] Saved checkpoints in `logs_phase1/citrus_occlusion_aware/models/`

---

## Evaluation (M4a Results)

### Prepare Evaluation Script

- [ ] Copy `evaluate_citrus.py` or adapt `evaluate_depth.py`
- [ ] Ensure it handles:
  - Citrus image dimensions (not KITTI crop assumptions)
  - LiDAR-densified labels with valid masks
  - Custom metrics (MAE, RMSE, etc.)

### Run Evaluation

```powershell
python evaluate_citrus.py \
  --weights_folder logs_phase1/citrus_occlusion_aware/models/weights_20 \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --split val
```

- [ ] Evaluation completes without errors
- [ ] Metrics printed (MAE, RMSE, etc.)
- [ ] Results better than M3 baseline (expect 10-15% improvement)

---

## Results Documentation

### Record M4a Metrics

| Metric | M3 (Baseline) | M4a (Occlusion Masking) | Improvement |
|---|---|---|---|
| Depth MAE (m) | _____ | _____ | _____ |
| Depth RMSE (m) | _____ | _____ | _____ |
| Runtime (ms/frame) | _____ | _____ | _____ |

- [ ] Fill in table above
- [ ] Update `citrus_project/research/baseline_notes.md` with M4a entry
- [ ] Save sample predictions (RGB, predicted depth, GT, mask)

### Visualizations

- [ ] Occlusion mask samples (showing what was marked as uncertain)
- [ ] Depth prediction comparisons (M3 vs M4a on same frame)
- [ ] Qualitative failure cases (where occlusion masking helps most)

---

## Debugging Guide (If Things Go Wrong)

### Problem: Loss doesn't decrease
- [ ] Check if occlusion mask is all 0s or all 1s (gradient threshold issue)
- [ ] Reduce `grad_threshold` from 0.5 to 0.3
- [ ] Increase `dilation_radius` from 2 to 3

### Problem: Shape mismatch errors
- [ ] Verify padding in `OcclusionDetector.__call__`
- [ ] Check that mask output shape matches depth input shape
- [ ] Print shapes for debugging: `print(depth.shape, mask.shape)`

### Problem: M4a results worse than M3
- [ ] Option 1: Increase `grad_threshold` (mask fewer pixels)
- [ ] Option 2: Decrease `dilation_radius` (narrower boundaries)
- [ ] Option 3: Switch to `method="error_based"` instead of gradient
- [ ] Option 4: Reduce weight: `loss = loss * (0.5 * mask + 0.5)` (gradually reduce masking)

### Problem: Training slower than expected
- [ ] Check if `num_workers` is set correctly
- [ ] Verify GPU is being used: `torch.cuda.is_available()` should be True
- [ ] Profile: add timing to see where slowdown is

---

## Before Moving to Phase 2

✅ Checklist:

- [ ] M4a training complete (20 epochs)
- [ ] M4a evaluation shows improvement over M3
- [ ] Results documented in `baseline_notes.md`
- [ ] Sample visualizations saved
- [ ] Code clean and commented
- [ ] Occlusion masking parameters locked (won't change in Phase 2)

**Only then:** Proceed to Phase 2 (Boundary-Aware Loss)

---

## File Summary

| File | Purpose | Status |
|---|---|---|
| `PHASE_1_OCCLUSION_MASKING.md` | Detailed roadmap + code | ✅ Ready to read |
| `OCCLUSION_MASKING_EXPLAINED.md` | Conceptual guide (read first!) | ✅ Ready to read |
| `layers.py` | Add OcclusionDetector class | ⏳ Needs implementation |
| `trainer.py` | Integrate detector + mask loss | ⏳ Needs implementation |
| `options.py` | Add CLI flags (optional) | ⏳ Optional |
| `logs_phase1/` | Training outputs | ⏳ Will be created |

---

## Time Estimate

- Reading + understanding: 2-3 hours
- Implementation: 2-4 hours (includes debugging)
- Training: 4-6 hours (depends on GPU)
- Evaluation: 1 hour
- **Total: 9-14 hours**

---

## Success Criteria

Phase 1 is **COMPLETE** when:

1. ✅ Occlusion masking code integrated and runs without errors
2. ✅ Training shows improvement over M3 baseline
3. ✅ M4a metrics documented (expected 10-15% improvement)
4. ✅ Visualizations show cleaner depth in vegetation
5. ✅ Ready to move to Phase 2

Good luck! 🚀
