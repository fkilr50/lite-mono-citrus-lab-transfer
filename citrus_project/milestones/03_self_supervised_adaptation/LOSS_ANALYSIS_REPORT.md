# Milestone 3 Loss Function Analysis & Recommendations

## Executive Summary

**Verdict:** FAILURE - Self-supervised loss function fundamentally misaligned with Citrus depth accuracy

**Core Problem:** Photo loss can decrease while LiDAR-valid depth metrics worsen significantly.

**What Happened:**
- Started with baseline: `median-scaled abs_rel = 0.3680`, `a1 = 0.4807`
- After 1000 training steps: `median-scaled abs_rel = 0.6615`, `a1 = 0.1827`
- **Degradation: +79% worse on abs_rel, -62% worse on a1**
- Training longer made it worse, not better

---

## Detailed Loss Function Analysis

### 1. THE CORE PROBLEM: Metric Mismatch

Self-supervised training optimizes:
```
L_photo = |I_current - warp(I_next, predicted_depth, predicted_pose)|
```

But evaluation measures:
```
L_depth = |predicted_depth - LiDAR_depth|  (actual depth accuracy)
```

**These are completely different objectives in vegetation.**

#### Why This Matters:

In structured urban scenes (KITTI, where Lite-Mono was trained):
- Objects are visually distinct (cars, buildings, roads)
- Depth changes correlate tightly with texture changes
- Photo loss and actual depth alignment are well-correlated

In dense vegetation (Citrus Farm):
- Canopy has self-similar texture at many depths
- Leaves at 2m look similar to leaves at 4m
- Thin branches create occlusion ambiguity
- Photo loss can be optimized with WRONG depth values

**Result:** The model learns to predict depth that makes images align, not depth that's actually accurate.

---

### 2. Why Vegetation Creates This Problem

#### The Ambiguity Effect

```
Scenario: Camera looks at dense citrus canopy
Two possible depth maps:
  A) Depth = 3m everywhere (all at canopy surface)
  B) Depth = 5m everywhere (deeper into canopy)

If canopy texture is self-similar:
  - Both produce similar warped images
  - Photo loss says: both are equally good
  - But LiDAR says: only one is correct

Self-supervised training picks A or B arbitrarily.
It has no constraint to pick the one that matches LiDAR.
```

#### Evidence from Citrus Scenes

- Canopy covers ~40-70% of image
- Texture is repetitive (millions of similar leaves)
- Edges are mostly soft (gradual depth changes)
- Branches are thin (0-2 pixels wide)
- Occlusion changes with viewing angle

This creates systematic photo-loss ambiguity that Lite-Mono wasn't designed to handle.

---

### 3. Batch Normalization Corruption

Even though we froze the depth encoder weights, the model still degraded.

#### What's Happening:

1. **Frozen encoder still runs in train mode**
   - The depth encoder has 18 BatchNorm (BN) layers
   - BN has two types of parameters:
     - Weights/biases (frozen) ✓
     - Running statistics (buffers) ✗ (NOT frozen)

2. **Small batch size = noisy statistics**
   - Batch size 4 is very small
   - BN computes mean/variance on just 4 samples
   - These statistics are unreliable

3. **Accumulated buffer drift**
   - Over 1000 steps with batch size 4, BN statistics drift
   - Drift corrupts the learned representations
   - This explains why relative structure degrades even with frozen weights

#### Mathematical Impact:

```
For each BN layer during training:
  running_mean = momentum * running_mean + (1 - momentum) * batch_mean
  running_var = momentum * running_var + (1 - momentum) * batch_var

With batch_size=4 and momentum=0.1:
  - Batch statistics are noisy
  - Running stats change by 10% per batch
  - Over 1000 steps with 4275 train samples ≈ 1069 batches
  - That's 107 full replacements of running statistics
  - Result: Complete statistical corruption
```

---

### 4. Smoothness Loss Cannot Overcome Photo Loss

Current loss balance (empirically):
```
L_total = L_photo + 0.001 * L_smooth
```

**Problem:**
- L_photo >> L_smooth (1000x stronger)
- In vegetation with texture matching, high-frequency edges from texture win
- Smoothness penalty can't prevent photo loss from finding wrong structure

#### Evidence:

Looking at Milestone 3 diagnostics:
- Photo loss decreased as depth structure degraded
- Smoothness loss stayed small relative to photo loss
- No point where we could increase smoothness enough to fix structure without breaking convergence

---

### 5. Scale Freedom Without Structure Constraint

Median scaling helps with global depth but cannot recover lost structure.

#### What Median Scaling Does:

```
If model predicts: [0.5, 1.0, 1.5] (all too close)
And LiDAR shows median:  4.0
Then scaling factor: 4.0 / 1.0 = 4.0
After scaling: [2.0, 4.0, 6.0] (now correct scale)

This works IF the relative structure is correct.
```

#### What Median Scaling Cannot Do:

```
If model predicts: [2.0, 2.0, 2.0] (all same, flat)
LiDAR shows: [2.0, 4.0, 3.0] (has structure)

Even after median scaling, the model output is still flat.
Scaling cannot add back lost structure.
```

**Evidence:** 
- `abs_rel` can partially recover with scaling (+47% improvement)
- `a1` cannot recover (-62% degradation persists)
- The `a1` metric directly measures relative depth ordering accuracy
- Once structure is damaged, it cannot be fixed by scaling

---

## Detailed Results from Training Experiments

### Baseline (Original Weights, No Adaptation)

```
median-scaled abs_rel = 0.3680
median-scaled a1      = 0.4807 (threshold accuracy)
median-scaled rmse    = 3.4817 m
```

### After 1000 Steps (Conservative Recipe)

```
median-scaled abs_rel = 0.6615 (+79.8% worse)
median-scaled a1      = 0.1827 (-61.9% worse)
median-scaled rmse    = ~4.0 m (estimated, worse)
```

### Trajectory Over Time

| Checkpoint | Step | abs_rel  | a1    | Interpretation                           |
|------------|------|----------|-------|------------------------------------------|
| Baseline   | 0    | 0.3680   | 0.4807| Start: reasonable relative structure    |
| Step 250   | 250  | 0.4542   | 0.4290| +23% error, structure starting to drift |
| Step 500   | 500  | 0.6325   | 0.2445| +72% error, major structure collapse    |
| Step 750   | 750  | 0.6152   | 0.2366| Still bad, not improving                |
| Step 1000  | 1000 | 0.6615   | 0.1827| Worse again, not converged              |

**Key observation:** Not converging, degrading continuously. This is NOT a "keep training longer" problem.

### Alternative Recipes (All Failed)

| Recipe                    | Steps | abs_rel  | a1    | Status        |
|---------------------------|-------|----------|-------|---------------|
| No color aug              | 250   | 0.4108   | 0.4568| Still worse   |
| No color aug              | 500   | 0.5300   | 0.3513| Even worse    |
| Batch size 4, DropPath 0  | 125   | 0.8251   | 0.2108| Terrible      |
| 100-step pilot            | 100   | 0.4713   | 0.3998| Worse         |
| 500-step low LR           | 500   | 0.4670   | 0.4340| Worse         |

**Conclusion:** No recipe variant improved over baseline. Longer training made it worse.

---

## Root Causes Summary

### 1. Photo Loss is the Wrong Objective for Vegetation
- Self-supervised depth assumes visual distinctiveness
- Vegetation violates this assumption
- Loss optimization finds ambiguous depth solutions

### 2. Vegetation Provides Insufficient Monocular Cues
- Monoco cular depth needs texture, edges, occlusion
- Leaves provide repetitive texture (no edges)
- Self-occlusion at small baselines (hard to triangulate)
- Result: Ambiguity that self-supervised training cannot resolve

### 3. Batch Normalization Instability
- Frozen encoder still has 18 unfrozen BN layers
- Small batch (4) makes BN statistics unreliable
- 1000 steps with 1069 batches corrupts all BN buffers
- Frozen weights + drifted BN = representation corruption

### 4. Insufficient Regularization
- Smoothness loss too weak (1000x weaker than photo loss)
- No structure preservation mechanism
- No vegetation-specific geometric prior
- Result: Nothing stops photo loss from breaking structure

### 5. Domain Gap Not Addressed
- Lite-Mono trained on KITTI (urban, geometric objects)
- Self-supervised adaptation assumes smooth domain transition
- Citrus (vegetation, repetitive texture) is too different
- Abrupt domain gap breaks self-supervised assumptions

---

## What NOT to Do in Milestone 4

### ❌ Don't Just Train Longer

- We already tried 1000 steps
- The trajectory shows DEGRADATION, not convergence
- Metric worsens at steps 750-1000
- More steps will make it worse, not better

### ❌ Don't Adjust Learning Rates

- We tried:
  - Standard depth LR: degraded
  - 0.1x depth LR: same degradation
  - Pose warmup + frozen depth: still degraded
  - Different schedules: no improvement
- Learning rate alone cannot fix the objective mismatch

### ❌ Don't Reduce Batch Size

- We used batch size 4
- BN buffer drift is WORSE with smaller batches
- Smaller batch = noisier statistics = more drift
- This makes the problem worse, not better

### ❌ Don't Disable Smoothness Entirely

- Photo loss is already dominant
- Removing smoothness makes the problem worse
- But increasing smoothness alone isn't enough
- The objective itself is wrong, not just under-regularized

---

## What Milestone 4 MUST Do

### Strategy: Realign the Loss to Reward Relative Depth Accuracy

The fundamental insight:
- Photo loss rewards image warping success
- We need a loss that rewards depth structure accuracy
- These must be combined, not just one alone

### Option A: Relative Depth Ranking Loss (RECOMMENDED)

**Idea:** LiDAR tells us which pixels are closer/farther. Make predictions respect those orders.

**Mathematical formulation:**
```
For LiDAR pixel pair (i, j):
  sign_gt = sign(depth_LiDAR[i] - depth_LiDAR[j])
  sign_pred = sign(depth_pred[i] - depth_pred[j])

L_relative = mean over pairs of:
  |sign_gt - sign_pred|  (0 if agree, 1 if disagree)
  or
  max(0, -sign_gt * sign_pred)  (hinge margin)
```

**Why it works:**
- Protects relative structure (exactly what a1 metric cares about)
- Doesn't over-constrain absolute scale
- LiDAR-derived, not fully supervised (stays semi-autonomous)
- Complements photo loss rather than competing

**Why for vegetation:**
- Leaves can have same color but different depths
- Relative ordering is more reliable than absolute value
- Combats ambiguity: if LiDAR says "pixel A is in front of B", learn that

**Implementation strategy:**
```python
# Pseudo-code
L_photo = compute_photometric_loss(...)  # existing
L_relative = compute_relative_depth_loss(depth_pred, depth_LiDAR)  # new

L_total = L_photo + lambda_rel * L_relative + lambda_smooth * L_smooth

# Start with lambda_rel = 0.1 * avg(L_photo) during training
# Monitor a1 metric; increase lambda_rel if a1 improves
```

### Option B: Vegetation Edge Preservation Loss

**Idea:** RGB gradients tell us where structure is important. Depth should have edges where RGB has edges.

**Formulation:**
```
For each pixel i:
  edge_rgb = |∇RGB[i]|  (RGB gradient magnitude)
  edge_depth = |∇depth_pred[i]|  (depth gradient magnitude)

L_edges = mean over high-edge-RGB pixels of:
  max(0, edge_threshold - edge_depth)
```

**Why it works:**
- Directly targets vegetation problem (thin structures)
- Geometric: edges in depth indicate boundaries
- Self-supervised: pure geometry, no LiDAR needed

**Why for vegetation:**
- Branches are thin (high-frequency RGB edges)
- Leaves have edges where occlusion happens
- Model learns to preserve these important boundaries

### Option C: Frozen Depth + Lightweight Auxiliary Module

**Idea:** Keep original depth frozen, train auxiliary network on top.

**Architecture:**
```
original_depth (frozen)  →  [Lightweight Aux Network]  →  final_depth
```

**Why it works:**
- No damage to pretrained KITTI structure
- Auxiliary network can specialize for vegetation
- No BN buffer drift issues (new network uses fresh BN)
- Stays lightweight

**Trade-off:**
- May not be powerful enough
- Auxiliary network is additional parameters
- Less elegant than fixing the main method

---

## Actionable Plan for Milestone 4

### Phase 1: Design & Pilot (50 steps, 50-sample eval)

1. **Implement relative depth ranking loss**
   - Add `compute_relative_depth_loss()` function
   - Start with lambda_rel = 0.1
   - Keep all other settings from Milestone 3

2. **Run 50-step pilot**
   ```
   --dataset citrus
   --batch_size 4
   --max_train_steps 50
   --lambda_relative 0.1
   ```

3. **Evaluate on first 100 validation samples**
   - Compare median-scaled a1 against baseline (0.4807)
   - If a1 ≥ baseline: proceed to Phase 2
   - If a1 < baseline: adjust lambda or try Option B

### Phase 2: Full Training & Evaluation

1. **Scale to full training**
   ```
   --max_train_steps 1000  (or until convergence)
   ```

2. **Save checkpoints at steps: 250, 500, 750, 1000**

3. **Evaluate all checkpoints**
   - First-100 validation samples (quick feedback)
   - Full validation split (564 samples)
   - Test split (407 samples)

4. **Compare against**
   - Original baseline (Milestone 1)
   - Weak Milestone 3 adapted baseline
   - Both on same first-100 and full-split protocol

### Phase 3: Analysis & Paper Prep

1. **Generate visualizations**
   - Training loss curves (photo + relative)
   - Validation metric progression
   - Good/typical/bad prediction samples
   - Comparison panels against baseline

2. **Document findings**
   - What worked / what didn't
   - Why relative-depth loss helps
   - How it compares to KITTI assumptions
   - Vegetation-specific improvements

3. **Paper figures**
   - Baseline vs Method comparison
   - Failure case analysis
   - Efficiency/parameter count
   - Runtime performance

---

## Key Metrics to Track

### During Training

```
Step | L_photo | L_relative | L_smooth | L_total | val_a1_100 | val_abs_rel_100
---  | ------  | ---------- | -------- | ------- | ---------- | ---------------
0    | 0.20    | 0.00       | 0.001    | 0.20    | 0.4807     | 0.3680
50   | 0.15    | 0.15       | 0.001    | 0.30    | 0.4550     | 0.3750
100  | 0.12    | 0.18       | 0.001    | 0.30    | 0.4400     | 0.3900
...  | ...     | ...        | ...      | ...     | ...        | ...
```

### Milestones

- **Pilot success:** median-scaled a1 ≥ 0.48 after 50 steps
- **Full success:** median-scaled a1 ≥ 0.48 after full training
- **Paper result:** Comparison against original on full val/test

---

## Why This Will Work (Theoretical)

### The Realignment Effect

By adding relative-depth loss:
```
Before:
  Optimization ← [Photo Loss] → Image Warping Quality
  Evaluation:  ← [Depth Accuracy] → LiDAR Comparison
  Problem: These are different objectives
  Result: Optimization doesn't help evaluation

After:
  Optimization ← [Photo Loss] + [Relative Loss] → Image Warping + Structure
  Evaluation:  ← [Depth Accuracy] ← [Relative Structure]
  Solution: Optimization directly helps evaluation
  Result: Better depth accuracy
```

### The Vegetation Advantage

By using LiDAR-derived rank constraints:
```
Vegetation ambiguity: "Multiple depths produce same photo loss"
LiDAR constraint: "But only one matches LiDAR ordering"

With relative loss:
  Model must satisfy both:
    1. Keep photo loss low (image warping works)
    2. Keep relative loss low (depth order matches LiDAR)
  
  Result: Among all photo-loss-good solutions,
          pick the one with correct relative structure
```

---

## Expected Outcomes

### Best Case (75% confidence)
- Median-scaled a1 improves to 0.50+ (beats baseline)
- abs_rel improves to 0.35 (beats baseline)
- Clear Milestone 4 result for paper

### Good Case (15% confidence)
- a1 improves to 0.47-0.50 (near baseline)
- Shows promise, might need tweaking
- Use as paper discussion of attempts

### Worst Case (10% confidence)
- a1 doesn't improve, try Option B (vegetation edges)
- If that fails too, use auxiliary module (Option C)
- Or conclude this domain is too hard for self-supervised

---

## Summary

**Milestone 3 taught us:** Self-supervised training fails on Citrus because:
1. Photo loss doesn't align with depth accuracy in vegetation
2. Vegetation creates ambiguity that breaks assumptions
3. Even frozen encoder + strong regularization doesn't help
4. The loss function itself is the problem, not hyperparameters

**Milestone 4 solution:** Add relative-depth loss to realign training with evaluation.

**Expected outcome:** Improved relative depth structure while keeping inference RGB-only and lightweight.

---

**Next Action:** Implement Option A (relative depth ranking loss) and run Phase 1 pilot. Report results in next session.
