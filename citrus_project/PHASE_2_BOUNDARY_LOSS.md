# Phase 2: Boundary-Aware Loss Implementation Roadmap

**Objective:** Add boundary-aware loss term to sharpen depth at RGB edges  
**Timeline:** 10-16 hours total  
**Complexity:** Medium (adds one new loss term)  
**Risk:** Low (additive, can be toggled via weight parameter)

---

## PART A: Understanding Boundary Loss

### What is Boundary Loss?

**Standard photometric loss:** Makes reprojected images match, but doesn't penalize blurry edges

**Boundary loss:** Explicitly encourages depth edges to align with RGB edges

```
Photometric loss alone:
│ Leaf (3.0) ──────┐
│ Leaf (2.9)       │  Soft transition (0-9 pixels)
│ Leaf (2.5)       │
│ Sky  (2.1) ──────┘
│ Sky  (1.0)
                    ❌ Blurry edge

With boundary loss added:
│ Leaf (3.0)───┐
│ Leaf (3.0)   │  Sharp transition (1-2 pixels)
│ Leaf (3.0)───┘
│ Sky  (10.0)
│ Sky  (10.0)
                ✓ Sharp edge
```

### Why Align Depth Gradients with Image Gradients?

**Intuition:** If the RGB image has a sharp edge, there's probably a real depth discontinuity there

```
RGB Image (what we see):
[Green leaves] | [Blue sky]  ← Sharp color boundary
                ↑ Indicates depth boundary

If depth is:
[3.0, 2.9, 2.8 | 10.0, 9.9, 9.8]  ← Gradual transition
           ↑ Mismatch! Should be sharp here

Boundary loss penalty: "Align your depth gradients with the RGB edge!"
```

---

## PART B: Two Approaches Explained

### Approach 1: Direct Gradient Matching (BoRe-Depth Style)

**Formula:**
```
L_boundary = mean( |∇_depth - ∇_img| )
```

**Interpretation:** Penalize any mismatch between depth and image gradients

**Code:**
```python
def boundary_loss_direct(depth, img):
    """Direct gradient matching"""
    # Compute gradients in X direction
    grad_depth_x = torch.abs(depth[:, :, :-1, :] - depth[:, :, 1:, :])
    grad_img_x = torch.abs(img[:, :, :-1, :] - img[:, :, 1:, :])
    
    # L1 distance between gradients
    loss_x = torch.abs(grad_depth_x - grad_img_x)
    
    # Same for Y direction
    grad_depth_y = torch.abs(depth[:, :, :, :-1] - depth[:, :, :, 1:])
    grad_img_y = torch.abs(img[:, :, :, :-1] - img[:, :, :, 1:])
    loss_y = torch.abs(grad_depth_y - grad_img_y)
    
    # Average
    loss = (loss_x.mean() + loss_y.mean()) / 2
    return loss
```

**Pros:**
- ✅ Simple, straightforward
- ✅ Direct correlation between depth/RGB edges
- ✅ Fewer parameters to tune

**Cons:**
- ❌ May be too strict in uniform regions
- ❌ Can create artifacts if RGB has noise/texture

---

### Approach 2: Selective Edge Sharpening (Sharper Boundaries Style)

**Formula:**
```
L_boundary = mean( (|∇_img| > threshold) * smoothness(depth) )
             ↑ Only penalize depth smoothness at RGB edges
```

**Interpretation:** "Be smooth everywhere, BUT be sharp at RGB edges"

**Code:**
```python
def boundary_loss_selective(depth, img, threshold=0.05):
    """Selective edge sharpening"""
    # Compute image gradients
    grad_img_x = torch.abs(img[:, :, :-1, :] - img[:, :, 1:, :])
    grad_img_y = torch.abs(img[:, :, :, :-1] - img[:, :, :, 1:])
    
    # Find where image has edges
    edge_mask_x = (grad_img_x > threshold).float()
    edge_mask_y = (grad_img_y > threshold).float()
    
    # Compute depth gradients
    grad_depth_x = torch.abs(depth[:, :, :-1, :] - depth[:, :, 1:, :])
    grad_depth_y = torch.abs(depth[:, :, :, :-1] - depth[:, :, :, 1:])
    
    # Penalize SMALL depth gradients at image edges
    # Invert: want LARGE depth gradients at edges
    loss_x = edge_mask_x * (1.0 - torch.exp(-grad_depth_x))
    loss_y = edge_mask_y * (1.0 - torch.exp(-grad_depth_y))
    
    loss = -(loss_x.mean() + loss_y.mean()) / 2  # Negative = maximize gradient
    return loss
```

**Pros:**
- ✅ More flexible (only constrains at edges)
- ✅ Allows smoothness in uniform regions
- ✅ More robust to texture/noise

**Cons:**
- ❌ More parameters (threshold, weighting)
- ❌ More complex logic

---

## RECOMMENDATION: Approach 1 (Direct Gradient Matching)

**Why:**
- Simpler to implement and debug
- Works well empirically for vegetation
- Fewer parameters to tune
- BoRe-Depth paper shows good results with this approach

---

## PART C: Implementation Steps

### Step 1: Create Boundary Loss Function

**File:** `layers.py`

**Add this class/function:**

```python
class BoundaryLoss:
    """Encourage sharp edges in depth at RGB boundaries"""
    
    def __init__(self, normalize=True):
        """
        Args:
            normalize: Whether to normalize gradients before comparison
        """
        self.normalize = normalize
    
    def __call__(self, depth, img, reduction='mean'):
        """
        Args:
            depth: [B, 1, H, W] predicted depth
            img: [B, 3, H, W] (or [B, 1, H, W]) input RGB image
            reduction: 'mean', 'sum', or None
        
        Returns:
            boundary loss scalar
        """
        # Ensure img is single channel for gradient computation
        if img.shape[1] == 3:
            # Convert RGB to grayscale for edge detection
            img = 0.299 * img[:, 0:1, :, :] + 0.587 * img[:, 1:2, :, :] + 0.114 * img[:, 2:3, :, :]
        
        # Compute gradients in X direction
        grad_depth_x = torch.abs(depth[:, :, :-1, :] - depth[:, :, 1:, :])
        grad_img_x = torch.abs(img[:, :, :-1, :] - img[:, :, 1:, :])
        
        # Compute gradients in Y direction
        grad_depth_y = torch.abs(depth[:, :, :, :-1] - depth[:, :, :, 1:])
        grad_img_y = torch.abs(img[:, :, :, :-1] - img[:, :, :, 1:])
        
        # Pad to original size
        grad_depth_x = torch.nn.functional.pad(grad_depth_x, (0, 1, 0, 0))
        grad_img_x = torch.nn.functional.pad(grad_img_x, (0, 1, 0, 0))
        grad_depth_y = torch.nn.functional.pad(grad_depth_y, (0, 0, 0, 1))
        grad_img_y = torch.nn.functional.pad(grad_img_y, (0, 0, 0, 1))
        
        # Normalize if requested
        if self.normalize:
            grad_depth_x = (grad_depth_x + 1e-8) / (torch.max(grad_depth_x) + 1e-8)
            grad_depth_y = (grad_depth_y + 1e-8) / (torch.max(grad_depth_y) + 1e-8)
            grad_img_x = (grad_img_x + 1e-8) / (torch.max(grad_img_x) + 1e-8)
            grad_img_y = (grad_img_y + 1e-8) / (torch.max(grad_img_y) + 1e-8)
        
        # L1 distance between depth and image gradients
        loss_x = torch.abs(grad_depth_x - grad_img_x)
        loss_y = torch.abs(grad_depth_y - grad_img_y)
        
        loss = loss_x + loss_y
        
        if reduction == 'mean':
            loss = loss.mean()
        elif reduction == 'sum':
            loss = loss.sum()
        
        return loss
```

---

### Step 2: Add to Trainer Init

**File:** `trainer.py`

**In `__init__` method, add:**

```python
from layers import BoundaryLoss

# In __init__:
self.boundary_loss = BoundaryLoss(normalize=True)
self.boundary_loss_weight = 0.2  # Tunable: typically 0.1-0.5
```

---

### Step 3: Integrate into Training Loss

**File:** `trainer.py`

**In `compute_losses` method, after computing photometric + smoothness loss:**

```python
# Existing code (around line 520):
loss += self.opt.disparity_smoothness * smooth_loss / (2 ** scale)
total_loss += loss
losses["loss/{}".format(scale)] = loss

# NEW: Add boundary loss
boundary_loss = self.boundary_loss(
    outputs[("depth", 0, scale)],
    inputs[("color", 0, scale)]
)
boundary_weighted = self.boundary_loss_weight * boundary_loss
loss += boundary_weighted
total_loss += boundary_weighted
losses["boundary_loss/{}".format(scale)] = boundary_loss
```

**Full updated loss computation:**

```python
def compute_losses(self, inputs, outputs):
    """Compute the reprojection, smoothness, and BOUNDARY losses for a minibatch"""
    
    losses = {}
    total_loss = 0

    for scale in self.opt.scales:
        loss = 0
        reprojection_losses = []

        # ... [existing photometric loss code] ...
        
        loss += to_optimise.mean()

        # Smoothness loss (existing)
        mean_disp = disp.mean(2, True).mean(3, True)
        norm_disp = disp / (mean_disp + 1e-7)
        smooth_loss = get_smooth_loss(norm_disp, color)
        loss += self.opt.disparity_smoothness * smooth_loss / (2 ** scale)
        
        # NEW: Boundary loss (sharp edges)
        boundary_loss = self.boundary_loss(
            outputs[("depth", 0, scale)],
            inputs[("color", 0, scale)]
        )
        boundary_weighted = self.boundary_loss_weight * boundary_loss
        loss += boundary_weighted
        
        # Logging
        losses["loss/{}".format(scale)] = loss
        losses["boundary_loss/{}".format(scale)] = boundary_loss
        total_loss += loss

    total_loss /= self.num_scales
    losses["loss"] = total_loss
    return losses
```

---

### Step 4: Add Command-Line Options (Optional)

**File:** `options.py`

**Add these flags:**

```python
# In the parser setup:
parser.add_argument("--boundary_loss_weight",
                    type=float,
                    default=0.2,
                    help="Weight of boundary loss in total loss")

parser.add_argument("--boundary_normalize",
                    action="store_true",
                    default=True,
                    help="Normalize gradients before comparison")
```

---

## PART D: Testing & Validation

### Step 1: Verify Boundary Loss Shape

**Before full training, test with dummy data:**

```python
# Add to trainer.py for debugging:
def test_boundary_loss(self):
    """Test boundary loss computation"""
    # Create dummy tensors
    batch_size = 2
    dummy_depth = torch.randn(batch_size, 1, 128, 256).cuda()
    dummy_img = torch.randn(batch_size, 3, 128, 256).cuda()
    
    # Compute loss
    loss = self.boundary_loss(dummy_depth, dummy_img)
    
    print(f"Boundary loss shape: {loss.shape}")
    print(f"Boundary loss value: {loss.item():.4f}")
    
    # Should be scalar value, not NaN/Inf
    assert not torch.isnan(loss), "Loss is NaN!"
    assert not torch.isinf(loss), "Loss is Inf!"
    assert loss.dim() == 0, "Loss should be scalar!"
    
    print("✓ Boundary loss test passed")

# Call in __init__:
self.test_boundary_loss()
```

---

### Step 2: Smoke Test Training

**Before full training (5 steps on minimal data):**

```powershell
python train.py \
  --model lite-mono \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --log_dir logs_debug_phase2 \
  --num_epochs 1 \
  --num_steps 5 \
  --batch_size 1 \
  --boundary_loss_weight 0.2
```

**Checks:**
- ✅ No crashes (shape/type errors)
- ✅ Loss values printed (not NaN/Inf)
- ✅ Loss decreases over 5 steps
- ✅ Boundary loss component visible in logs

---

### Step 3: Full Training (Phase 2)

**Command:**

```powershell
cd c:\Users\user\Documents\brgkuliah\sem6\ai apps\plantdepths\lite-Mono

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
  --scales 0 1 2 3 \
  --frame_ids 0 -1 1 \
  --use_stereo \
  --boundary_loss_weight 0.2
```

**Training should:**
- ✅ Run for 20 epochs without crashes
- ✅ Total loss decreases
- ✅ Boundary loss component contributes meaningfully (~5-10% of total)
- ✅ Checkpoint saved at end

---

## PART E: Hyperparameter Tuning

### Boundary Loss Weight

**Effect:** How much to emphasize edge sharpness

| Weight | Effect | Range |
|---|---|---|
| 0.0 | No boundary loss (Phase 1 + smoothness only) | 0 |
| 0.1 | Mild edge sharpening | Light |
| 0.2 | Moderate edge sharpening (RECOMMENDED) | Standard |
| 0.5 | Strong edge sharpening | Heavy |
| 1.0+ | Very aggressive (may cause artifacts) | Too much |

**How to tune:**
- Start with 0.2 (recommended)
- If edges look artificial/crispy: **reduce to 0.1**
- If edges still blurry: **increase to 0.3-0.5**

---

### Gradient Normalization

**Effect:** Whether to normalize gradients before comparing

| Setting | Pros | Cons |
|---|---|---|
| `normalize=True` (default) | Fair comparison, scale-invariant | May lose information |
| `normalize=False` | Preserves scale | Sensitive to depth range |

**Recommendation:** Keep `normalize=True` for vegetation (depth range varies)

---

## PART F: Monitoring Training

### Key Metrics to Watch

```
Epoch 1:   loss = 0.245  ├─ photometric: 0.120
                         ├─ smoothness: 0.100
                         └─ boundary: 0.025

Epoch 5:   loss = 0.185  ├─ photometric: 0.095
                         ├─ smoothness: 0.070
                         └─ boundary: 0.020  ← Should also decrease

Epoch 20:  loss = 0.165  ├─ photometric: 0.085
                         ├─ smoothness: 0.060
                         └─ boundary: 0.020  ← Stabilized
```

**Green flags:**
- ✅ All loss components decreasing
- ✅ Boundary loss ~5-15% of total loss
- ✅ No NaN/Inf values

**Red flags:**
- ❌ Boundary loss increasing or not decreasing
- ❌ Total loss plateaus before epoch 20
- ❌ Loss oscillates wildly

---

## PART G: Evaluation (M4b Results)

### Prepare Evaluation

```python
# evaluate_citrus.py or adapt evaluate_depth.py

def evaluate_phase2(model_path, data_path, split='val'):
    # Load M4a checkpoint (Phase 1 results)
    m4a_results = evaluate(model_path.replace('phase2', 'phase1'), data_path, split)
    
    # Load M4b checkpoint (Phase 2 results)
    m4b_results = evaluate(model_path, data_path, split)
    
    # Compare
    improvement = (m4a_results['mae'] - m4b_results['mae']) / m4a_results['mae'] * 100
    
    print(f"M4a MAE: {m4a_results['mae']:.4f}")
    print(f"M4b MAE: {m4b_results['mae']:.4f}")
    print(f"Improvement: {improvement:.1f}%")
    
    return m4b_results
```

### Run Evaluation

```powershell
python evaluate_citrus.py \
  --weights_folder logs_phase2/citrus_boundary_aware/models/weights_20 \
  --data_path citrus_project/dataset_workspace/prepared_training_dataset/ \
  --split val
```

**Expected output:**

```
M4a (Occlusion only):    MAE = 0.330m
M4b (+ Boundary loss):   MAE = 0.303m
Improvement:             -8.2% ✓

Edge Sharpness Score:    0.78 (higher is better)
```

---

## PART H: Visualizations

### Generate Boundary Comparisons

**Create visualization script:**

```python
def visualize_boundary_improvement(rgb, depth_m4a, depth_m4b, gt_depth):
    """Side-by-side comparison"""
    import matplotlib.pyplot as plt
    from matplotlib import cm
    
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    
    # Input RGB
    axes[0].imshow(rgb)
    axes[0].set_title('Input RGB')
    
    # M4a depth (Phase 1 only)
    im1 = axes[1].imshow(depth_m4a, cmap='viridis')
    axes[1].set_title('M4a: Occlusion Masking')
    plt.colorbar(im1, ax=axes[1])
    
    # M4b depth (Phase 1 + Boundary)
    im2 = axes[2].imshow(depth_m4b, cmap='viridis')
    axes[2].set_title('M4b: + Boundary Loss')
    plt.colorbar(im2, ax=axes[2])
    
    # Ground truth
    im3 = axes[3].imshow(gt_depth, cmap='viridis')
    axes[3].set_title('Ground Truth (LiDAR)')
    plt.colorbar(im3, ax=axes[3])
    
    plt.tight_layout()
    plt.savefig('phase2_comparison.png', dpi=150)
    plt.close()
```

---

## PART I: Troubleshooting

### Problem: Boundary Loss is Very High (> 1.0)

**Causes:**
- Gradients not normalized
- Depth range very different from image range
- Large depth discontinuities

**Solutions:**
1. Ensure `normalize=True` in BoundaryLoss init
2. Check gradient values: `print(grad_depth_x.mean())`
3. Reduce `boundary_loss_weight` to 0.05-0.1

---

### Problem: M4b Worse than M4a

**Causes:**
- Boundary loss too strong (weight too high)
- Artificial sharpness destroying smooth geometry
- Misalignment between RGB edges and actual depth boundaries

**Solutions:**
1. **Reduce weight:** `--boundary_loss_weight 0.1` (from 0.2)
2. **Check gradient alignment:** visualize depth/RGB gradients
3. **Increase training epochs:** Phase 2 may need more time to converge
4. **Disable if needed:** `--boundary_loss_weight 0.0` (fallback to Phase 1)

---

### Problem: Training Very Slow

**Causes:**
- Boundary loss computation is expensive
- GPU memory issues

**Solutions:**
1. Reduce batch size: `--batch_size 2`
2. Check GPU memory: `nvidia-smi`
3. Profile: where is time spent (data vs model vs loss)?

---

## PART J: File Summary

| File | Changes | Lines |
|---|---|---|
| `layers.py` | Add `BoundaryLoss` class | ~50 |
| `trainer.py` | Init + integrate in `compute_losses` | ~20 |
| `options.py` | Add CLI flags (optional) | ~10 |
| **Total** | | **~80** |

---

## Expected Results

### Metrics (M4b vs M4a)

| Metric | M4a | M4b | Improvement |
|---|---|---|---|
| **Depth MAE** | 0.330m | 0.303m | -8.2% |
| **Depth RMSE** | 0.47m | 0.42m | -10.6% |
| **Edge Sharpness** | 0.68 | 0.78 | +14.7% |
| **Runtime** | 36ms | 37ms | +0.3% |

### Qualitative

**Canopy depth:**
- M4a: Smooth but soft boundaries
- M4b: Smooth AND sharp boundaries ✓

**Leaf edges:**
- M4a: Gradual transitions
- M4b: Crisp boundaries ✓

**Fruit detection:**
- M4a: Hard to localize precisely
- M4b: Clear depth separation ✓

---

## Next Steps After Phase 2

1. ✅ Document M4b results
2. ✅ Compare M1 → M3 → M4a → M4b progression
3. ⏳ (Optional) Phase 3: Architecture comparison (RTS-Mono vs M4b)
4. ⏳ Paper writing: Results table + qualitative examples

---

## Success Checklist

- [ ] BoundaryLoss class added to layers.py
- [ ] Integrated into trainer.py compute_losses
- [ ] Smoke test passes (5 training steps)
- [ ] Full training completes 20 epochs
- [ ] M4b validation MAE < M4a validation MAE
- [ ] Boundary loss component non-zero and decreasing
- [ ] Edge visualizations show improvement
- [ ] Results documented
- [ ] Ready for next phase
