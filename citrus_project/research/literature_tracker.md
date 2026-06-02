# Literature Tracker

This is Friend A's working file for related-work intake and model-improvement idea scouting.

## What To Look For

Prioritize papers that are relevant to at least one of these:

- lightweight monocular depth estimation
- self-supervised monocular depth
- depth estimation in outdoor non-urban scenes
- agriculture/orchard/forest vegetation perception
- thin-structure or repetitive-texture handling
- efficient attention, feature fusion, or geometry-preserving modules

## Screening Rule

For each paper, try to answer:

1. Is it lightweight enough to fit our robot story?
2. Does it seem relevant to vegetation-dense scenes?
3. Is it realistic to implement in this repo?
4. Is it low, medium, or high risk?

## Candidate Table

| Paper / Method | Year | Lightweight? | Main Idea | Why Relevant To Citrus | Implementation Risk | Priority |
|---|---:|---|---|---|---|---|
| RTS-Mono: Real-Time Self-Supervised Monocular Depth Estimation for Real-World Deployment | 2025 | yes | Real-time inference focus; competitive accuracy/speed tradeoff | Direct comparison for robot deployment; RGB-only, self-supervised | low | **HIGH** |
| BoRe-Depth: Self-supervised Monocular Depth Estimation with Boundary Refinement for Embedded Systems | 2025 | yes | Boundary-aware refinement for edge devices | Vegetation edges are critical failure points in orchards | medium | **HIGH** |
| PuriLight: A Lightweight Shuffle and Purification Framework for Monocular Depth Estimation | 2026 | yes | Lightweight encoder-decoder with feature purification | Compact model for pest-killer robot; self-supervised | low | **HIGH** |
| CC-Depth: A Lightweight Self-supervised Depth Estimation Network with Enhanced Interpretability | 2024 | yes | Compact architecture with interpretable predictions | Small model + interpretable uncertainty → good for field debugging | low | medium |
| SS3D: End2End Self-Supervised 3D from Web Videos | 2026 | maybe | Web-scale self-supervised SfM; learns from unlabeled video | Could leverage unlabeled robot trajectory data for pretraining | medium | medium |
| Towards Sharper Object Boundaries in Self-Supervised Depth Estimation | 2025 | yes | Occlusion boundary preservation | Vegetation occlusion/edge quality critical for canopy navigation | medium | **HIGH** |
| Deep Neighbor Layer Aggregation for Lightweight Self-Supervised Monocular Depth Estimation | 2023 | yes | Lightweight aggregation design; neighborhood context | Compact model exploration; vegetation texture handling via neighbors | low | medium |
| Occlusion-Aware Self-Supervised Monocular Depth Estimation for Weak-Texture Endoscopic Images | 2025 | yes | Explicit occlusion masking in self-supervised loss | Dense occlusion (leaves) is similar to endoscopy challenges; weak texture relevant | medium | **HIGH** |
| Hybrid-grained Feature Aggregation with Coarse-to-fine Language Guidance for Self-supervised Monocular Depth Estimation | 2025 | maybe | Language guidance for scene understanding | Could encode agronomic scene knowledge (rows, canopy layers, fruit) as guidance | high | medium |
| MambaDepth: Enhancing Long-range Dependency for Self-Supervised Fine-Structured Monocular Depth Estimation | 2024 | maybe | State-space models (Mamba) for long-range context | May help with repetitive canopy structure; newer architecture to benchmark | medium | medium |
| Self-Supervised Monocular Depth Estimation with Large Kernel Attention | 2024 | maybe | Large receptive fields for context | Vegetation context spans large areas; large kernels could help coherence | medium | medium |
| Towards Better Data Exploitation in Self-Supervised Monocular Depth Estimation | 2023 | yes | Data efficiency focus | Robot has limited unlabeled sequences; data reuse matters | low | medium |
| GasMono: Geometry-Aided Self-Supervised Monocular Depth Estimation for Indoor Scenes | 2023 | yes | Geometric priors for non-urban settings | Indoor vegetation (orchards are non-urban) geometry != outdoor urban | medium | medium |
| Jasmine: Harnessing Diffusion Prior for Self-supervised Depth Estimation | 2025 | maybe | Diffusion priors + self-supervised training | Diffusion could provide semantic/structural priors for plant scenes | high | low |
| CropCraft: Complete Structural Characterization of Crop Plants From Images | 2026 | no | 3D plant reconstruction from single image | Plant-specific 3D understanding; heavier but good for validation targets | high | low |
| In-field high throughput grapevine phenotyping with a consumer-grade depth camera | 2019 | yes | Stereo depth for vineyard phenotyping | Agricultural deployment; validation metrics for crop monitoring | low | medium |
| Machine Vision-Based Crop-Load Estimation Using YOLOv8 | 2023 | yes | Detection + visual features for crop tasks | Shows ML deployment in orchards; could combine with depth for fruit detection | low | medium |
| Lite-Mono: A Lightweight CNN and Transformer Architecture for Self-Supervised Monocular Depth Estimation | 2022 | yes | Your baseline; hybrid CNN+Transformer | Direct baseline; good reference for architecture efficiency | n/a | n/a |
| SQLdepth: Generalizable Self-Supervised Fine-Structured Monocular Depth Estimation | 2023 | yes | Structured light-like learning without hardware | Fine detail preservation in sparse vegetation may benefit | medium | medium |
| TAD: Test-Time Adaptation for Depth Estimation via Domain Shift Compensation | 2025 | maybe | Online adaptation to deployment domain | Could adapt Lite-Mono to Citrus domain at inference time | medium | low |

## Research Strategy (Post-Focused Planning)

**Core Hypothesis:**
Vegetation depth fails due to: occlusion + thin structures + weak textures + boundary confusion.
Solution: Lightweight self-supervised depth with occlusion-aware loss + boundary-aware training.

**Paper Story:**
"Improving lightweight monocular depth for vegetation-dense scenes via occlusion-aware + boundary-aware self-supervised training."

---

## CORE PAPERS (Directly Support Main Contribution)

Must read, must implement ideas from:

1. **Occlusion-Aware SSL (Endoscopy)** — Shows how to mask occlusions in photometric loss
   - Why: Dense vegetation = dense occlusion. Same loss strategy applies.
   - Implement: Add occlusion masking to Lite-Mono's photometric loss

2. **BoRe-Depth (Boundary Refinement)** — Shows how to preserve object boundaries
   - Why: Vegetation edges + thin branches = hard boundaries. Need explicit boundary awareness.
   - Implement: Add boundary-aware term to loss or attention

3. **Towards Sharper Object Boundaries** — Edge preservation in self-supervised depth
   - Why: Same problem as BoRe-Depth, different approach
   - Implement: Compare techniques; pick one for Phase 2

4. **RTS-Mono** — Lightweight baseline for real-time deployment
   - Why: Direct architecture comparison; validates "lightweight" design choices
   - Implement: Train on Citrus, compare metrics vs original Lite-Mono

---

## SECONDARY PAPERS (Pick 1-2 max to strengthen Phase 2)

Optional, only if time:

1. **PuriLight** → Alternative compact backbone to benchmark
   - Use: Only if you want encoder-swap ablation
   - Skip if: Time is tight; RTS-Mono comparison is enough

2. **SQLdepth** → Fine structure preservation for sparse vegetation
   - Use: If Phase 1 results show thin-structure failures
   - Skip if: Occlusion + boundary handling already solves the problem

3. **Data Exploitation** → Data efficiency (you have limited sequences)
   - Use: If training is data-starved
   - Skip if: Citrus dataset size is adequate

---

## CUT (Remove from table, don't distract)

❌ **Language-Guided Depth** (Hybrid coarse-to-fine)
- Why: Completely different paradigm; high risk; not core to occlusion/boundary problem

❌ **Jasmine (Diffusion)**
- Why: Heavy, opposite of "lightweight robot" constraint

❌ **MambaDepth, Large Kernel Attention**
- Why: Architecture rabbit hole; doesn't directly solve vegetation occlusion/boundary

❌ **CropCraft, Phenotyping papers**
- Why: Application/validation only; not method papers. Keep only for motivation/metrics inspiration.

❌ **YOLO Crop Estimation**
- Why: Detection ≠ depth. Not relevant unless you're doing multi-task learning (you're not).

---

## Implementation Roadmap

### PHASE 1: Occlusion-Aware Baseline (Milestone 4a)
**Goal:** Add occlusion masking to Lite-Mono's photometric loss

From **Occlusion-Aware SSL** paper:
1. Detect occlusion boundaries (depth discontinuities)
2. Mask photometric loss in uncertain regions
3. Train on Citrus sequences
4. Compare vs original Lite-Mono baseline

**Measurable:** Depth error comparison table

### PHASE 2: Boundary-Aware Refinement (Milestone 4b)
**Goal:** Add explicit boundary preservation

Choose ONE from **BoRe-Depth** or **Sharper Boundaries**:
1. Implement boundary-aware attention or loss term
2. Fine-tune Phase 1 model
3. Compare vs BoRe-Depth trained on Citrus

**Measurable:** Edge quality metrics, depth error improvement

### (Optional) PHASE 3: Architecture Comparison
If time remains:
- Train **RTS-Mono** on Citrus
- Compare runtime/accuracy vs Phase 2
- Document trade-offs

---

## What This Means for Your Project

**Your Paper:**
- Title: *"Occlusion-Aware Lightweight Depth for Vegetation: Self-Supervised Monocular Depth in Citrus Orchards"*
- Contribution: Occlusion masking + boundary awareness in lightweight self-supervised framework
- Scope: Clear, focused, publishable

**Your Milestones:**
- M1: Baseline (original Lite-Mono on Citrus)
- M3: Self-supervised fine-tune on Citrus
- **M4a: Add occlusion-aware loss** (Phase 1)
- **M4b: Add boundary awareness** (Phase 2)
- (Optional) M5: Architecture comparison (RTS-Mono vs Phase 2)
