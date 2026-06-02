# Phase 1: Occlusion Masking — Complete Documentation Index

**Location:** `citrus_project/`  
**Status:** Ready for implementation  
**Start Date:** 2026-04-27

---

## 📚 Documentation Structure (Read in This Order)

### 1. **OCCLUSION_MASKING_EXPLAINED.md** (Start Here)
**Purpose:** Conceptual understanding with visuals  
**Time:** 1-2 hours  
**What you'll learn:**
- What is occlusion and why it causes problems
- Why vanilla photometric loss hallucinates in vegetation
- How occlusion masking prevents hallucination
- Real Citrus examples with visualizations

✅ **Read this first to understand the concept**

---

### 2. **PHASE_1_OCCLUSION_MASKING.md** (Detailed Roadmap)
**Purpose:** Implementation blueprint with code  
**Time:** 2-3 hours (reference during coding)  
**What it covers:**
- Part A: Understanding occlusion masking (repeat from file 1)
- Part B: Methods to detect occlusion (gradient vs error-based)
- Part C: 5 implementation steps with exact code
- Part D: Testing & validation procedures
- Part E: Hyperparameter tuning guide
- Part F: File locations to modify
- Part G: Expected outcomes

✅ **Reference during actual implementation**

---

### 3. **PHASE_1_CHECKLIST.md** (Step-by-Step Execution)
**Purpose:** Checkbox-style workflow  
**Time:** Use throughout implementation  
**Contains:**
- Pre-implementation checks
- Step-by-step implementation tasks
- Testing procedures
- Debugging guide
- Results documentation template

✅ **Use as checklist during work**

---

### 4. **PHASE_1_SUMMARY.md** (Overview & Quick Reference)
**Purpose:** One-document summary  
**Time:** 20 minutes to read  
**Has:**
- TL;DR paragraph
- Problem/solution explanation
- Implementation overview
- Expected results table
- Complete workflow diagram
- Debugging guide

✅ **Quick reference when you need to refresh**

---

## 🎯 Quick Reference: What Needs to Change

### File 1: `layers.py`
**Add:** OcclusionDetector class (~40 lines)
```python
class OcclusionDetector:
    def __init__(self, grad_threshold=0.5, dilation_radius=2):
        # Store parameters
    
    def __call__(self, depth):
        # Compute gradients
        # Detect boundaries
        # Dilate
        # Return mask
```

### File 2: `trainer.py`
**Modify 1:** `__init__` method
```python
self.occlusion_detector = OcclusionDetector(...)
```

**Modify 2:** `compute_reprojection_loss` function
```python
def compute_reprojection_loss(self, pred, target, depth=None, occlusion_aware=False):
    # Existing code
    if occlusion_aware and depth is not None:
        occlusion_mask = self.occlusion_detector(depth)
        reprojection_loss = reprojection_loss * occlusion_mask
    return reprojection_loss
```

**Modify 3:** Call sites in `compute_losses`
```python
# Add depth and occlusion_aware parameters to calls
reprojection_losses.append(
    self.compute_reprojection_loss(
        pred, target,
        depth=outputs[("depth", 0, scale)],
        occlusion_aware=True
    )
)
```

**Total:** ~75 lines of code changes

---

## ⏱️ Timeline Estimate

| Phase | Activity | Time |
|---|---|---|
| 1️⃣ | Read OCCLUSION_MASKING_EXPLAINED.md | 1-2 hrs |
| 2️⃣ | Study PHASE_1_OCCLUSION_MASKING.md (Part A-B) | 1-2 hrs |
| 3️⃣ | Implement (layers.py + trainer.py) | 2-4 hrs |
| 4️⃣ | Smoke test (5 training steps) | 0.5-1 hr |
| 5️⃣ | Fix bugs if needed | 0.5-1 hr |
| 6️⃣ | Full training (20 epochs) | 4-6 hrs |
| 7️⃣ | Evaluation & results | 1-2 hrs |
| **Total** | **Phase 1 Complete** | **9-14 hrs** |

---

## 🔄 The Concept in One Image

```
PROBLEM:
    Hidden pixels in source frame
         ↓
    High reprojection error
         ↓
    Model hallucinates depth
         ↓
    Unrealistic vegetation surfaces

SOLUTION:
    Detect depth boundaries
         ↓
    Create occlusion mask (1=confident, 0=uncertain)
         ↓
    Apply mask to loss: Loss *= Mask
         ↓
    Model ignores hidden pixels
         ↓
    Smooth, realistic depth

RESULT:
    10-15% improvement on Citrus test set ✓
```

---

## 📊 Expected Improvement

**Before Phase 1:**
- M3 (Citrus-adapted Lite-Mono): 0.38m MAE, fuzzy edges, some hallucinations

**After Phase 1:**
- M4a (Occlusion-aware): 0.33m MAE, sharp edges, no hallucinations
- **Improvement: -13%, edge quality: High**

---

## ⚠️ Common Pitfalls (Avoid These!)

❌ Forget to pad gradients back to original size → Shape mismatch  
✅ Always use `F.pad()` to match input depth dimensions

❌ Apply mask AFTER averaging loss → Loses effectiveness  
✅ Apply mask BEFORE averaging: `loss *= mask` before `.mean()`

❌ grad_threshold too high (e.g., 50m) → All 0s mask  
✅ Use reasonable threshold for depth range (0.3–0.8m for Citrus)

❌ Training makes model worse → Wrong gradient threshold  
✅ Check mask visualizations first, adjust threshold iteratively

---

## 🎓 For Friend A (Literature Person)

**Your role in Phase 1:**

1. ✅ Read the **Occlusion-Aware SSL (Endoscopy)** paper
   - Focus on: Loss masking design section
   - Take notes: How do they detect occlusion in medical images?
   - Report: "Here's why it works, here's how to apply to vegetation"

2. Read **BoRe-Depth** paper (for Phase 2 prep)
   - Skim the boundary-aware components
   - Compare with Sharper Boundaries approach

3. Discuss with main developer:
   - "This loss masking approach should work for vegetation similar to endoscopy"
   - "Here's why: dense occlusion (leaves) = dense occlusion (medical tissue)"

---

## 🛠️ For Main Developer (Implementation Person)

**Your workflow:**

1. Read docs in order (OCCLUSION_MASKING_EXPLAINED → PHASE_1_OCCLUSION_MASKING)
2. Copy OcclusionDetector code from roadmap
3. Integrate into trainer.py
4. Run smoke test (catch import/shape errors)
5. Train for 20 epochs
6. Evaluate and compare vs M3
7. Record results
8. Move to Phase 2

---

## ✅ Success Checklist

Phase 1 is COMPLETE when:

- [ ] Code compiles without errors
- [ ] Training runs for 20 epochs
- [ ] M4a validation error < M3 validation error
- [ ] Improvement is approximately 10-15%
- [ ] Qualitative results look better (sharper edges)
- [ ] Results documented in baseline_notes.md
- [ ] Ready to move to Phase 2

---

## 📞 Quick Troubleshooting

| Problem | Check This |
|---|---|
| Shape mismatch | PHASE_1_OCCLUSION_MASKING.md Part D, Step 1 |
| Loss doesn't decrease | PHASE_1_CHECKLIST.md Debugging section |
| M4a worse than M3 | Adjust grad_threshold (see tuning guide) |
| Training very slow | GPU usage, num_workers setting |

---

## 📍 Next Phase (Phase 2)

After Phase 1 completes successfully:

**Phase 2: Boundary-Aware Loss** (1-2 weeks)
- Add explicit boundary preservation loss
- Read BoRe-Depth paper for implementation
- Expected improvement: Additional 5-10%

**Total paper story:**
- M1 (Baseline) → M3 (Adapted) → M4a (Occlusion) → M4b (Boundary) = **-25% depth error**

---

## 📝 Files Summary

| File | Purpose | Read When |
|---|---|---|
| OCCLUSION_MASKING_EXPLAINED.md | Conceptual guide | First (1-2 hrs) |
| PHASE_1_OCCLUSION_MASKING.md | Implementation details | During coding (reference) |
| PHASE_1_CHECKLIST.md | Step-by-step workflow | During implementation (checklist) |
| PHASE_1_SUMMARY.md | Quick reference | When refreshing/debugging |
| **This file** | **Index & overview** | **Now (you are here!)** |

---

## 🚀 Ready to Begin?

### For Friend A (Literature):
```
→ Read Occlusion-Aware SSL paper (endoscopy)
→ Take notes on loss masking section
→ Report findings to main dev
```

### For Main Developer:
```
→ Start with OCCLUSION_MASKING_EXPLAINED.md
→ Move to PHASE_1_OCCLUSION_MASKING.md
→ Use PHASE_1_CHECKLIST.md as you work
→ Success: M4a shows 10-15% improvement
```

---

**Good luck! You've got this! 🎉**

Questions? Refer to the relevant doc above, or debug with the guides provided.
