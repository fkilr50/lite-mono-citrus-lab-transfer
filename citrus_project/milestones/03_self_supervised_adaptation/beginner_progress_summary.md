# Milestone 3 Beginner Progress Summary

Date: 2026-05-06

Purpose: explain Milestone 3 in plain language, with the technical terms kept but defined.

## One-Sentence Summary

Milestone 3 is testing whether the original Lite-Mono model can be adapted to Citrus Farm using the standard self-supervised training setup, but our short controlled runs show that the training loss can improve while the actual Citrus depth quality gets worse.

## What We Are Trying To Prove

The research question is:

```text
Can original Lite-Mono fine-tune itself on Citrus RGB video frames
and become better at Citrus depth estimation?
```

This is the normal adaptation baseline.

It is important because Milestone 4 should later beat a fair adapted baseline, not only the untouched original model.

## The Main Pieces

### Depth Network

Plain meaning:

```text
the part of the model that predicts depth from one RGB image
```

In Lite-Mono inference:

```text
RGB image -> depth network -> predicted depth map
```

This is the part we care about for a future robot, because the robot would have one RGB camera image and needs depth.

### Pose Network

Plain meaning:

```text
the training helper that predicts how the camera moved between frames
```

During self-supervised training, we have:

```text
previous image
current image
next image
```

The pose network estimates camera movement between those frames.

During evaluation and deployment, the pose network is not used. It is only a training scaffold.

### Photo Loss

Plain meaning:

```text
how different the current RGB image is from a nearby image after warping
```

Training asks:

```text
Can predicted depth + predicted camera motion warp the nearby frame
so it looks like the current frame?
```

If yes, photo loss goes down.

### LiDAR Depth Evaluation

Plain meaning:

```text
compare predicted depth values against our LiDAR-derived Citrus depth labels
```

Evaluation asks:

```text
Is the predicted depth close to the Citrus depth label?
```

This is different from photo loss.

That difference is the core Milestone 3 problem:

```text
photo loss can improve
while LiDAR depth metrics get worse
```

## Why This Can Happen

Self-supervised depth training learns depth indirectly.

It is not told:

```text
this leaf pixel should be 2.3 meters away
```

It is told:

```text
make nearby video frames match after warping
```

In orchard scenes, image matching can be misleading because:

- leaves repeat visually
- branches are thin
- vegetation has holes
- shadows and highlights change
- nearby and far leaves can look similar
- occlusion happens when the camera moves

So the model may find a depth map that helps image warping but is not better true depth.

## Metrics In Friendly Terms

### `abs_rel`

Plain meaning:

```text
average relative depth error
```

Lower is better.

Example:

```text
true depth:      4 meters
predicted depth: 5 meters
relative error:  1 / 4 = 0.25
```

### `a1`

Plain meaning:

```text
fraction of valid pixels that are close enough
```

Higher is better.

Lite-Mono style `a1` checks whether prediction and label are within about 25 percent of each other.

### Raw Metrics

Plain meaning:

```text
evaluate predicted depth in its original meter scale
```

Raw metrics care whether the predicted distance is close in meters.

### Median-Scaled Metrics

Plain meaning:

```text
first fix one big scale mismatch,
then check whether the inside-image depth pattern is good
```

Median-scaled metrics ask:

```text
after adjusting the overall scale,
does the model still understand what is nearer and farther?
```

For vegetation, this matters because a model may get broad distance scale better while damaging the relative shape of leaves, canopy, trunks, row gaps, and ground.

## What We Tried

| Setting tried | Plain meaning | Result |
|---|---|---|
| Short smoke runs | Check that training, saving, loading, and evaluation work | Passed |
| Pretrained pose | Start the pose helper from better image features | Worked mechanically, but did not solve depth |
| Lower learning rate | Move depth weights more gently | Still worse than baseline |
| Batch size 4 and `drop_path=0` | Reduce training noise | Raw scale improved, relative depth worsened |
| Freeze depth first | Let pose learn first while protecting depth | Safe while frozen, but not a real depth improvement |
| Freeze depth encoder | Keep the big visual feature extractor stable | Worked mechanically, still worse |
| Previous-only frames | Remove the next frame as a possible bad source | Still worse |
| Fully freeze depth path | Train only pose, keep depth unchanged | Depth metrics exactly matched original baseline |
| Seeded trajectory | Watch what happens after 0, 5, 15, 25 depth updates | Relative depth worsened after only 5 depth updates |

## The Most Important Result

Seeded trajectory with 25-step pose warmup:

| checkpoint | depth update steps | raw `abs_rel` | median-scaled `abs_rel` | median-scaled `a1` |
|---|---:|---:|---:|---:|
| original baseline | n/a | 0.7289 | 0.3680 | 0.4807 |
| 25 steps | 0 | 0.7274 | 0.3758 | 0.4797 |
| 30 steps | 5 | 0.6781 | 0.3902 | 0.4484 |
| 40 steps | 15 | 0.6697 | 0.4409 | 0.3908 |
| 50 steps | 25 | 0.7901 | 0.6354 | 0.2280 |

How to read this:

- With 0 depth updates, the model stays close to the original baseline.
- After 5 depth updates, raw meter-scale error improves, but relative depth structure already gets worse.
- After 15 depth updates, relative depth gets worse again.
- After 25 depth updates, this seeded run is much worse.

Plain conclusion:

```text
The harmful direction starts soon after the depth network begins updating.
```

This does not prove a long run can never recover. But it means a long run with the same recipe is risky.

## What Happened In The Conservative 1000-Step Probe

We then tried one more careful version of the same general Milestone 3 idea.

It was conservative because:

- the original depth encoder was frozen
- the depth encoder's BatchNorm statistics were frozen
- only the small depth decoder was allowed to adapt after warmup
- depth learning rate was low
- the run saved checkpoints every 250 steps
- the run stopped at 1000 steps, not a full 30-epoch training

Result on the first 100 validation samples:

| checkpoint | raw abs_rel | median-scaled abs_rel | median-scaled a1 |
|---|---:|---:|---:|
| original baseline | 0.7289 | 0.3680 | 0.4807 |
| step 250 | 0.7331 | 0.4542 | 0.4290 |
| step 500 | 0.7458 | 0.6325 | 0.2445 |
| step 750 | 0.7332 | 0.6152 | 0.2366 |
| final 1000 | 0.7448 | 0.6615 | 0.1827 |

Plain reading:

- Lower `abs_rel` is better.
- Higher `a1` is better.
- The final model is worse than the original baseline.
- The model did not recover as training continued.
- The early checkpoint at step 250 was already worse on relative-depth quality.

So the answer to "maybe it only needs more time?" is:

```text
For this conservative standard recipe, more steps did not help.
```

## What The Visual Comparison Shows

We also made side-by-side images:

```text
original model vs adapted model vs LiDAR label
```

The panels are saved here:

```text
citrus_project/milestones/03_self_supervised_adaptation/runs/citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps/visual_compare_original_vs_adapted_val100_weights_0/
```

Plain visual finding:

- The original model is not great, but it still shows some tree/ground/row depth structure.
- The adapted model looks smoother and less specific.
- In several examples, the adapted model turns the scene into broad depth bands instead of keeping useful object boundaries.
- This means the problem is not only "the predicted meters are scaled wrong."
- The adapted model is also hurting the relative depth shape.

Simple analogy:

```text
The original model gives a blurry map.
The adapted model gives an even smoother map that loses important landmarks.
```

## No-Color-Augmentation Control

We also tested one ordinary training setting:

```text
turn off Citrus color augmentation
```

Color augmentation means the training loader randomly changes brightness/color a bit. This is usually helpful, but orchard scenes already have shadows, leaves, and strong sunlight, so it might make the image-matching training game less stable.

Result after 250 steps:

| checkpoint | raw abs_rel | median-scaled abs_rel | median-scaled a1 |
|---|---:|---:|---:|
| original baseline | 0.7289 | 0.3680 | 0.4807 |
| 250 steps with color aug | 0.7331 | 0.4542 | 0.4290 |
| 250 steps no color aug | 0.7192 | 0.4108 | 0.4568 |

Plain reading:

- No color augmentation is better than color augmentation here.
- But it is still not better than the original baseline on relative depth.
- So color augmentation was likely making the drift worse, but it was not the whole problem.

We then checked 500 steps without color augmentation:

| checkpoint | raw abs_rel | median-scaled abs_rel | median-scaled a1 |
|---|---:|---:|---:|
| original baseline | 0.7289 | 0.3680 | 0.4807 |
| 250 steps no color aug | 0.7192 | 0.4108 | 0.4568 |
| 500 steps no color aug | 0.7235 | 0.5300 | 0.3513 |

Plain reading:

```text
Turning off color augmentation helped at first,
but more steps still made relative depth worse.
```

So this setting is not a good long-run setting either.

## What To Tell The Professor

Short version:

```text
Milestone 3 training works technically, but the standard self-supervised adaptation recipe is unstable on Citrus.
The model can reduce photometric/image-warping loss while getting worse against LiDAR-valid depth labels.
This happens soon after depth weights start updating, and a conservative 1000-step near-epoch probe did not recover.
So we should not blindly scale the same recipe into a long training run.
```

More complete version:

```text
I completed the Citrus training integration and started controlled Milestone 3 self-supervised adaptation tests.
The pipeline runs on GPU, saves checkpoints, loads pretrained Lite-Mono depth weights, and evaluates against the Citrus LiDAR labels.

The main finding is that standard photometric self-supervision is not reliably aligned with Citrus depth quality.
Pose-only training can reduce photo loss, but pose is not used during final depth inference.
When the depth network starts updating, raw scale sometimes improves, but median-scaled relative depth structure gets worse.
In a seeded trajectory, this relative-depth degradation appeared after only 5 depth-update steps.
We then ran a conservative 1000-step probe with the depth encoder frozen and a low decoder learning rate.
That longer monitored run still became worse than the original baseline, especially on median-scaled relative-depth metrics.
Visual comparison shows the adapted model became smoother and less structurally specific, so the failure is not just one scale number being wrong.
Turning off color augmentation helped the short control run, but still did not beat the original baseline on relative-depth metrics.
Extending that no-color-augmentation control from 250 to 500 steps made relative-depth metrics worse again.

This suggests that Citrus vegetation scenes may need a more constrained adaptation method.
For Milestone 3, the current standard self-supervised baseline is not yet useful.
This becomes strong motivation for Milestone 4's proposed improvement.
```

## What We Should Do Now

Do not run a longer version of the same recipe.

Recommended next decision:

1. Treat the current Milestone 3 recipe family as negative evidence.
2. Inspect a few visual examples from the 1000-step checkpoint so we can see what "worse" looks like.
3. Start planning the Milestone 4 improvement as the next research move, while keeping Milestone 3 as the fair failed/weak adaptation baseline.

Possible Milestone 3 wording:

```text
standard self-supervised Citrus adaptation is unstable or insufficient
```

Then Milestone 4 can propose the actual improvement, such as a structure-preserving adaptation objective.

## Current Confidence

High confidence:

- the training pipeline works
- the checkpoints and evaluator work
- pose-only training does not improve final depth inference
- depth updates are the point where instability appears
- photo loss alone is not a trustworthy success signal on Citrus

Still uncertain:

- whether the final improvement should be loss-based, architecture-based, data-based, or hybrid
- whether another standard recipe outside the tried family could work, but the current evidence says we should not keep trying blind longer runs
