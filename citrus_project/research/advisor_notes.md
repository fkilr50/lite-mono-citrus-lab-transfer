# Advisor Notes

This file tracks professor/advisor questions, recommendations, and follow-up research directions that should not get lost between chats or meetings.

Use it for:

1. questions that may affect later experiments
2. suggested reference directions
3. possible side studies or ablations
4. advice that is worth revisiting after the current milestone

Keep each entry short and practical:

- date
- what was asked or suggested
- why it might matter
- current interpretation
- follow-up action

## 2026-04-23 - Frame-motion sensitivity during self-supervised training

### Advisor question

What happens if the speed or motion between two neighboring frames is quite different? Will that affect prediction quality?

### Why it matters

This is relevant mainly to self-supervised training, because Lite-Mono-style monocular training relies on neighboring frames, predicted relative pose, and view-synthesis consistency.

Large or irregular frame-to-frame motion can reduce overlap, increase occlusion, and make the reprojection signal noisier.

### Current interpretation

1. This is a good research question, but not a main milestone by itself.
2. It is better treated as a later sub-study or ablation after the baseline and core adaptation path are working.
3. Best fit for now:
   - later Milestone 3 analysis, or
   - Milestone 4 supporting analysis
4. It should not replace the main improvement idea unless later evidence shows it is central to the method.

### Professor recommendation

Look for references that may connect to speed estimation or frame-to-frame motion handling, for example from highway speed camera / traffic speed detection work.

### Our current view on that recommendation

Partly related, but not directly the same problem.

Most highway speed-camera work is about estimating vehicle speed or displacement from video, radar, or tracked image motion. That is not the same as monocular depth estimation.

The most relevant overlap is likely in:

1. frame-to-frame motion estimation
2. optical flow / image displacement
3. ego-motion robustness
4. motion blur sensitivity
5. frame selection or frame sampling under variable motion

So:

1. traffic speed-detection references may be useful as secondary inspiration
2. they should not be the main literature base for this question
3. higher-priority references should still come from self-supervised depth, visual odometry, optical flow, and motion-robust video learning

### Follow-up action

1. Track this as a later analysis candidate, not a current milestone blocker.
2. Ask Friend A to note possible motion-robustness references in `literature_tracker.md`.
3. Revisit after Milestone 1 baseline results and before Milestone 4 improvement selection.
