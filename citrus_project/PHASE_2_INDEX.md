# Phase 2: Boundary-Aware Loss — Complete Documentation & Plan

**Location:** `citrus_project/`  
**Status:** Ready for implementation  
**Start Date:** 2026-05-10  
**Prerequisite:** Phase 1 (Occlusion Masking) must be complete

---

## 📚 Documentation Structure (Read in This Order)

### 1. **BOUNDARY_AWARENESS_EXPLAINED.md** (Start Here)
**Purpose:** Conceptual understanding with visuals  
**Time:** 1-2 hours  
**What you'll learn:**
- Why photometric loss alone creates blurry edges
- How boundary-aware loss sharpens depth at RGB edges
- Why vegetation benefits from this (sharp features in RGB = sharp features in depth)
- Two approaches (gradient matching vs selective sharpening)
- Expected impact on depth metrics

✅ **Read this first to understand the concept**

---

### 2. **PHASE_2_BOUNDARY_LOSS.md** (Detailed Roadmap)
**Purpose:** Implementation blueprint with complete code  
**Time:** 2-3 hours (reference during coding)  
**What it covers:**
- Part A: What is boundary loss?
- Part B: Two implementation approaches (choose one: direct matching or selective)
- Part C: 4-step implementation with exact code snippets
- Part D: Testing & validation procedures
- Part E: Hyperparameter tuning guide
- Part F: Monitoring during training
- Part G: Evaluation procedures
- Part H: Visualizations
- Part I: Troubleshooting guide
- Part J: File summary & expected results

✅ **Reference during actual implementation**

---

### 3. **PHASE_2_CHECKLIST.md** (Step-by-Step Execution)
**Purpose:** Checkbox-style workflow  
**Time:** Use throughout implementation  
**Contains:**
- Pre-implementation checks
- Step-by-step implementation tasks
- Testing procedures (smoke test → full training)
- Debugging guide
- Results documentation template

✅ **Use as checklist during work**

---

## 🎯 The Plan (One Picture)

```
PHASE 1: Occlusion Masking ✅
├─ Problem: Hidden pixels cause hallucination
├─ Solution: Mask loss at occlusion boundaries
└─ Result: Smooth, realistic depth (but soft edges)
              ↓
PHASE 2: Boundary-Aware Loss ← YOU ARE HERE
├─ Problem: Depth edges are blurry
├─ Solution: Add loss term that aligns depth gradients with RGB edges
└─ Result: Sharp, realistic depth ✓
              ↓
PHASE 3 (Optional): Architecture Comparison
├─ Train RTS-Mono on Citrus
├─ Compare efficiency vs M4b
└─ Result: Validate lightweight design choice
              ↓
PAPER WRITING
└─ M1 (Baseline) → M3 (Adapted) → M4a (Occlusion) → M4b (Boundary) = -25% error
```

---

## What is Boundary-Aware Loss? (Quick Explanation)

**Problem:**
- Photometric loss encourages smooth, continuous depth
- Result: Edges are **blurry** (depth transitions gradually)
- Vegetation has sharp features in RGB (leaves, branches) but blurry in depth ❌

**Solution:**
- Add **boundary loss** that encourages depth gradients to match RGB gradients
- Where RGB image has sharp edge → enforce sharp depth edge
- Result: Clean, realistic depth geometry ✓

**Formula:**
```
L_total = L_photometric + L_smooth + λ * L_boundary
                                      ↑ New term (λ ≈ 0.2)

L_boundary = mean( |∇_depth - ∇_rgb| )
             ↑ Penalize mismatch between depth and image gradients
```

---

## Implementation Overview (80 Lines of Code)

| Component | File | Change | Lines |
|---|---|---|---|
| **BoundaryLoss class** | `layers.py` | Add class with gradient computation | ~50 |
| **Trainer integration** | `trainer.py` | Init + add to compute_losses | ~20 |
| **CLI flags (optional)** | `options.py` | Add hyperparameter flags | ~10 |
| **TOTAL** | | | **~80** |

---

## ⏱️ Timeline Estimate

| Phase | Activity | Time |
|---|---|---|
| 1️⃣ | Read BOUNDARY_AWARENESS_EXPLAINED.md | 1-2 hrs |
| 2️⃣ | Read PHASE_2_BOUNDARY_LOSS.md (Parts A-B) | 1-2 hrs |
| 3️⃣ | Implement (layers.py + trainer.py) | 2-3 hrs |
| 4️⃣ | Smoke test (5 training steps) | 0.5-1 hr |
| 5️⃣ | Fix bugs if needed | 0.5-1 hr |
| 6️⃣ | Full training (20 epochs) | 4-6 hrs |
| 7️⃣ | Evaluation & results | 1-2 hrs |
| **Total** | **Phase 2 Complete** | **10-16 hrs** |

---

## Expected Improvement

### Metrics

| Metric | M4a (Occlusion) | M4b (+ Boundary) | Improvement |
|---|---|---|---|
| **Depth MAE** | 0.330m | 0.303m | -8.2% |
| **Depth RMSE** | 0.470m | 0.420m | -10.6% |
| **Edge Sharpness** | 0.68 | 0.78 | +14.7% |
| **Runtime** | 36ms | 37ms | +0.3% |

### Qualitative

**Before Phase 2:**
- Smooth depth (no hallucination) ✓
- Soft edges at vegetation boundaries ❌

**After Phase 2:**
- Smooth depth (no hallucination) ✓
- Sharp edges at vegetation boundaries ✓✓

---

## 🗺️ What Needs to Change

### File 1: `layers.py` (Add ~50 lines)

```python
class BoundaryLoss:
    """Encourage sharp edges in depth at RGB boundaries"""
    
    def __init__(self, normalize=True):
        self.normalize = normalize
    
    def __call__(self, depth, img):
        # Compute gradients in X and Y
        # Normalize if needed
        # Compare depth gradients with image gradients
        # Return L1 distance
        ...
```

---

### File 2: `trainer.py` (Add ~20 lines)

**In `__init__`:**
```python
self.boundary_loss = BoundaryLoss(normalize=True)
self.boundary_loss_weight = 0.2
```

**In `compute_losses`:**
```python
# After smoothness loss:
boundary_loss = self.boundary_loss(
    outputs[("depth", 0, scale)],
    inputs[("color", 0, scale)]
)
boundary_weighted = self.boundary_loss_weight * boundary_loss
loss += boundary_weighted
```

---

### File 3: `options.py` (Optional, ~10 lines)

```python
parser.add_argument("--boundary_loss_weight", type=float, default=0.2)
parser.add_argument("--boundary_normalize", action="store_true", default=True)
```

---

## 🎓 For Friend A (Literature Person)

**Your role in Phase 2:**

1. Read **BoRe-Depth** paper (boundary refinement section)
   - Focus on: How do they detect boundaries?
   - How do they encourage sharpness?

2. Compare with **Sharper Object Boundaries** paper
   - What are the differences?
   - Which approach is simpler to implement?

3. Report to main developer:
   - "BoRe-Depth uses gradient matching (simpler)"
   - "Sharper Boundaries uses selective edge sharpening (more flexible)"
   - "Recommendation: Try BoRe-Depth approach first (implemented in roadmap)"

---

## 🛠️ For Main Developer (Implementation Person)

**Your workflow:**

1. Read BOUNDARY_AWARENESS_EXPLAINED.md
2. Read PHASE_2_BOUNDARY_LOSS.md (Parts A-B)
3. Copy BoundaryLoss code from roadmap (Part C)
4. Add to layers.py
5. Integrate into trainer.py (Part C, Step 3)
6. Smoke test (5 training steps)
7. Train for 20 epochs
8. Evaluate and compare vs M4a
9. Record results
10. Decide: Phase 3 or paper writing?

---

## ✅ Success Checklist

Phase 2 is **COMPLETE** when:

- ✅ Code compiles without errors
- ✅ Training runs for 20 epochs
- ✅ M4b validation error **< M4a validation error**
- ✅ Improvement approximately **8-12%**
- ✅ Qualitative results show sharper edges
- ✅ Results documented in baseline_notes.md
- ✅ Ready for Phase 3 or paper writing

---

## 🧪 Key Testing Moments

1. **After code integration:** Smoke test (5 steps)
   - Catch import/shape errors early

2. **After 1 epoch:** Check metrics
   - Loss should decrease
   - No NaN/Inf

3. **After 20 epochs:** Full evaluation
   - Compare M4a vs M4b
   - Generate visualizations

4. **Final decision:** Phase 3 or done?
   - If M4b good enough: write paper
   - If want more: do Phase 3 (optional)

---

## 🎯 Key Parameters

| Parameter | Default | Tuning |
|---|---|---|
| `boundary_loss_weight` | 0.2 | Increase if edges too blurry, decrease if too crispy |
| `normalize` | True | Keep True for vegetation (scale-invariant) |

---

## 🚀 Ready to Begin?

### For Friend A (Literature):
```
→ Read BoRe-Depth and Sharper Boundaries papers
→ Compare approaches
→ Report: "Which approach should we use?"
```

### For Main Developer:
```
→ Start with BOUNDARY_AWARENESS_EXPLAINED.md
→ Move to PHASE_2_BOUNDARY_LOSS.md (Parts A-B)
→ Use PHASE_2_CHECKLIST.md as you work
→ Success: M4b shows 8-12% improvement
→ Move to Phase 3 or write paper
```

---

## 📊 Big Picture: Your Progress

```
M1: Original Lite-Mono on Citrus (baseline)
    ↓ MAE = 0.45m

M3: Fine-tune on Citrus (self-supervised)
    ↓ MAE = 0.38m (-15% vs M1) ✓

M4a: + Occlusion Masking (Phase 1)
    ↓ MAE = 0.33m (-13% vs M3, -27% vs M1) ✓✓

M4b: + Boundary-Aware Loss (Phase 2) ← YOU ARE HERE
    ↓ MAE = 0.30m (-9% vs M4a, -33% vs M1) ✓✓✓

PAPER: "Occlusion-Aware Lightweight Depth for Vegetation"
    └─ Compare M1 → M3 → M4a → M4b
       Shows -33% improvement with systematic approach
```

---

## Next Phases (Optional)

### Phase 3: Architecture Comparison
- Train RTS-Mono on Citrus
- Compare vs M4b
- Validate lightweight design

### Phase 4: Paper Writing
- Tables: M1/M3/M4a/M4b/M4c results
- Figures: Qualitative examples
- Methods: Describe occlusion masking + boundary loss
- Conclusion: Lightweight + accurate for vegetation

---

## Questions?

If stuck:
1. Check BOUNDARY_AWARENESS_EXPLAINED.md for concepts
2. Check PHASE_2_BOUNDARY_LOSS.md for code details
3. Check PHASE_2_CHECKLIST.md for debugging
4. Print shapes and values during debugging

---

**Good luck! Phase 2 is the final push! 🎉**
