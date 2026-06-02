# Focused Research Strategy (Approved by ChatGPT Review)

**Date:** 2026-04-27  
**Status:** Research direction locked in  
**Paper Title (Target):** "Occlusion-Aware Lightweight Depth for Vegetation: Self-Supervised Monocular Depth in Citrus Orchards"

---

## The Core Problem (One Sentence)

**Vegetation = occlusion + thin structures + weak textures + boundary confusion.**

---

## The Solution (One Sentence)

**Lightweight self-supervised monocular depth with occlusion-aware loss + boundary-aware training.**

---

## Why This Matters for the Robot

1. **Occlusion handling** → Can distinguish leaves from branches from trunk
2. **Boundary sharpness** → Can detect edges between fruit and canopy
3. **Lightweight** → Runs on robot at 30fps RGB-only
4. **Self-supervised** → Works with robot's own video sequences

---

## Four Core Papers (All You Need to Read)

| Paper | Role | Key Takeaway |
|---|---|---|
| **Occlusion-Aware SSL (Endoscopy)** | Loss design | Mask photometric loss where occlusion suspected |
| **BoRe-Depth** | Boundary refinement | Preserve sharp edges in depth predictions |
| **Sharper Object Boundaries** | Alternative approach | Compare against BoRe-Depth for Phase 2 |
| **RTS-Mono** | Architecture baseline | Validate lightweight design; compare metrics |

---

## Two-Phase Implementation (This Is Your M4)

### Phase 1: Occlusion-Aware Masking

**What:** Add occlusion detection + loss masking to Lite-Mono's photometric training

**From paper:** Occlusion-Aware SSL (endoscopy approach)

**Implementation:**
1. Detect depth discontinuities (likely occlusion boundaries)
2. Create occlusion mask (1 = confident, 0 = uncertain)
3. Weight photometric loss: `loss = loss_before * mask`
4. Fine-tune original Lite-Mono on Citrus sequences (M3 + occlusion)

**Expected result:**
- Model avoids "hallucinating" depth in occluded regions
- Sharper depth at vegetation boundaries

**Code location:** `trainer.py` modification in photometric loss computation

**Metrics:** Depth MAE comparison (M3 vs M4a on val split)

---

### Phase 2: Boundary-Aware Refinement

**What:** Add explicit boundary preservation to Phase 1 model

**From paper:** BoRe-Depth OR Sharper Boundaries (pick one approach)

**Implementation:**
1. Detect object boundaries (edges in depth gradient)
2. Add boundary loss term: `L_boundary = encourage_sharp_edges`
3. Combine with Phase 1: `L_total = L_photo * mask + λ * L_boundary`
4. Fine-tune Phase 1 model on Citrus

**Expected result:**
- Crisp leaf/branch/trunk boundaries
- Better canopy geometry overall

**Code location:** `trainer.py` new loss term

**Metrics:** 
- Depth MAE
- Edge sharpness score (custom metric)
- Depth gradient smoothness

---

## Optional Phase 3: Architecture Comparison

**If time allows (after Phase 2):**

1. Train **RTS-Mono** end-to-end on Citrus
2. Compare against Phase 2 (Lite-Mono + occlusion + boundary)
3. Report: accuracy, runtime, parameter count

**This validates:** Lightweight design choice

---

## Mapping to Project Milestones

| Milestone | What | Time |
|---|---|---|
| M0 | Dataset audit | ✅ Done |
| M1 | Original baseline | Next (1 week) |
| M2 | Citrus training setup | Same as M1 |
| M3 | Self-supervised Citrus adapt | 1 week |
| **M4a** | **+ Occlusion masking (Phase 1)** | **1-2 weeks** |
| **M4b** | **+ Boundary awareness (Phase 2)** | **1-2 weeks** |
| M5 | (Optional) Architecture compare | If time |
| M6 | Paper write-up | Final 1-2 weeks |

---

## The Paper (High-Level Structure)

```
1. MOTIVATION
   - Vegetation is hard: occlusion, thin structures, weak textures
   - Lightweight monocular depth for robot
   - Domain gap: KITTI urban ≠ citrus orchards

2. BACKGROUND
   - Lite-Mono architecture
   - Self-supervised photometric loss
   - Problem: vanilla loss doesn't handle occlusion/boundaries well

3. METHOD (YOUR CONTRIBUTION)
   - Phase 1: Occlusion-aware masking
     * Detect boundaries
     * Mask uncertain regions
   - Phase 2: Boundary-aware loss
     * Encourage sharp edges
     * Combined photometric + boundary loss

4. RESULTS
   - Table: M1 (baseline) → M3 (adapted) → M4a (occlusion) → M4b (boundary)
   - Depth error, edge quality, runtime
   - Qualitative: canopy, aisles, trunks, high-occlusion scenes
   - Failure analysis

5. COMPARISON (Optional)
   - RTS-Mono baseline (if Phase 3 done)

6. CONCLUSION
   - Lightweight depth + occlusion + boundary = better vegetation scenes
   - Deployment-ready for robot
```

---

## What NOT to Do

- ❌ Don't implement architecture searches (MambaDepth, large kernels)
- ❌ Don't add language guidance
- ❌ Don't add diffusion models
- ❌ Don't try multi-task learning (detection + depth)

**Why?** These dilute your contribution and create scope creep.

---

## Success Criteria (For Paper)

1. ✅ M1 baseline established (original Lite-Mono on Citrus)
2. ✅ M3 shows adaptation helps (fine-tune > baseline)
3. ✅ M4a shows occlusion masking helps (Phase 1 > M3)
4. ✅ M4b shows boundary awareness helps (Phase 2 > Phase 1)
5. ✅ Qualitative examples show clear improvement in vegetation scenes
6. ✅ Runtime/efficiency maintained (lightweight constraint met)

**If you hit all 6:** You have a strong, focused, publishable paper.

---

## Next Action

1. **Friend (main dev):** Run M1 baseline (original Lite-Mono on Citrus val/test)
2. **Friend A (you):** Read core papers (focus on loss design sections)
3. **Together:** Discuss Phase 1 implementation details
4. **Then:** Code Phase 1, measure M4a results
5. **Then:** Code Phase 2, measure M4b results
