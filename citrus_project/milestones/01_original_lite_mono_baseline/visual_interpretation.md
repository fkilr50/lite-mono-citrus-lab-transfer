# Milestone 1 Visual Interpretation

This note explains the first good/typical/bad original Lite-Mono visual panels in beginner-friendly language.

The goal is not only to say "the metric is high or low." The goal is to connect the numbers to what the model appears to be doing in real Citrus orchard images.

## How To Read The Panels

Each visual panel has six parts:

1. `RGB input`
   - the original image that Lite-Mono sees

2. `Prediction: raw depth`
   - the model's first converted depth estimate
   - this is before median scaling
   - in these examples, it is usually too close overall

3. `Prediction: median-scaled depth`
   - the same prediction after multiplying by one scale number
   - this does not change the model
   - it only asks whether the near/far layout is reasonable after fixing global scale

4. `Dense LiDAR label on valid pixels`
   - our reference depth label
   - it has holes because we only trust some LiDAR-supported pixels

5. `Evaluation valid mask`
   - white pixels are scored
   - black pixels are ignored

6. `Absolute error after median scaling`
   - brighter means larger depth error
   - darker means smaller depth error

For the depth panels:

```text
bright/yellow = nearer
dark/purple/black = farther
```

Important caution:

Each selected panel uses its own display range so the image is readable. That means colors are good for comparing prediction versus label within the same sample, but they should not be used as exact cross-sample measurements.

## Why We Selected These Three Samples

The helper selected samples using `median_scaled_a1`.

Plain meaning of `a1`:

```text
After scale correction, what fraction of trusted pixels are close enough?
```

`a1` is strict. A pixel only passes if prediction and LiDAR are within about 25% of each other.

The selected validation samples are:

| Role | Index | Median-scaled a1 | Median-scaled abs_rel | Plain meaning |
|---|---:|---:|---:|---|
| Good | 420 | 0.8264 | 0.1510 | most scored pixels are close enough |
| Typical | 82 | 0.4784 | 0.3405 | close to the validation-set middle behavior |
| Bad | 442 | 0.0468 | 0.7835 | almost no scored pixels are close enough |

The same helper was also run on the test split. The selected test samples are:

| Role | Index | Median-scaled a1 | Median-scaled abs_rel | Plain meaning |
|---|---:|---:|---:|---|
| Good | 24 | 0.7709 | 0.1821 | most scored pixels are close enough |
| Typical | 7 | 0.5301 | 0.3168 | close to the test-set middle behavior |
| Bad | 46 | 0.0761 | 0.6204 | very few scored pixels are close enough |

## Good Sample: Index 420

Panel:

```text
citrus_project/milestones/01_original_lite_mono_baseline/visuals/good_index_0420_median_scaled_a1_0.826.png
```

Key numbers:

1. valid fraction: 38.59%
2. median scale ratio: 3.10
3. raw a1: 0.0006
4. median-scaled a1: 0.8264
5. median-scaled abs_rel: 0.1510

Plain interpretation:

The raw prediction is still at the wrong meter scale, so the raw score is bad. After median scaling, the model's near/far layout matches the LiDAR label fairly well for many valid pixels.

This is the kind of case where Lite-Mono's learned scene structure helps. The model sees an orchard row, broad ground, and vegetation walls, then predicts a smooth depth layout that is close enough for many LiDAR-scored pixels.

What it still does imperfectly:

1. it smooths over fine vegetation detail
2. it does not reproduce the LiDAR label holes or scanline-like structure
3. error is still visible around object/vegetation boundaries

Why it matters:

This sample tells us the original model is not useless on Citrus. It can sometimes recover the broad near/far structure after scale correction.

## Typical Sample: Index 82

Panel:

```text
citrus_project/milestones/01_original_lite_mono_baseline/visuals/typical_index_0082_median_scaled_a1_0.478.png
```

Key numbers:

1. valid fraction: 31.80%
2. median scale ratio: 6.00
3. raw a1: 0.0007
4. median-scaled a1: 0.4784
5. median-scaled abs_rel: 0.3405

Plain interpretation:

This is close to the middle behavior of the validation split. The raw model prediction is much too close, so it needs a large scale correction. After scaling, it captures some big scene regions, but many valid pixels are still wrong enough to fail the strict `a1` threshold.

The panel shows a common baseline behavior:

1. the prediction is smooth and visually plausible
2. the LiDAR label has sharper, patchier depth structure
3. the model has trouble matching detailed vegetation and row-edge geometry

Why it matters:

This is the most useful mental picture of the current baseline. The model is not completely random, but it is not reliable enough for accurate vegetation-dense depth.

## Bad Sample: Index 442

Panel:

```text
citrus_project/milestones/01_original_lite_mono_baseline/visuals/bad_index_0442_median_scaled_a1_0.047.png
```

Key numbers:

1. valid fraction: 34.71%
2. median scale ratio: 1.46
3. raw a1: 0.1106
4. median-scaled a1: 0.0468
5. median-scaled abs_rel: 0.7835

Plain interpretation:

This is a true failure case. Median scaling does not help much because the problem is not only global scale. The model's predicted depth layout disagrees with the LiDAR label's layout.

The prediction still looks smooth, but smooth does not mean correct. In the valid-mask region, the LiDAR label says the scene has different depth structure than what the model predicts.

Likely failure pattern:

1. the model treats parts of vegetation and orchard-row structure as broad smooth surfaces
2. the LiDAR label shows more complicated depth changes across trees, gaps, and ground
3. the model's learned prior does not match this agricultural scene well

Why it matters:

This sample is strong evidence for the paper motivation. Original Lite-Mono can produce a nice-looking full depth image, but in vegetation-dense agricultural scenes the nice-looking output can be geometrically wrong.

## What These Three Panels Teach Us

The full validation average says:

```text
median-scaled abs_rel = 0.4176
median-scaled a1      = 0.4629
```

The panels explain what those numbers mean:

1. sometimes the model gets broad layout right after scale correction
2. often it gets some structure right but misses many valid pixels
3. sometimes the output looks smooth and plausible but is badly wrong against LiDAR

The main baseline weakness is not just "wrong scale."

Wrong scale is clearly present, because raw metrics are very poor. But even after median scaling, the model still struggles with:

1. vegetation geometry
2. tree/ground boundaries
3. row gaps and canopy shapes
4. fine or irregular depth changes
5. scenes where smooth monocular priors do not match LiDAR-supported structure

## Test Split Check

The test split good/typical/bad panels show the same general pattern as validation.

Command used:

```powershell
D:/Conda_Envs/lite-mono/python.exe citrus_project/milestones/01_original_lite_mono_baseline/analyze_lite_mono_citrus_results.py --split test
```

Outputs:

1. `visuals/good_index_0024_median_scaled_a1_0.771.png`
2. `visuals/typical_index_0007_median_scaled_a1_0.530.png`
3. `visuals/bad_index_0046_median_scaled_a1_0.076.png`
4. `visuals/test_lite-mono_median_scaled_a1_selection_summary.json`
5. `visuals/test_lite-mono_median_scaled_a1_selection_summary.csv`

What the test panels add:

1. the good test sample again shows that broad orchard-row depth can sometimes be captured after scale correction
2. the typical test sample again shows partial structure with many remaining errors
3. the bad test sample again shows that smooth-looking depth can be geometrically wrong against LiDAR-supported vegetation and row structure

This makes the qualitative interpretation more stable:

```text
The validation panels and test panels show the same kind of baseline behavior.
```

So the baseline evidence is no longer only:

```text
one average metric table
```

It is now:

```text
full val/test metrics + val/test good/typical/bad visual examples + written interpretation
```

## Paper-Facing Interpretation

A careful paper statement could be:

```text
The original Lite-Mono baseline transfers imperfectly to Citrus Farm. Raw-scale evaluation shows severe absolute-scale mismatch. Median-scaled evaluation recovers some relative depth structure, but qualitative panels reveal frequent smoothing and geometry errors around vegetation, tree-row structure, and ground/canopy transitions.
```

This supports the next research step:

```text
adapt or improve lightweight monocular depth estimation for vegetation-dense agricultural scenes while keeping RGB-only inference.
```

## What Is Still Not Proven

These three panels are useful, but they are not the whole story.

They do not yet prove:

1. which exact scene categories fail most often
2. whether the problem is mostly from vegetation, lighting, camera motion, label sparsity, or domain mismatch
3. which improvement idea will work best

The next useful step is either:

1. make a small failure taxonomy from more visual samples
2. add FLOPs or a cleaner deployment-speed benchmark if the paper needs it
3. move into Milestone 2 integration/training if the advisor prefers faster model progress
