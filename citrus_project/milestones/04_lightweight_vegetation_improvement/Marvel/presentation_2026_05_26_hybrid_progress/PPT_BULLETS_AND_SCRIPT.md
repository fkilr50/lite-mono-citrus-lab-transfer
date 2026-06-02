# Progress Presentation: Hybrid Supervised Lite-Mono and Next LiDAR-Aware Edge Loss

Date prepared: 2026-05-25

Purpose: show the current Milestone 4 progress: the hybrid supervised result, why `weights_13` is now our selected checkpoint, and the next planned improvement using LiDAR-aware edge loss.

## Suggested Presentation Length

Target: 6-8 minutes.

Main message:

> Plain Citrus training still struggles with absolute depth and vegetation structure. Adding masked LiDAR supervision gives a major quantitative improvement while keeping inference RGB-only. The best checkpoint was mid-run (`weights_13`), so our next step is not blindly longer training, but a more targeted LiDAR-aware edge loss with checkpoint-based selection.

## Asset Folder

Use images from:

```text
assets/
```

Key generated assets:

```text
graph_metric_summary_table.png
graph_absrel_plain_vs_hybrid_w13.png
graph_a1_plain_vs_hybrid_w13.png
graph_median_scaled_plain_vs_hybrid_w13.png
graph_checkpoint_sweep_val_w13_vs_w29.png
graph_top3_test_confirmation.png
visual_plain_medianscaled_vs_weights13_test_bad.png
visual_plain_medianscaled_vs_weights13_test_typical.png
visual_plain_medianscaled_vs_weights13_test_good.png
visual_plain_medianscaled_vs_weights13_val_bad.png
visual_plain_medianscaled_vs_weights13_val_typical.png
visual_plain_medianscaled_vs_weights13_val_good.png
visual_w29_vs_w13_test_bad.png
visual_w29_vs_w13_test_typical.png
visual_w29_vs_w13_test_good.png
visual_w29_vs_w13_val_bad.png
visual_w29_vs_w13_val_typical.png
visual_w29_vs_w13_val_good.png
```

---

# Slide 1: Title

## Slide Bullets

- Improving Lite-Mono for Citrus Farm depth estimation
- Current result: hybrid supervised training with LiDAR depth labels
- Next plan: LiDAR-aware edge loss for stronger boundary learning

## Speaker Script

Today I will show our current progress on improving Lite-Mono for the Citrus Farm dataset. The main result is a hybrid supervised model, where Lite-Mono still uses RGB as input, but during training we also guide it with projected LiDAR depth labels. Then I will explain why our best model is not the final epoch, and how that leads into our next experiment: a LiDAR-aware edge loss.

---

# Slide 2: Problem and Motivation

## Slide Bullets

- Lite-Mono was originally designed around urban driving-style data
- Citrus scenes are vegetation-heavy, irregular, and visually cluttered
- Plain Citrus training struggles with absolute scale and plant/ground structure
- Goal: improve depth while keeping runtime inference lightweight and RGB-only

## Suggested Visual

Use no image or use one RGB crop from a comparison panel.

## Speaker Script

The problem is that Citrus Farm scenes are very different from typical road scenes. There are trees, thin branches, repeated leaf textures, shadows, and uneven ground. This makes monocular depth difficult because RGB texture does not always correspond to true geometry. Our goal is not to make a LiDAR-based robot at runtime. The robot should still use only RGB and a lightweight Lite-Mono-style model. LiDAR is used offline during training and evaluation.

---

# Slide 3: Baseline: Plain Citrus Model

## Slide Bullets

- Plain Citrus baseline: Lite-Mono trained/adapted without the hybrid LiDAR depth loss
- Main issue: raw-scale depth is very poor
- Plain Citrus test raw abs_rel: 0.7787
- Plain Citrus test raw a1: 0.0077
- Median scaling helps, but does not solve the structure problem

## Suggested Visual

Use:

```text
assets/graph_metric_summary_table.png
```

## Speaker Script

First, we need a fair baseline. The Plain Citrus model is the model trained on Citrus without our hybrid LiDAR depth supervision. Its raw-scale metrics are extremely weak. On the test split, raw abs_rel is about 0.779, and raw a1 is only about 0.008. Median scaling improves the score because it corrects global scale after prediction, but that is not enough for deployment, because in practice we want the model to predict a useful absolute depth scale directly.

---

# Slide 4: Why We Switched From Pure Self-Supervised Training

## Slide Bullets

- Pure self-supervised training relies mostly on photometric consistency
- In Citrus scenes, lower photometric loss did not reliably mean better depth
- Main problems:
  - vegetation texture and shadows can fool the RGB reconstruction loss
  - occlusions and moving scene content create false training signals
  - monocular self-supervision has weak absolute-scale control
- Since Citrus has LiDAR, we used it during training to stabilize depth and scale
- This is still RGB-only at inference time

## Suggested Visual

Use a simple two-column comparison:

```text
Pure self-supervised:
RGB frames -> photometric loss only -> scale/structure can drift

Hybrid supervised:
RGB frames + LiDAR depth mask during training -> stronger depth target
```

## Speaker Script

Before showing the hybrid result, it is important to explain why we moved away from pure self-supervised training. In pure self-supervision, the model mainly learns by reconstructing one RGB frame from nearby frames. That can work well in road scenes, but in Citrus Farm we saw a problem: photometric loss could improve while actual depth metrics got worse. In other words, the model became better at satisfying the image reconstruction objective, but not necessarily better at predicting depth.

This happens because vegetation scenes have repeated leaf texture, shadows, thin branches, occlusions, and irregular geometry. RGB similarity is not always a reliable depth teacher. Also, monocular self-supervision has weak absolute-scale control. Since our prepared Citrus pipeline gives us projected LiDAR depth labels and valid masks, we switched to a hybrid setup. We still use RGB and the Lite-Mono training framework, but LiDAR gives an extra supervised depth signal during training. At inference time, the model still uses only RGB.

---

# Slide 5: Hybrid Supervised Approach

## Slide Bullets

- Training input: RGB temporal frames
- Extra training label: dense LiDAR depth + valid mask
- RGB and LiDAR are paired by timestamp in the prepared dataset, not stacked side by side
- The model sees RGB; LiDAR depth is used only as a loss target
- Loss combines:
  - normal Lite-Mono photometric loss
  - smoothness loss
  - masked LiDAR depth loss
- Runtime remains monocular RGB-only

## Suggested PPT Diagram

Make a simple flow diagram:

```text
RGB frames -> Lite-Mono -> predicted depth
                    |
Dense LiDAR + mask -> supervised depth loss during training only
```

## Speaker Script

Our hybrid approach does not combine RGB and LiDAR into one side-by-side image. Each dataset sample has an RGB frame, a matched dense LiDAR depth label, and a valid mask. The RGB frame goes into Lite-Mono and produces predicted depth. The dense LiDAR depth and valid mask stay separate; they are used only to calculate a supervised depth loss on trusted pixels. So during training, the model learns from both the normal photometric loss and the masked LiDAR depth loss. During inference, none of the LiDAR inputs are needed. The trained model still only takes RGB.

---

# Slide 6: Quantitative Result: Plain Citrus vs Hybrid `weights_13`

## Slide Bullets

- Selected hybrid checkpoint: `weights_13`
- Test raw abs_rel improves: 0.7787 -> 0.1620
- Test raw a1 improves: 0.0077 -> 0.8149
- Test median-scaled abs_rel improves: 0.4889 -> 0.1677
- Test median-scaled a1 improves: 0.6582 -> 0.8159
- Abs rel is average relative depth error; lower is better
- a1 is the fraction of valid pixels within 1.25x of the true depth; higher is better

## Suggested Visuals

Use one or both:

```text
assets/graph_absrel_plain_vs_hybrid_w13.png
assets/graph_a1_plain_vs_hybrid_w13.png
assets/graph_median_scaled_plain_vs_hybrid_w13.png
```

## Speaker Script

The hybrid supervised result is a large improvement over Plain Citrus. Abs rel means absolute relative error: roughly, how wrong the predicted depth is compared with the true depth as a percentage of the true depth. Lower is better. a1 measures the fraction of valid pixels where the prediction is within 1.25 times the true depth. Higher is better. On the test split, raw abs_rel drops from about 0.779 to 0.162, and raw a1 rises from about 0.008 to about 0.815. The very low Plain Citrus raw a1 is not a graph mistake; it happens because the Plain Citrus model predicts depth at the wrong absolute scale, so almost no raw pixels are within the 1.25x threshold.

If we compare after median scaling, the gap is smaller but still important. Plain Citrus test median-scaled abs_rel is about 0.489, while Hybrid `weights_13` is about 0.168. Plain Citrus test median-scaled a1 is about 0.658, while Hybrid is about 0.816. So the honest conclusion is: raw-scale improvement is the biggest win, but even after correcting scale, the hybrid model still has better relative depth quality.

---

# Slide 7: Checkpoint Selection and Visual Evidence

## Slide Bullets

- We trained for 30 epochs and evaluated every checkpoint
- Best validation checkpoint was `weights_13`, not final `weights_29`
- Test confirmation: `weights_13` had the best raw abs_rel among top candidates
- Visual panels support the metric result on typical/good examples
- Lesson: use checkpoint selection instead of assuming final epoch is best

## Suggested Visual

Use one graph plus one comparison panel:

```text
assets/graph_checkpoint_sweep_val_w13_vs_w29.png
assets/visual_plain_medianscaled_vs_weights13_test_typical.png
```

## Speaker Script

After the 30-epoch run, we did not simply assume the final epoch was best. We evaluated every saved checkpoint. The best validation checkpoint by raw abs_rel was `weights_13`, not final `weights_29`. We then checked the top validation candidates on the test split, and `weights_13` still had the best raw abs_rel. For the visual comparison, the Plain Citrus prediction is median-scaled, so it gets a fair scale correction before being compared with Hybrid `weights_13`. Even with that correction, the improvement is clearest in the error maps and selected typical/good examples. The final epoch did not collapse, but it drifted away from the best validation/test tradeoff. So the main lesson is that future runs should use checkpoint selection or early stopping.

---

# Slide 8: Next Experiment: LiDAR-Aware Edge Loss

## Slide Bullets

- Hybrid supervision improved depth and scale, but boundaries are still not explicitly targeted
- RGB-edge losses are risky because texture/shadow edges are not always depth edges
- Next idea: use LiDAR depth jumps to identify trusted geometry edges
- Add a small edge-loss term to the current hybrid recipe
- Start with 2-epoch and 5-epoch gates before any long run

## Suggested Diagram

```text
Dense LiDAR depth + valid mask
        -> compute trusted local depth jumps
        -> LiDAR edge mask
        -> edge-aware loss on predicted depth gradients
```

## Speaker Script

The next planned improvement is LiDAR-aware edge loss. The current hybrid model improves depth and scale, but it does not explicitly teach the model where vegetation boundaries should be. A simple RGB-edge loss is risky because many RGB edges in orchards are just leaf texture or shadow. Instead, we plan to compute trusted depth jumps from the LiDAR depth map and valid mask, then encourage the predicted depth to preserve those geometry edges. We will start conservatively with short 2-epoch and 5-epoch checks before committing to another long run.

---

# Slide 9: Closing Summary

## Slide Bullets

- Hybrid supervised training gives a strong improvement over Plain Citrus
- Best checkpoint is `weights_13`, not final `weights_29`
- This supports best-checkpoint selection and early stopping
- Next research direction: LiDAR-aware edge loss for geometry boundaries
- Goal remains RGB-only lightweight inference

## Speaker Script

To summarize, the hybrid supervised approach is a strong result. It greatly improves both raw-scale and median-scaled metrics over Plain Citrus. The checkpoint scan also taught us something important: the best model was in the middle of training, not the final epoch. Going forward, we should use validation-based checkpoint selection and focus on a more targeted next improvement: LiDAR-aware edge loss. This keeps the final model lightweight and RGB-only, while using LiDAR during training to teach better geometry.

---

# Short Version If Time Is Limited

Use only these slides:

1. Title
2. Problem and motivation
3. Why we switched from pure self-supervised training
4. Hybrid supervised method
5. Quantitative results
6. Checkpoint selection and visual evidence
7. LiDAR-aware edge-loss plan
8. Closing summary

# Things To Say Carefully

Do say:

- Hybrid supervised training strongly improves Citrus depth metrics.
- The selected checkpoint is `weights_13` based on validation sweep and test confirmation.
- LiDAR is used during training/evaluation, but inference remains RGB-only.
- LiDAR-aware edge loss is the next experiment, not a completed result yet.

Do not overclaim:

- Do not say boundaries are already solved.
- Do not say every image is better with `weights_13`.
- Do not say the final epoch collapsed.
- Do not say LiDAR labels are perfect object outlines.

# One-Sentence Research Claim For Tomorrow

Our current evidence shows that masked LiDAR-supervised hybrid training substantially improves Lite-Mono on Citrus Farm while preserving RGB-only inference, and checkpoint analysis suggests the next improvement should focus on validation-selected training plus LiDAR-aware geometry-edge supervision rather than simply training longer.

