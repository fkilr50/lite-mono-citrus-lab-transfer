# Phase 1 Occlusion Masking: Complete Summary

**Date:** 2026-04-27  
**Status:** Ready for implementation  
**Complexity:** Medium (new loss masking mechanism)  
**Expected Duration:** 9-14 hours total

---

## TL;DR (One Paragraph)

Occlusion masking fixes a critical problem in vegetation depth: when the model learns from video sequences, some pixels in the target frame are hidden in the source frame (occluded by leaves/branches). Vanilla photometric loss penalizes ALL pixels equally, so the model hallucinates depth to explain hidden pixels. **Solution:** Detect depth discontinuities (where occlusions likely occur) and mask the loss there, so the model learns smooth, realistic geometry without hallucination. Implementation: 75 lines of code across `layers.py` and `trainer.py`. Expected improvement: 10-15% depth error reduction.

---

## Documentation Files Created

| File | What | Read Order |
|---|---|---|
| **OCCLUSION_MASKING_EXPLAINED.md** | Conceptual guide with visuals | 1️⃣ Start here |
| **PHASE_1_OCCLUSION_MASKING.md** | Detailed roadmap + implementation code | 2️⃣ Then here |
| **PHASE_1_CHECKLIST.md** | Step-by-step checklist for implementation | 3️⃣ During work |

---

## What is Occlusion Masking? (Visual Explanation)

### The Problem

```
Two camera angles of the same citrus tree:

Camera 1 (target):           Camera 2 (source):
┌──────────────────┐         ┌──────────────────┐
│ [apple]  [leaf]  │         │ [sky]    [sky]   │
│ [branch] [leaf]  │         │ [branch] [leaf]  │
│ [trunk]  [trunk] │         │ [trunk]  [trunk] │
└──────────────────┘         └──────────────────┘

The apple is VISIBLE in Camera 1 but HIDDEN in Camera 2 (occluded by branch).

Vanilla loss tries to explain this mismatch:
Error = |[apple] - [sky]| = HIGH
Model thinks: "Add fake depth at apple position to match sky"
Result: Hallucinated depth surface ❌
```

### The Solution

```
Detect where errors are unexplainable:
Occlusion Mask = [0, 1, 1, 1]  ← 0 at boundaries, 1 elsewhere

Masked Loss = Error * Mask
           = [0, (branch error), (trunk error), (trunk error)]

Model only penalizes pixels where depth CAN explain the difference.
Hidden pixels are ignored.
Result: Realistic, smooth depth ✓
```

---

## Implementation Overview

### Three Components

1. **OcclusionDetector** (layers.py)
   - Computes depth gradients to find boundaries
   - Creates mask: 1 = confident, 0 = uncertain
   - 40 lines of code

2. **Loss Integration** (trainer.py)
   - Apply mask to reprojection loss before averaging
   - Modify `compute_reprojection_loss` function
   - Update call sites in `compute_losses`
   - 30 lines of code

3. **Training** (existing train.py)
   - No changes needed to training loop
   - Just add `--occlusion_aware_loss` flag (optional)

### Code Structure

```
layers.py:
├─ OcclusionDetector.__init__()
│  └─ Store grad_threshold, dilation_radius
├─ OcclusionDetector.__call__(depth)
│  ├─ Compute gradients
│  ├─ Threshold to find boundaries
│  ├─ Dilate boundaries
│  └─ Return mask (1=confident, 0=uncertain)
└─ [existing code unchanged]

trainer.py:
├─ Trainer.__init__()
│  └─ self.occlusion_detector = OcclusionDetector(...)
├─ compute_reprojection_loss(pred, target, depth, occlusion_aware)
│  ├─ Compute photometric loss
│  └─ If occlusion_aware: loss *= occlusion_mask
└─ compute_losses() [update calls to compute_reprojection_loss]
```

---

## Expected Results

### Metrics Improvement (M4a vs M3)

| Metric | M3 (Baseline) | M4a (Occlusion) | Improvement |
|---|---|---|---|
| **Depth MAE** | 0.38m | 0.33m | -13% |
| **Depth RMSE** | 0.54m | 0.47m | -13% |
| **Edge Sharpness** | Medium | High | ✓ |
| **Runtime** | 35ms | 36ms | +0.3% |

### Qualitative Changes

**Before occlusion masking:**
- Smooth but fake depth in canopy (hallucinated surfaces)
- Fuzzy edges at vegetation boundaries
- Unrealistic depth values in occluded regions

**After occlusion masking:**
- Smooth AND realistic depth (no hallucination)
- Sharp edges at leaves/branches
- Properly undefined depth in truly occluded regions

---

## Implementation Workflow

### 1️⃣ Pre-Implementation (1-2 hours)
- [ ] Read OCCLUSION_MASKING_EXPLAINED.md
- [ ] Read PHASE_1_OCCLUSION_MASKING.md (Part A-B)
- [ ] Understand the concept (should be able to explain to friend)
- [ ] Prepare workspace

### 2️⃣ Implementation (2-4 hours)
- [ ] Add OcclusionDetector to layers.py (copy-paste from roadmap)
- [ ] Integrate into trainer.py (modify 2 functions)
- [ ] Quick smoke test (5 training steps)
- [ ] Fix any shape/import errors

### 3️⃣ Training (4-6 hours)
- [ ] Run full training: `python train.py --model lite-mono ... --num_epochs 20`
- [ ] Monitor loss curves (should decrease smoothly)
- [ ] Save best checkpoint

### 4️⃣ Evaluation (1-2 hours)
- [ ] Run evaluation on val/test split
- [ ] Compare metrics vs M3
- [ ] Generate qualitative comparisons (side-by-side images)
- [ ] Document results

### 5️⃣ Results Documentation (1 hour)
- [ ] Update baseline_notes.md with M4a entry
- [ ] Create results table (M1 vs M3 vs M4a)
- [ ] Save visualizations for paper

**Total: 9-14 hours**

---

## Key Parameters

### Tunable Hyperparameters

| Parameter | Default | Effect | Range |
|---|---|---|---|
| `grad_threshold` | 0.5m | Sensitivity to depth changes | 0.3–0.8m |
| `dilation_radius` | 2 px | Width of occlusion boundary | 1–4 px |

### How to Adjust

**If occlusion mask is too aggressive (too many 0s):**
```python
grad_threshold = 0.7   # Higher = fewer boundaries detected
dilation_radius = 1    # Smaller = narrower boundaries
```

**If occlusion mask is too conservative (too many 1s):**
```python
grad_threshold = 0.3   # Lower = more boundaries detected
dilation_radius = 3    # Larger = wider boundaries
```

---

## Debugging Guide

### Common Issues

| Issue | Symptom | Solution |
|---|---|---|
| Shape mismatch | Crash during training | Check padding in OcclusionDetector |
| All zeros mask | Depth is flat everywhere | Increase grad_threshold |
| All ones mask | Hallucinations still present | Decrease grad_threshold |
| Worse than baseline | M4a error > M3 error | Disable masking, try gradient-based detection |
| Training slow | GPU not being used | Check `torch.cuda.is_available()` |

### Debug Prints

```python
# Add to trainer.py during testing:
if batch_idx == 0:
    print(f"Depth shape: {depth.shape}")
    print(f"Mask shape: {mask.shape}")
    print(f"Mask min/max: {mask.min():.3f} / {mask.max():.3f}")
    print(f"Mask mean: {mask.mean():.3f}")
    
    # If mean is very close to 0 or 1 → parameter issue
```

---

## Before Moving to Phase 2

**Phase 1 is COMPLETE when:**

- ✅ Code integrated and training runs without errors
- ✅ M4a validation error < M3 validation error (expected 10-15% improvement)
- ✅ Qualitative results look better (sharper edges, no hallucination)
- ✅ Results documented in baseline_notes.md
- ✅ Parameters locked (grad_threshold, dilation_radius finalized)

---

## File Locations

```
citrus_project/
├─ OCCLUSION_MASKING_EXPLAINED.md ← Read this first
├─ PHASE_1_OCCLUSION_MASKING.md ← Implementation details
├─ PHASE_1_CHECKLIST.md ← Step-by-step
└─ research/
   └─ baseline_notes.md ← Record M4a results here

layers.py ← Add OcclusionDetector class
trainer.py ← Integrate detector
```

---

## Next Phase (Phase 2)

After Phase 1 is complete:

**Phase 2: Boundary-Aware Loss** (1-2 weeks)
- Add explicit boundary preservation loss term
- Encourage sharp edges in depth predictions
- Alternative: Switch to BoRe-Depth approach

**Paper Story So Far:**
1. M1: Original Lite-Mono fails on vegetation (baseline)
2. M3: Fine-tuning on Citrus helps (domain adaptation)
3. M4a: Occlusion masking improves further (handles hidden pixels)
4. M4b: Boundary awareness makes edges sharp (explicit edge loss)

---

## Questions?

If stuck:
1. Check OCCLUSION_MASKING_EXPLAINED.md for concepts
2. Check PHASE_1_OCCLUSION_MASKING.md for code details
3. Check debugging section above for common issues
4. Print shapes and values during debugging

Good luck! 🚀
