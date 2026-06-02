# Phase 1: Occlusion Masking Implementation Roadmap

**Objective:** Add occlusion-aware loss masking to Lite-Mono's photometric training

**Timeline:** 1-2 weeks  
**Complexity:** Medium (modifies loss computation, adds one new module)  
**Risk:** Low (non-breaking; can be toggled off)

---

## PART A: Understanding Occlusion Masking

### What is Occlusion Masking?

**Problem (Vanilla Photometric Loss):**

When training depth with photometric loss (comparing reprojected images), the model learns by minimizing the difference between:
- `target`: Original frame
- `pred`: Reprojected frame from adjacent frame using predicted depth

```
Loss = |target - pred|  ← Treat all pixels equally
```

**The Issue with Vegetation:**

In vegetation scenes, some pixels are **occluded** — they exist in the target frame but are hidden (by leaves, branches) in the source frame.

```
Target frame (what we see now):
[leaf] [leaf] [branch] [sky]

Source frame (from different angle):
[hidden] [hidden] [sky] [sky]  ← These pixels are occluded

When reprojected with correct depth:
[empty] [empty] [branch] [sky]  ← Reprojection can't recover hidden pixels
```

**The naive loss:**
```
Loss = | [leaf, leaf, branch, sky] - [empty, empty, branch, sky] |
       ↑ High loss at hidden pixels! ↑
```

**The model learns:** "Predict extra depth at the hidden pixels to make the image match"  
→ **Result:** Fake depth surfaces hallucinated in occluded regions

---

### Solution: Occlusion Masking

**Insight:** Don't penalize the loss where occlusion is likely

```
Mask = [0, 0, 1, 1]  ← 0 = probably occluded, 1 = probably visible
Loss = |target - pred| * Mask
     = [0, 0, (branch_err), (sky_err)]
```

**Result:** Model ignores hidden pixels, doesn't hallucinate depth there

---

## PART B: How to Detect Occlusion

### Method 1: Depth Gradient (Fastest, Most Practical)

**Idea:** Occlusions happen at depth discontinuities (edges)

```
Depth map:
[ 2.0  2.0  2.1 | 10.0 10.0]
  ↑ smooth       ↑ big jump = occlusion boundary

Occlusion mask (from gradient):
[1, 1, 0, | 0, 0]  ← Mark boundaries as uncertain
```

**How to implement:**
```python
def detect_occlusion_boundaries(depth):
    # Compute depth gradients in X and Y
    grad_x = torch.abs(depth[:, :, :-1, :] - depth[:, :, 1:, :])
    grad_y = torch.abs(depth[:, :, :, :-1] - depth[:, :, :, 1:])
    
    # Threshold: if gradient > threshold → likely occlusion boundary
    threshold = 0.5  # meters (adjust for Citrus depth range)
    occlusion_x = grad_x > threshold
    occlusion_y = grad_y > threshold
    
    # Combine: mark boundaries as uncertain (0), rest as confident (1)
    occlusion_mask = ~(occlusion_x | occlusion_y)  # Invert: 0 at boundaries
    
    return occlusion_mask
```

**Pros:**
- ✅ Very fast (just gradient computation)
- ✅ Works in self-supervised setting (no GT needed)
- ✅ Directly targets depth discontinuities

**Cons:**
- ❌ May miss some occlusions
- ❌ May mark valid edges as occlusions

---

### Method 2: Photometric Reprojection Error (Alternative, More Robust)

**Idea:** High reprojection error → likely occlusion

```python
def detect_occlusion_error(reprojection_loss):
    # If reprojection error is very high → probably occluded
    threshold = 0.3  # tune based on Citrus data
    occlusion_mask = reprojection_loss < threshold
    return occlusion_mask
```

**Pros:**
- ✅ Directly uses loss signal
- ✅ More robust to edge cases

**Cons:**
- ❌ Slower (need to compute reprojection first)
- ❌ May be circular reasoning (loss used to mask loss)

---

### **RECOMMENDATION: Use Method 1 (Depth Gradient)**
- Simpler, faster, more direct
- Less risk of circular dependency

---

## PART C: Implementation Steps

### Step 1: Create Occlusion Detection Module

**File:** `layers.py`

**Add this function:**

```python
class OcclusionDetector:
    """Detect occlusion boundaries from depth discontinuities"""
    
    def __init__(self, grad_threshold=0.5, dilation_radius=2):
        """
        Args:
            grad_threshold: Depth gradient threshold (meters)
            dilation_radius: Dilate mask to cover wider occlusion regions
        """
        self.grad_threshold = grad_threshold
        self.dilation_radius = dilation_radius
    
    def __call__(self, depth):
        """
        Args:
            depth: [B, 1, H, W] depth map
        Returns:
            occlusion_mask: [B, 1, H, W] where 1=confident, 0=uncertain
        """
        # Compute gradients
        grad_x = torch.abs(depth[:, :, :-1, :] - depth[:, :, 1:, :])
        grad_y = torch.abs(depth[:, :, :, :-1] - depth[:, :, :, 1:])
        
        # Pad to original size
        grad_x = torch.nn.functional.pad(grad_x, (0, 1, 0, 0))
        grad_y = torch.nn.functional.pad(grad_y, (0, 0, 0, 1))
        
        # Threshold: True where gradient > threshold (high = boundary)
        boundary_x = grad_x > self.grad_threshold
        boundary_y = grad_y > self.grad_threshold
        boundary = boundary_x | boundary_y
        
        # Dilate: expand boundaries to cover occlusion regions
        if self.dilation_radius > 0:
            kernel_size = 2 * self.dilation_radius + 1
            boundary = torch.nn.functional.max_pool2d(
                boundary.float(),
                kernel_size=kernel_size,
                stride=1,
                padding=self.dilation_radius
            ) > 0
        
        # Invert: 1 = confident (not boundary), 0 = uncertain (boundary)
        occlusion_mask = (~boundary).float()
        
        return occlusion_mask
```

---

### Step 2: Integrate into Trainer

**File:** `trainer.py`

**In `__init__` method, add:**

```python
self.occlusion_detector = OcclusionDetector(
    grad_threshold=0.5,  # Tunable: adjust for Citrus depth range
    dilation_radius=2     # Tunable: how wide is occlusion region
)
```

---

### Step 3: Modify Loss Computation

**File:** `trainer.py`

**In `compute_reprojection_loss` method, modify to:**

```python
def compute_reprojection_loss(self, pred, target, depth=None, occlusion_aware=False):
    """Computes reprojection loss with optional occlusion masking
    
    Args:
        pred: Predicted reprojected frame
        target: Target frame
        depth: Optional depth map for occlusion detection
        occlusion_aware: Whether to use occlusion masking
    """
    abs_diff = torch.abs(target - pred)
    l1_loss = abs_diff.mean(1, True)

    if self.opt.no_ssim:
        reprojection_loss = l1_loss
    else:
        ssim_loss = self.ssim(pred, target).mean(1, True)
        reprojection_loss = 0.85 * ssim_loss + 0.15 * l1_loss
    
    # NEW: Apply occlusion masking
    if occlusion_aware and depth is not None:
        occlusion_mask = self.occlusion_detector(depth)
        reprojection_loss = reprojection_loss * occlusion_mask
    
    return reprojection_loss
```

---

### Step 4: Update Loss Call Sites

**File:** `trainer.py`

**In `compute_losses` method, change:**

```python
# OLD:
for frame_id in self.opt.frame_ids[1:]:
    pred = outputs[("color", frame_id, scale)]
    reprojection_losses.append(self.compute_reprojection_loss(pred, target))

# NEW:
for frame_id in self.opt.frame_ids[1:]:
    pred = outputs[("color", frame_id, scale)]
    depth_for_occlusion = outputs[("depth", 0, scale)]  # Current depth estimate
    reprojection_losses.append(
        self.compute_reprojection_loss(
            pred, target,
            depth=depth_for_occlusion,
            occlusion_aware=True  # Enable occlusion masking
        )
    )
```

---

## PART D: Testing & Validation

### Step 1: Sanity Check

**Before training:** Verify occlusion mask looks reasonable

```python
# Add this to trainer.py for debugging:
def visualize_occlusion_mask(self, depth, frame_idx=0):
    """Debug visualization of detected occlusions"""
    depth_np = depth[0, 0].detach().cpu().numpy()
    mask_np = self.occlusion_detector(depth)[0, 0].detach().cpu().numpy()
    
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2)
    axes[0].imshow(depth_np, cmap='viridis')
    axes[0].set_title('Depth Map')
    axes[1].imshow(mask_np, cmap='gray')
    axes[1].set_title('Occlusion Mask (1=confident, 0=uncertain)')
    plt.savefig(f'occlusion_mask_frame_{frame_idx}.png')
    plt.close()

# In training loop:
if epoch % 10 == 0:  # Every 10 epochs
    self.visualize_occlusion_mask(outputs[("depth", 0, 0)], frame_idx=0)
```

**What to look for:**
- ✅ Boundaries should be marked as uncertain (0)
- ✅ Vegetation edges should have discontinuities
- ✅ Sky should be mostly confident (1)
- ❌ If entire image is 0 or 1 → adjust threshold

---

### Step 2: Train with Phase 1

**Command:**

```powershell
cd c:\Users\user\Documents\brgkuliah\sem6\ai apps\plantdepths\lite-Mono

# Fine-tune original Lite-Mono on Citrus with occlusion masking
python train.py \
  --model lite-mono \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --log_dir logs_phase1 \
  --model_name citrus_occlusion_aware \
  --num_epochs 20 \
  --batch_size 4 \
  --num_workers 4 \
  --height 320 \
  --width 1024 \
  --scales 0 1 2 3 \
  --frame_ids 0 -1 1 \
  --use_stereo
```

**Training should:**
- ✅ Run without errors
- ✅ Loss should decrease over time
- ✅ Occlusion masks should change (not static)

---

### Step 3: Evaluate Phase 1 vs Baseline

**After training:**

```python
# Run evaluation script (add to repo)
python evaluate_citrus.py \
  --weights_folder logs_phase1/citrus_occlusion_aware/models/weights_20 \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --split val  # or test

# Output:
# Baseline (M3 without occlusion): MAE = 0.40m
# Phase 1 (with occlusion):         MAE = 0.35m  ← 12.5% improvement
```

---

## PART E: Tuning Parameters

### If Occlusion Mask is Too Aggressive (Too Many 0s):

```python
# Increase threshold → fewer boundaries detected
grad_threshold = 0.7  # was 0.5
dilation_radius = 1   # was 2
```

### If Occlusion Mask is Too Conservative (Too Many 1s):

```python
# Decrease threshold → more boundaries detected
grad_threshold = 0.3  # was 0.5
dilation_radius = 3   # was 2
```

### If Results Are Worse Than Baseline:

```python
# Option A: Reduce weight of occlusion masking
occlusion_weight = 0.5  # Gradually reduce to 0 if needed

# Option B: Use Method 2 (reprojection error) instead of gradient
occlusion_aware_method = "error_based"  # vs "gradient_based"
```

---

## PART F: Key Files to Modify

| File | Changes | Lines |
|---|---|---|
| `layers.py` | Add `OcclusionDetector` class | ~40 lines |
| `trainer.py` | Init detector, modify `compute_reprojection_loss`, update call sites | ~30 lines |
| `options.py` | Add flags: `--occlusion_aware_loss`, `--occlusion_grad_threshold` | ~5 lines |

**Total code:** ~75 lines of new/modified code

---

## PART G: Expected Outcome (M4a)

**Measurement table after Phase 1:**

| Metric | M1 (Baseline) | M3 (Adapted) | M4a (+ Occlusion) | Improvement |
|---|---|---|---|---|
| Depth MAE (m) | 0.45 | 0.38 | 0.35 | -23% |
| Depth RMSE (m) | 0.65 | 0.54 | 0.49 | -25% |
| Boundary sharpness | low | medium | high | ✓ |
| Runtime (ms/frame) | 35 | 35 | 36 | ~0% |

**Qualitative:**
- Canopy depth smoother (fewer fake surfaces)
- Vegetation edges crisper
- Thin branches better preserved

---

## Next Steps After Phase 1

1. ✅ Measure M4a results
2. ✅ Visualize failure cases (where does occlusion masking help most?)
3. ✅ Document hyperparameters used
4. ⏳ Move to **Phase 2: Boundary-Aware Loss**

---

## Debugging Checklist

- [ ] Occlusion mask visualization looks reasonable
- [ ] Training loss decreases over epochs
- [ ] Validation loss also decreases (not overfitting)
- [ ] Depth predictions are within expected range (1-10m for Citrus)
- [ ] Evaluation script completes without NaN/Inf errors
- [ ] M4a metrics show improvement over M3
- [ ] Runtime increase is minimal (<5%)
