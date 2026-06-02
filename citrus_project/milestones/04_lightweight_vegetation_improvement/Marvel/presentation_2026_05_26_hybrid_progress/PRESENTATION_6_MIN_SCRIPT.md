# 6-Minute Presentation Script: Hybrid Supervised Lite-Mono

Target length: about 6 minutes  
Recommended pace: 35-45 seconds per slide  
Main message: Hybrid LiDAR-supervised training improves Lite-Mono on Citrus Farm while keeping inference RGB-only, and checkpoint selection showed `weights_13` is better than the final epoch.

---

## Slide 1: Title

Visual: none, or one Citrus RGB crop.

Script:

Today I will present our progress on improving Lite-Mono for Citrus Farm depth estimation. The main result is a hybrid supervised model: the model still uses RGB at inference time, but during training we guide it with projected LiDAR depth labels. I will also show why our selected checkpoint is `weights_13`, not the final epoch, and what experiment we plan next.

---

## Slide 2: Problem and Motivation

Visual: RGB orchard image or crop from a comparison panel.

Script:

Citrus Farm scenes are much harder than typical road scenes because they contain dense vegetation, repeated leaf textures, shadows, thin branches, and irregular ground. These details can confuse monocular depth estimation. Our goal is to improve Lite-Mono for this agricultural setting while keeping the final model lightweight and RGB-only.

---

## Slide 3: Plain Citrus Baseline

Visual: `assets/graph_metric_summary_table.png`

Script:

The Plain Citrus baseline is Lite-Mono trained without our hybrid LiDAR depth loss. Its biggest weakness is depth accuracy on Citrus, especially scale and vegetation structure. In the table, even after median scaling corrects global scale, Plain Citrus still has much worse abs_rel and a1 than our hybrid model.

---

## Slide 4: Why We Switched From Pure Self-Supervised Training

Visual: simple two-column diagram:

```text
Self-supervised: RGB -> photometric loss
Hybrid: RGB + LiDAR label -> depth loss
```

Script:

Pure self-supervised training can be misleading in Citrus scenes because textures, shadows, occlusions, and weak scale control may improve photometric loss without improving depth. Since Citrus provides LiDAR, we use it during training to stabilize depth and scale, while keeping inference RGB-only.

---

## Slide 5: Hybrid Supervised Method

Visual: simple pipeline diagram:

```text
RGB frames -> Lite-Mono -> predicted depth
Dense LiDAR + mask -> supervised depth loss during training only
```

Script:

In our hybrid setup, RGB and LiDAR are not stacked into one image. The RGB frame goes into Lite-Mono, while the dense LiDAR label and valid mask stay separate as training targets. The loss combines the normal Lite-Mono training losses with a masked LiDAR depth loss. At inference time, the trained model only needs RGB.

---

## Slide 6: Quantitative Result

Visual: use one of:

```text
assets/graph_median_scaled_plain_vs_hybrid_w13.png
assets/graph_absrel_plain_vs_hybrid_w13.png
assets/graph_a1_plain_vs_hybrid_w13.png
```

Script:

The hybrid result is a clear improvement over Plain Citrus. On the test split, raw abs_rel improves from about 0.779 to 0.162, and raw a1 improves from about 0.008 to 0.815. More importantly, even after median scaling gives Plain Citrus a fair scale correction, Hybrid `weights_13` still performs better, so the gain is not only a scale fix.

---

## Slide 7: Checkpoint Selection and Visual Evidence

Visual: use:

```text
assets/graph_checkpoint_sweep_val_w13_vs_w29.png
assets/visual_plain_medianscaled_vs_weights13_test_typical.png
```

Script:

We trained for 30 epochs and evaluated every checkpoint. The best validation checkpoint was `weights_13`, not the final `weights_29`. We confirmed the top candidates on the test split, and `weights_13` had the best raw abs_rel. The visual panels also support this on typical and good examples, so the lesson is to select checkpoints by validation results instead of assuming the last epoch is best.

---

## Slide 8: Next Experiment: LiDAR-Aware Edge Loss

Visual: method diagram:

```text
Dense LiDAR depth + valid mask
        -> trusted depth jumps
        -> LiDAR edge mask
        -> edge-aware loss
```

Script:

The next improvement is LiDAR-aware edge loss. The hybrid model improves overall depth and scale, but it does not explicitly target boundaries. Instead of using RGB edges, which can be shadows or leaf texture, we want to use LiDAR depth jumps as trusted geometry edges. We will test this carefully with short runs first before another long training run.

---

## Slide 9: Closing Summary

Visual: optional, or reuse the best result graph.

Script:

To summarize, hybrid supervised training gives a strong improvement over Plain Citrus while keeping the final model RGB-only. The best checkpoint was `weights_13`, which shows that checkpoint scanning is important. Our next step is LiDAR-aware edge loss, aiming to improve vegetation boundaries without adding LiDAR to inference.

---

## Short Backup Answer For Questions

If asked why LiDAR does not make the model LiDAR-based:

LiDAR is only used during training and evaluation. The deployed model still takes one RGB image and predicts depth, so the inference setup remains monocular and lightweight.

If asked why not just train longer:

The checkpoint scan showed that the final epoch was not the best. Training longer can drift away from the best validation behavior, so future long runs should use checkpoint selection or early stopping.

If asked what median scaling means:

Median scaling corrects the prediction's global scale after inference, so it tests relative depth structure more fairly. Hybrid still wins after median scaling, which means the improvement is not only absolute scale.
