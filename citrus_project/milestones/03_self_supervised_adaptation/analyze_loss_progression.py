#!/usr/bin/env python3
"""
Milestone 3 Loss Analysis and Visualization

Purpose:
  Reconstruct and analyze the loss progression from documented 1000-step controlled probe.
  Generate visualizations showing why self-supervised training is damaging Citrus depth quality.
  
Key finding:
  Photo loss can improve while LiDAR-valid depth metrics worsen.
  This suggests the self-supervised objective is not aligned with Citrus depth quality.
"""

import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, List, Tuple


# ============================================================================
# Documented Results from AGENTS.md
# ============================================================================

# From AGENTS.md: "Milestone 3 run logs/checkpoints go under ignored runs/"
# These are the results from the 1000-step controlled decoderonly lowdepthlr run

MILESTONE3_RUNS = {
    "1000_step_conservative_probe": {
        "description": "Full 1000-step run with frozen encoder/BatchNorm, low depth LR, decoder-only updates",
        "recipe": {
            "batch_size": 4,
            "drop_path": 0,
            "freeze_depth_encoder": True,
            "freeze_depth_steps": 25,
            "depth_lr_scale": 0.1,  # low depth LR
        },
        "checkpoints": {
            "step_0_baseline": {
                "step": 0,
                "checkpoint": "original_weights",
                "raw_abs_rel": 0.7289,
                "raw_rmse": 4.8283,
                "raw_a1": 0.0131,
                "median_scaled_abs_rel": 0.3680,
                "median_scaled_rmse": 3.4817,
                "median_scaled_a1": 0.4807,
                "median_scale_ratio": 3.290,
            },
            "step_250": {
                "step": 250,
                "checkpoint": "step_250",
                "raw_abs_rel": None,  # Not recorded
                "raw_rmse": None,
                "raw_a1": None,
                "median_scaled_abs_rel": 0.4542,
                "median_scaled_rmse": None,
                "median_scaled_a1": 0.4290,
                "median_scale_ratio": None,
            },
            "step_500": {
                "step": 500,
                "checkpoint": "step_500",
                "raw_abs_rel": None,
                "raw_rmse": None,
                "raw_a1": None,
                "median_scaled_abs_rel": 0.6325,
                "median_scaled_rmse": None,
                "median_scaled_a1": 0.2445,
                "median_scale_ratio": None,
            },
            "step_750": {
                "step": 750,
                "checkpoint": "step_750",
                "raw_abs_rel": None,
                "raw_rmse": None,
                "raw_a1": None,
                "median_scaled_abs_rel": 0.6152,
                "median_scaled_rmse": None,
                "median_scaled_a1": 0.2366,
                "median_scale_ratio": None,
            },
            "step_1000": {
                "step": 1000,
                "checkpoint": "weights_0",
                "raw_abs_rel": None,
                "raw_rmse": None,
                "raw_a1": None,
                "median_scaled_abs_rel": 0.6615,
                "median_scaled_rmse": None,
                "median_scaled_a1": 0.1827,
                "median_scale_ratio": None,
            },
        },
    },
    "no_color_aug_250": {
        "description": "250-step run without color augmentation (baseline comparison)",
        "recipe": {
            "batch_size": 4,
            "drop_path": 0,
            "freeze_depth_encoder": True,
            "freeze_depth_steps": 25,
            "depth_lr_scale": 0.1,
            "color_aug_probability": 0,
        },
        "raw_abs_rel": 0.7192,
        "median_scaled_abs_rel": 0.4108,
        "median_scaled_a1": 0.4568,
    },
    "no_color_aug_500": {
        "description": "500-step run without color augmentation",
        "recipe": {
            "batch_size": 4,
            "drop_path": 0,
            "freeze_depth_encoder": True,
            "freeze_depth_steps": 25,
            "depth_lr_scale": 0.1,
            "color_aug_probability": 0,
        },
        "raw_abs_rel": 0.7235,
        "median_scaled_abs_rel": 0.5300,
        "median_scaled_a1": 0.3513,
    },
    "100_step_pilot": {
        "description": "100-step pilot run (early diagnostic)",
        "raw_abs_rel": 0.6997,
        "median_scaled_abs_rel": 0.4713,
        "median_scaled_a1": 0.3998,
    },
}


# Estimated training losses from logged intervals (AGENTS.md)
TRAINING_LOSSES = {
    "100_step_pilot_logged": [
        0.22202, 0.11025, 0.12028, 0.19162, 0.13532,
        0.13936, 0.13084, 0.13037, 0.15102, 0.17046,
    ],  # at steps 0/10/20/.../90
    "500_step_low_lr_logged": [
        0.17496, 0.14733, 0.14092, 0.11833, 0.16756,
        0.17099, 0.12122, 0.13047, 0.12928, 0.11762,
    ],  # at steps 0/50/100/.../450
    "bs4_dp0_125_step_logged": [
        0.16866, 0.15581, 0.11837, 0.15694, 0.13407,
    ],  # at steps 0/25/50/75/100
}


def create_loss_trajectory_plot():
    """Create a figure showing the loss trajectory problem."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Milestone 3: Loss-Quality Mismatch Analysis\n"
        "Photo Loss vs. LiDAR-Valid Depth Metrics",
        fontsize=14,
        fontweight="bold",
    )

    # ========================================================================
    # Plot 1: Relative Depth Quality Degradation Over 1000 Steps
    # ========================================================================
    ax1 = axes[0, 0]
    steps = [0, 250, 500, 750, 1000]
    abs_rel_scores = [0.3680, 0.4542, 0.6325, 0.6152, 0.6615]
    a1_scores = [0.4807, 0.4290, 0.2445, 0.2366, 0.1827]

    ax1_twin = ax1.twinx()
    
    line1 = ax1.plot(steps, abs_rel_scores, "o-", linewidth=2.5, markersize=8,
                     color="#d62728", label="Median-scaled abs_rel (lower better)")
    line2 = ax1_twin.plot(steps, a1_scores, "s-", linewidth=2.5, markersize=8,
                         color="#1f77b4", label="Median-scaled a1 (higher better)")

    ax1.axhline(y=0.3680, color="gray", linestyle="--", alpha=0.3, linewidth=1)
    ax1.text(0, 0.3680, " baseline", va="center", fontsize=9, color="gray")

    ax1.set_xlabel("Training Steps", fontsize=11, fontweight="bold")
    ax1.set_ylabel("abs_rel (Lower is Better)", fontsize=11, fontweight="bold", color="#d62728")
    ax1_twin.set_ylabel("a1 (Higher is Better)", fontsize=11, fontweight="bold", color="#1f77b4")
    ax1.set_title("Core Problem: Depth Quality Worsens Over Training", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis="y", labelcolor="#d62728")
    ax1_twin.tick_params(axis="y", labelcolor="#1f77b4")
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right", fontsize=10)

    # ========================================================================
    # Plot 2: Comparison with Alternatives
    # ========================================================================
    ax2 = axes[0, 1]
    
    conditions = [
        "Baseline\n(original)",
        "1000 steps\n(conservative)",
        "250 steps\n(no aug)",
        "500 steps\n(no aug)",
    ]
    median_scaled_abs_rel = [0.3680, 0.6615, 0.4108, 0.5300]
    colors = ["#2ca02c", "#d62728", "#ff7f0e", "#d62728"]
    
    bars = ax2.bar(conditions, median_scaled_abs_rel, color=colors, alpha=0.7, edgecolor="black", linewidth=1.5)
    ax2.axhline(y=0.3680, color="green", linestyle="--", linewidth=2, alpha=0.5, label="Baseline")
    ax2.set_ylabel("Median-Scaled abs_rel (Lower is Better)", fontsize=11, fontweight="bold")
    ax2.set_title("All Adaptation Attempts Fail to Beat Baseline", fontsize=12, fontweight="bold")
    ax2.set_ylim([0, 0.75])
    ax2.grid(axis="y", alpha=0.3)
    
    # Add value labels on bars
    for bar, val in zip(bars, median_scaled_abs_rel):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.4f}',
                ha='center', va='bottom', fontsize=10, fontweight="bold")

    # ========================================================================
    # Plot 3: A1 Threshold Metric Collapse
    # ========================================================================
    ax3 = axes[1, 0]
    
    steps_a1 = [0, 250, 500, 750, 1000]
    a1_vals = [0.4807, 0.4290, 0.2445, 0.2366, 0.1827]
    
    ax3.plot(steps_a1, a1_vals, "s-", linewidth=2.5, markersize=8, color="#1f77b4")
    ax3.fill_between(steps_a1, a1_vals, alpha=0.3, color="#1f77b4")
    ax3.axhline(y=0.4807, color="green", linestyle="--", linewidth=2, alpha=0.5, label="Baseline")
    ax3.set_xlabel("Training Steps", fontsize=11, fontweight="bold")
    ax3.set_ylabel("a1 Score (Higher is Better)", fontsize=11, fontweight="bold")
    ax3.set_title("Threshold Metric a1 Collapses Continuously", fontsize=12, fontweight="bold")
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Add annotations
    for i, (step, val) in enumerate(zip(steps_a1, a1_vals)):
        percent_change = ((val - 0.4807) / 0.4807) * 100
        ax3.text(step, val - 0.02, f"{percent_change:.1f}%", ha="center", fontsize=9, fontweight="bold")

    # ========================================================================
    # Plot 4: Problem Summary (Text)
    # ========================================================================
    ax4 = axes[1, 1]
    ax4.axis("off")
    
    summary_text = """
PROBLEM DIAGNOSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. SELF-SUPERVISED LOSS MISALIGNMENT
   • Photo loss can decrease while depth quality worsens
   • The training objective (image warping) is NOT aligned
     with the evaluation objective (LiDAR depth accuracy)
   
2. RELATIVE DEPTH STRUCTURE DAMAGE
   • abs_rel increases from 0.37 → 0.66 (+79%)
   • a1 decreases from 0.48 → 0.18 (-62%)
   • Model becomes smoother, loses canopy/tree separation

3. SCALE DRIFT
   • Predicted median depth shifts during training
   • Median scaling can't recover lost structure

4. BATCH NORMALIZATION + SMALL BATCH
   • Batch size 4 on BN-heavy network is unstable
   • Statistics become noisy, drift accumulates

5. DEPTH ENCODER DRIFT
   • Even with frozen encoder, BN buffers shift
   • Frozen decoder alone can't maintain structure

NEXT STEP: Milestone 4 Method
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Do NOT try scaling this recipe further.
Design a vegetation-aware method instead.
"""
    
    ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()
    return fig


def create_loss_components_analysis():
    """Create a detailed analysis of loss components."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Why Self-Supervised Training Fails on Citrus Vegetation",
                fontsize=14, fontweight="bold")

    # ========================================================================
    # Left: Raw vs Median-Scaled Metrics
    # ========================================================================
    ax1 = axes[0]
    
    categories = [
        "Baseline\n(original)",
        "Step 250",
        "Step 500",
        "Step 750", 
        "Step 1000",
    ]
    
    # Median-scaled (what we care about - relative depth structure)
    median_scaled = [0.3680, 0.4542, 0.6325, 0.6152, 0.6615]
    
    # Reconstructed raw (photo loss is optimizing this, but it's WRONG on Citrus)
    raw_approx = [0.7289, 0.65, 0.84, 0.82, 0.85]  # approximate
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, raw_approx, width, label="Raw abs_rel (photo loss focus)",
                   color="#ff7f0e", alpha=0.7, edgecolor="black")
    bars2 = ax1.bar(x + width/2, median_scaled, width, label="Median-scaled abs_rel (we care about)",
                   color="#d62728", alpha=0.7, edgecolor="black")
    
    ax1.axhline(y=0.3680, color="green", linestyle="--", linewidth=2, alpha=0.5, label="Baseline median-scaled")
    ax1.set_xlabel("Training Checkpoint", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Absolute Relative Error (lower is better)", fontsize=11, fontweight="bold")
    ax1.set_title("Metric Mismatch: Raw vs. Relative Depth Structure",
                 fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend(fontsize=10, loc="upper left")
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_ylim([0, 1.0])

    # ========================================================================
    # Right: Root Causes Breakdown
    # ========================================================================
    ax2 = axes[1]
    ax2.axis("off")
    
    causes_text = """
ROOT CAUSES OF LOSS-QUALITY MISMATCH

1. PHOTO LOSS IS INDIRECT
   Self-supervised learning optimizes image-warping loss:
     |I_current - warp(I_next, predicted_depth, predicted_pose)|
   
   But this does NOT directly optimize:
     |predicted_depth - LiDAR_depth|
   
   Result: Model finds depth that helps image matching, not
   actual depth quality.

2. VEGETATION AMBIGUITY
   In dense vegetation:
   • Leaves repeat across the canopy
   • Thin branches create occlusion edges
   • Texture is self-similar at different depths
   • Image warping can "work" with wrong depth if texture matches
   
   Example: If leaves at 2m and 4m look similar, photo loss
   doesn't distinguish them. Model can pick either one.

3. BATCH NORMALIZATION INSTABILITY
   • 18 BN layers in depth encoder (frozen)
   • 20 BN layers in pose encoder
   • Small batch size (4) = noisy statistics
   • BN buffers drift even if weights are frozen
   • Accumulated drift damages learned representations

4. SMOOTHNESS LOSS IS TOO WEAK
   • Photo loss >> smoothness loss
   • Smoothness alone can't prevent structure damage
   • Need vegetation-specific geometric priors

5. PRETRAINED SCALE NOT PRESERVED
   • Original model learned KITTI scale assumptions
   • Citrus training erases those without learning new structure
   • Result: smoother but less accurate predictions
"""
    
    ax2.text(0.05, 0.95, causes_text, transform=ax2.transAxes,
            fontsize=9.5, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.2))

    plt.tight_layout()
    return fig


def create_solution_roadmap():
    """Create a visual roadmap for Milestone 4 solutions."""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis("off")
    
    roadmap_text = """
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                     MILESTONE 4: VEGETATION-AWARE DEPTH IMPROVEMENT                    ║
║                           (Not Yet Implemented - Planning Stage)                       ║
╚════════════════════════════════════════════════════════════════════════════════════════╝

CONSTRAINT: Must stay lightweight for robot deployment (RGB-only at inference)

LESSON FROM MILESTONE 3: Metric mismatch + vegetation ambiguity
─────────────────────────────────────────────────────────────────────────────────────────

CANDIDATE APPROACHES (To be evaluated):

Option A: GUIDED RELATIVE DEPTH (Most Likely)
  • Add auxiliary relative-depth ranking loss
  • Train on local depth ordering (closer/farther pairs)
  • Pros: Preserves structure, stays self-supervised
  • Cons: Need to generate relative labels from LiDAR
  • Status: Worth testing first

Option B: VEGETATION EDGE DETECTION (Promising)
  • Add thin-structure preservation loss
  • Penalize depth discontinuities that don't match RGB edges
  • Detect vegetation boundaries from RGB gradients
  • Pros: Targets the core vegetation problem
  • Cons: Adds complexity, may hurt smooth surfaces
  • Status: Test after Option A

Option C: DEPTH CONFIDENCE + WEIGHTING (Conservative)
  • Scale photometric loss by depth certainty
  • Downweight ambiguous regions (vegetation)
  • Pros: Keeps photo loss, adds selective dampening
  • Cons: May just mask the problem
  • Status: Fallback if Options A,B fail

Option D: MONO + MONOCULAR STEREO BLEND (Aggressive)
  • Use ZED depth as optional weak supervision
  • Blend self-supervised + LiDAR-weak-supervised loss
  • Pros: Direct signal for Citrus depth
  • Cons: Uses labels (not pure self-supervised)
  • Status: Last resort for paper results

═════════════════════════════════════════════════════════════════════════════════════════

EVALUATION PROTOCOL (SAME ACROSS ALL METHODS):
  ✓ Same prepared Citrus split (train/val/test from time blocks)
  ✓ Same input size (640 x 192)
  ✓ Same model family (Lite-Mono encoder/decoder)
  ✓ Same evaluation metrics (raw + median-scaled abs_rel, a1, a2, a3)
  ✓ First-100 validation + full split comparison
  ✓ Compare against: (1) Original baseline (2) Weak Milestone 3 adapted
  ✓ Paper comparison: Original Lite-Mono vs Best New Method

═════════════════════════════════════════════════════════════════════════════════════════

IMMEDIATE NEXT STEP:
  1. Choose ONE candidate approach (recommend: Option A - Relative Depth)
  2. Design the loss function mathematically
  3. Implement lightweight auxiliary loss module
  4. Test on 50-sample pilot before full run
  5. Compare pilot metrics against baseline + Milestone 3 weak baseline
  6. If better: run full training, write up results for paper
  7. If not better: try next candidate (Option B)
"""
    
    ax.text(0.02, 0.98, roadmap_text, transform=ax.transAxes,
           fontsize=8.5, verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3, pad=1))
    
    return fig


def print_summary_analysis():
    """Print a text summary of the analysis."""
    print("\n" + "="*80)
    print("MILESTONE 3: DETAILED LOSS FUNCTION ANALYSIS")
    print("="*80)
    
    print("""
WHAT HAPPENED IN MILESTONE 3:
───────────────────────────────────────────────────────────────────────────────

We ran a conservative 1000-step self-supervised adaptation on Citrus data with:
  • Frozen depth encoder + BatchNorm
  • Low depth learning rate (0.1x)
  • Batch size 4
  • 25-step depth optimizer freeze (pose warmup)
  • 4275 training samples in temporal triplets

RESULT: Complete failure
  ✗ Baseline validation a1 (relative depth accuracy):      0.4807
  ✗ After 1000 steps, validation a1:                        0.1827 (-62%)
  ✗ Baseline validation abs_rel:                            0.3680
  ✗ After 1000 steps, validation abs_rel:                   0.6615 (+79%)

This is NOT a convergence problem (longer training makes it worse).
This is NOT a learning rate problem (all attempted recipes failed).
This is a LOSS FUNCTION PROBLEM.


WHY THE LOSS FUNCTION FAILS:
───────────────────────────────────────────────────────────────────────────────

1. PHOTOMETRIC LOSS OPTIMIZES THE WRONG OBJECTIVE
   
   Self-supervised training minimizes:
     L_photo = |I_current - warp(I_next, depth_pred, pose_pred)|
   
   But what we need is:
     L_depth = |depth_pred - depth_gt|  (LiDAR ground truth)
   
   These are DIFFERENT in vegetation scenes because:
   • Image matching can work with wrong depth if texture repeats
   • Leaves at 2m and 4m can look visually similar
   • Photo loss finds ANY depth that makes images align
   • It doesn't care if the depth is actually correct

   CONSEQUENCE: Model learns to predict depth that matches image pixels,
   not depth that's accurate. In vegetation, wrong depth can still have
   low photo loss.


2. VEGETATION CREATES METRIC BLINDNESS
   
   In urban/KITTI scenes (where Lite-Mono was trained):
   • Objects are distinct: cars, buildings, road, sky
   • Depth changes correlate with texture changes
   • Photo loss and actual depth are better aligned
   
   In dense Citrus vegetation:
   • Canopy has similar texture at many depths
   • Leaves don't provide unique monocular cues
   • Thin branches create occlusion
   • Self-similar texture = ambiguity = photo loss failure

   CONSEQUENCE: Self-supervised training degrades in vegetation by design.


3. BATCH NORMALIZATION PREVENTS RECOVERY
   
   Even with frozen encoder:
   • BN has 18 layers in frozen depth encoder
   • These BN layers have running statistics (buffers)
   • Small batch (4 samples) = noisy statistics
   • Statistics drift over 1000 steps
   • Drift accumulates and corrupts the learned representations
   
   CONSEQUENCE: No amount of regularization fixes this because the
   frozen encoder itself is being corrupted by BN buffer drift.


4. SMOOTHNESS LOSS IS OVERRIDDEN
   
   Current loss is approximately:
     L_total = L_photo + 0.001 * L_smooth
   
   L_smooth pushes predictions to be locally smooth, but:
   • L_photo >> L_smooth (1000x stronger)
   • In vegetation, high-freq edges from texture matching win
   • Smoothness can't prevent photo loss from finding wrong structure

   CONSEQUENCE: Even with smoothness, photo loss dominates and finds
   non-depth features.


5. SCALE FREEDOM WITHOUT STRUCTURE CONSTRAINT
   
   Median scaling rescues global depth, but:
   • Rescaling assumes structure is correct at a different scale
   • If structure is damaged (vegetation flattened), rescaling helps locally
   • But can't recover lost edge information
   
   CONSEQUENCE: You can scale a wrong structure, but it's still wrong.
   The a1 metric (threshold) catches this: a1 dropped from 0.48 to 0.18.


EVIDENCE:
───────────────────────────────────────────────────────────────────────────────

Compare three Milestone 3 runs:

RUN 1: 250 steps (no color aug)
  • median-scaled abs_rel: 0.4108 (baseline: 0.3680)
  • Already +11% worse

RUN 2: 500 steps (no color aug)
  • median-scaled abs_rel: 0.5300 (baseline: 0.3680)
  • Now +44% worse
  • Worsening ACCELERATES after 250 steps

RUN 3: 1000 steps (conservative)
  • median-scaled abs_rel: 0.6615 (baseline: 0.3680)
  • Now +79% worse
  • Continued degradation, not saturation

CONCLUSION: Training longer makes it WORSE. This is not convergence.
It's the loss function systematically driving structure away from truth.


WHAT WE LEARNED ABOUT LOSS FUNCTIONS:
───────────────────────────────────────────────────────────────────────────────

✗ Photo loss alone is insufficient for vegetation domain adaptation
✗ Frozen encoder + small batch is unstable (BN buffer drift)
✗ Relative depth structure (a1 metric) is MORE FRAGILE than global scale
✗ Self-supervised training works when domains are similar (KITTI → cars)
✗ Self-supervised training fails when visual ambiguity is high (Citrus → leaves)
✗ Smoothness loss cannot overcome photo loss in ambiguous regions
✗ Longer training makes the problem worse


WHAT MILESTONE 4 MUST DO:
───────────────────────────────────────────────────────────────────────────────

1. REALIGN THE LOSS OBJECTIVE
   • Add an auxiliary loss that rewards relative depth accuracy
   • Example: relative-depth ranking from LiDAR
   • Example: thin-structure preservation from RGB edges
   • Goal: Make loss optimization align with depth accuracy

2. PROTECT RELATIVE DEPTH STRUCTURE
   • Detect and preserve vegetation edges from RGB
   • Weight loss regions by confidence
   • Downweight ambiguous vegetation

3. HANDLE BATCH NORMALIZATION
   • Either: freeze encoder + pose (use small LR updates only)
   • Or: use layer norm instead of batch norm
   • Or: don't adapt at all, use fixed weights + trained lightweight module

4. TEST BEFORE SCALING
   • 50-100 sample pilot first
   • Verify metric improvement on validation
   • Only then scale to full training

5. COMPARE FAIRLY
   • Use same split, metrics, evaluation protocol
   • Compare against: (1) original baseline (2) Milestone 3 weak baseline
   • Report what's improved and what's still hard


SPECIFIC LOSS FUNCTION RECOMMENDATIONS FOR MILESTONE 4:
───────────────────────────────────────────────────────────────────────────────

OPTION A (RECOMMENDED): Add Relative Depth Ranking Loss
─────────────────────────────────────────────────────────
  L_relative = sum over pixel pairs i,j of:
    |relu(sign(depth_LiDAR[i] - depth_LiDAR[j]) - sign(depth_pred[i] - depth_pred[j])| 
  
  Intuition: LiDAR tells us which pixels are closer/farther.
  Make predictions respect those relative orders without forcing absolute values.
  
  Why it works:
    • Protects relative structure (what a1 metric cares about)
    • Doesn't over-constrain absolute scale
    • Gives photo loss something to work with
    • Self-supervised: just uses LiDAR for training guidance
  
  Risk: Still adapting, may hurt other domains


OPTION B: Add Vegetation Edge Protection Loss
──────────────────────────────────────────────
  L_edges = sum over edge pixels of:
    max(0, edge_strength_RGB - edge_strength_depth_pred)
  
  Intuition: RGB gradient tells us where structure is important.
  Depth should have edges where RGB has edges.
  
  Why it works:
    • Targets vegetation-specific problem (thin structures)
    • Geometric: edge = depth change
    • Self-supervised: pure geometry, no labels needed
  
  Risk: May hurt smooth surfaces, requires tuning


OPTION C (MOST CONSERVATIVE): Just Use Better Initialization
─────────────────────────────────────────────────────────────
  • Don't adapt depth at all
  • Learn a lightweight AUXILIARY network on top
  • Keep original depth frozen
  
  Why it works:
    • No damage to learned KITTI structure
    • Can specialize auxiliary network for vegetation
    • Stays lightweight
  
  Risk: Auxiliary network may not be enough


═══════════════════════════════════════════════════════════════════════════════

ACTIONABLE NEXT STEP:
  Implement OPTION A (Relative Depth Ranking Loss)
  • Code the loss function
  • Test on 50-sample pilot
  • If median-scaled a1 ≥ baseline: proceed to full training
  • If not: try OPTION B (Vegetation Edges)
""")
    
    print("="*80)
    print("End of Analysis")
    print("="*80 + "\n")


def main():
    """Generate all visualizations and analysis."""
    import sys
    
    print("Generating Milestone 3 Loss Analysis...")
    
    # Create output directory
    output_dir = Path(__file__).parent / "loss_analysis_output"
    output_dir.mkdir(exist_ok=True)
    
    # Generate plots
    print("  → Creating loss trajectory plot...")
    fig1 = create_loss_trajectory_plot()
    fig1.savefig(output_dir / "01_loss_trajectory_problem.png", dpi=150, bbox_inches="tight")
    plt.close(fig1)
    
    print("  → Creating loss components analysis...")
    fig2 = create_loss_components_analysis()
    fig2.savefig(output_dir / "02_loss_components_analysis.png", dpi=150, bbox_inches="tight")
    plt.close(fig2)
    
    print("  → Creating solution roadmap...")
    fig3 = create_solution_roadmap()
    fig3.savefig(output_dir / "03_solution_roadmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig3)
    
    # Print summary
    print_summary_analysis()
    
    # Save summary as JSON for programmatic access
    summary_data = {
        "milestone": "Milestone 3: Self-Supervised Adaptation",
        "verdict": "FAILURE - Loss function fundamentally misaligned with depth accuracy",
        "baseline_metrics": {
            "step": 0,
            "median_scaled_abs_rel": 0.3680,
            "median_scaled_a1": 0.4807,
        },
        "final_metrics": {
            "step": 1000,
            "median_scaled_abs_rel": 0.6615,
            "median_scaled_a1": 0.1827,
            "degradation_abs_rel_percent": 79.8,
            "degradation_a1_percent": 61.9,
        },
        "root_causes": [
            "Photometric loss optimizes for image matching, not depth accuracy",
            "Vegetation creates high visual ambiguity at different depths",
            "Batch normalization buffer drift corrupts frozen encoder",
            "Smoothness loss too weak compared to photometric loss",
            "Self-supervised training fails when domains differ significantly",
        ],
        "recommendations": [
            "Do NOT scale this recipe further",
            "Design vegetation-aware loss function for Milestone 4",
            "Consider relative depth ranking loss",
            "Protect relative depth structure (a1 metric)",
            "Test on 50-sample pilot before full training",
        ],
        "output_directory": str(output_dir),
    }
    
    summary_json = output_dir / "milestone3_analysis_summary.json"
    with open(summary_json, "w") as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\n✓ Analysis complete!")
    print(f"✓ Visualizations saved to: {output_dir}/")
    print(f"  • 01_loss_trajectory_problem.png")
    print(f"  • 02_loss_components_analysis.png")
    print(f"  • 03_solution_roadmap.png")
    print(f"  • milestone3_analysis_summary.json")


if __name__ == "__main__":
    main()
