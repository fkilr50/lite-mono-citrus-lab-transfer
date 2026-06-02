# Phase 2 Quick-Start Checklist

## Pre-Implementation

- [ ] Read `BOUNDARY_AWARENESS_EXPLAINED.md` (understand the concept)
- [ ] Read `PHASE_2_BOUNDARY_LOSS.md` (Parts A-B, detailed roadmap)
- [ ] Verify M4a (Phase 1) training is complete
- [ ] Have M4a checkpoint ready: `logs_phase1/citrus_occlusion_aware/models/weights_20`
- [ ] Understand: Boundary loss = gradient alignment between depth and RGB edges

---

## Implementation (80 lines of code)

### Step 1: Add BoundaryLoss to `layers.py`

- [ ] Copy `BoundaryLoss` class from PHASE_2_BOUNDARY_LOSS.md
- [ ] Verify class compiles without errors
- [ ] Test with dummy tensors: `loss = BoundaryLoss()(dummy_depth, dummy_img)`

### Step 2: Add to `trainer.py` Init

- [ ] Import `BoundaryLoss` from layers
- [ ] Create instance in `__init__`: `self.boundary_loss = BoundaryLoss(...)`
- [ ] Set weight: `self.boundary_loss_weight = 0.2`
- [ ] Verify trainer still initializes without errors

### Step 3: Integrate into Loss Computation

- [ ] Find `compute_losses` method in trainer.py
- [ ] After smoothness loss, add boundary loss computation
- [ ] Combine: `loss += self.boundary_loss_weight * boundary_loss`
- [ ] Add logging: `losses["boundary_loss/{}".format(scale)] = boundary_loss`

### Step 4: Add Optional Hyperparameters (Optional)

- [ ] Add `--boundary_loss_weight` flag to options.py
- [ ] Add `--boundary_normalize` flag to options.py
- [ ] Test that flags parse correctly

### Step 5: Add Debug Visualization (Optional)

- [ ] Add `test_boundary_loss()` method to trainer
- [ ] Call in `__init__` to catch issues early
- [ ] Verify output is scalar (not NaN/Inf)

---

## Testing (Before Full Training)

### Quick Sanity Check

```powershell
# Run minimal training (5 steps)
python train.py \
  --model lite-mono \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --log_dir logs_debug_phase2 \
  --num_epochs 1 \
  --num_steps 5 \
  --batch_size 1 \
  --boundary_loss_weight 0.2
```

- [ ] No crashes (shape mismatches, missing imports)
- [ ] Loss values printed to console
- [ ] Boundary loss component visible (e.g., "boundary_loss/0: 0.0234")
- [ ] Loss decreases over 5 steps
- [ ] No NaN/Inf values

### Validation After Fixes

- [ ] Trainer runs for 1 full epoch without crashes
- [ ] All loss components decreasing
- [ ] Checkpoint saved

---

## Full Training (Phase 2)

```powershell
python train.py \
  --model lite-mono \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --log_dir logs_phase2 \
  --model_name citrus_boundary_aware \
  --num_epochs 20 \
  --batch_size 4 \
  --num_workers 4 \
  --height 320 \
  --width 1024 \
  --boundary_loss_weight 0.2
```

- [ ] Training completes 20 epochs without crashes
- [ ] Total loss decreases smoothly (no wild oscillations)
- [ ] Boundary loss component non-zero and decreasing
- [ ] Checkpoint saved: `logs_phase2/citrus_boundary_aware/models/weights_20`
- [ ] Training time reasonable (<8 hours on GPU)

---

## Evaluation (M4b Results)

### Prepare Evaluation Script

- [ ] Use existing evaluate_citrus.py or adapt evaluate_depth.py
- [ ] Ensure it loads LiDAR-densified labels + valid masks
- [ ] Compute: MAE, RMSE, edge sharpness metrics

### Run Evaluation

```powershell
python evaluate_citrus.py \
  --weights_folder logs_phase2/citrus_boundary_aware/models/weights_20 \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --split val
```

- [ ] Evaluation completes without errors
- [ ] M4b MAE < M4a MAE (expected 8-12% improvement)
- [ ] Edge sharpness metric available
- [ ] Runtime reported (should be ~37-38ms, similar to M4a)

---

## Results Documentation

### Record M4b Metrics

| Metric | M4a (Occlusion) | M4b (Occlusion + Boundary) | Improvement |
|---|---|---|---|
| Depth MAE (m) | _____ | _____ | _____ |
| Depth RMSE (m) | _____ | _____ | _____ |
| Edge Sharpness Score | _____ | _____ | _____ |
| Runtime (ms/frame) | _____ | _____ | _____ |

- [ ] Fill in table above
- [ ] Update `citrus_project/research/baseline_notes.md` with M4b entry
- [ ] Save sample predictions (RGB, M4a depth, M4b depth, GT)

### Generate Visualizations

- [ ] Side-by-side M4a vs M4b depth predictions
- [ ] Focus on vegetation boundaries (leaves, branches, fruit)
- [ ] Save 5-10 example comparisons
- [ ] Annotate: where did boundary loss help most?

---

## Debugging Guide (If Things Go Wrong)

### Problem: Boundary Loss is NaN

**Check:**
1. Are input tensors valid (no NaN/Inf)?
2. Is depth in reasonable range (1-20m)?
3. Is image normalized (0-1 or -1 to 1)?

**Fix:**
- [ ] Print shapes: `print(depth.shape, img.shape)`
- [ ] Print ranges: `print(depth.min(), depth.max())`
- [ ] Check normalization: `assert img.min() >= -1.5 and img.max() <= 1.5`

### Problem: M4b Worse Than M4a

**Try these in order:**

1. **Reduce boundary weight:**
   ```powershell
   --boundary_loss_weight 0.1  # was 0.2
   ```
   - [ ] Retrain and check results

2. **Increase training time:**
   ```powershell
   --num_epochs 30  # was 20
   ```
   - [ ] Phase 2 may need longer to converge

3. **Try without normalization:**
   ```python
   # In layers.py, change:
   self.boundary_loss = BoundaryLoss(normalize=False)
   ```
   - [ ] Retrain

4. **Fall back to Phase 1 if needed:**
   ```powershell
   --boundary_loss_weight 0.0  # Disables boundary loss
   ```
   - [ ] Use M4a as final model

### Problem: Boundary Loss Component Too Large

**Symptoms:** Boundary loss >> photometric loss (e.g., 0.5 vs 0.1)

**Fix:**
- [ ] Reduce weight: `--boundary_loss_weight 0.1`
- [ ] Or disable normalization and see if that helps
- [ ] Print gradient ranges: `print(grad_depth.min(), grad_depth.max())`

### Problem: Training Crashes with Shape Error

**Common causes:**
- Padding not matching original size
- RGB has different channel than expected

**Fix:**
- [ ] Check BoundaryLoss.__call__ padding logic
- [ ] Verify RGB is [B, 3, H, W] and gets converted to [B, 1, H, W]
- [ ] Print shapes at each step

### Problem: Edge Predictions Still Blurry

**Symptoms:** Edge sharpness score not improved from M4a

**Possible causes:**
1. Boundary loss weight too low
2. RGB edges don't align with depth edges
3. Training not converged

**Try:**
- [ ] Increase weight: `--boundary_loss_weight 0.3` or `0.4`
- [ ] Increase epochs: `--num_epochs 30`
- [ ] Visualize: are RGB edges where depth should be sharp?

---

## Before Moving to Phase 3 (Optional)

✅ Checklist:

- [ ] M4b training complete (20+ epochs)
- [ ] M4b evaluation shows improvement over M4a (expected 8-12%)
- [ ] Results documented in `baseline_notes.md`
- [ ] Sample visualizations saved and labeled
- [ ] Boundary loss behavior understood (not oscillating, stable)
- [ ] Code clean and commented
- [ ] Ready to write paper or do Phase 3

---

## File Summary

| File | Purpose | Status |
|---|---|---|
| `BOUNDARY_AWARENESS_EXPLAINED.md` | Conceptual guide | ✅ Ready |
| `PHASE_2_BOUNDARY_LOSS.md` | Roadmap + code | ✅ Ready |
| `layers.py` | Add BoundaryLoss class | ⏳ Implement |
| `trainer.py` | Integrate + log | ⏳ Implement |
| `options.py` | Add CLI flags | ⏳ Optional |
| `logs_phase2/` | Training output | ⏳ Generate |

---

## Time Estimate

- Reading + understanding: 2-3 hours
- Implementation: 2-3 hours (simpler than Phase 1)
- Smoke test: 0.5 hour
- Full training: 4-6 hours
- Evaluation: 1-2 hours
- **Total: 10-16 hours**

---

## Success Criteria

Phase 2 is **COMPLETE** when:

1. ✅ BoundaryLoss integrated and runs without errors
2. ✅ Training shows smooth loss decrease (no NaN/Inf)
3. ✅ M4b validation error < M4a (expected 8-12% improvement)
4. ✅ Visualizations show crisper depth edges
5. ✅ Results documented
6. ✅ Decision made: proceed to Phase 3 or write paper?

---

## What's Next?

### Option A: Phase 3 (Optional)
Train RTS-Mono on Citrus and compare vs M4b

### Option B: Paper Writing
Create final results tables and write up findings

### Option C: Done!
M4b is your final improved model; move to publication

Good luck! 🚀
