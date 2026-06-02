# Student Q&A

This file is the beginner-friendly companion to `AGENTS.md`.

Use it for recurring questions, simple explanations, and plain-language reminders that help a new student quickly understand the project without reading every code file first.

Keep answers:

1. simple
2. stable
3. tied to the real project folders/scripts
4. short enough to scan quickly

## Project In One Paragraph

We are trying to improve Lite-Mono, a lightweight monocular depth model, so it works better in citrus/orchard environments. The robot should eventually use only one RGB camera at runtime, but during research we use LiDAR and ZED depth offline to build and check our labels.

## Current Big Picture

1. We already extracted the raw Citrus data we need.
2. We checked how LiDAR should line up with the RGB camera.
3. We chose the best label-generation route.
4. We have not yet run the full final dataset build.
5. After the full build, we will run the original Lite-Mono baseline properly on Citrus.

## Common Questions

### What is a "pair"?

A pair means:

1. one RGB image
2. matched with the closest LiDAR scan in time

Pairing is only the matching step. It does not create a new image by itself.

### Is pairing the same thing as projection?

No.

1. Pairing = choose which LiDAR scan belongs to an RGB image.
2. Projection = place the matched 3D LiDAR points onto the 2D RGB image.
3. Densification = fill some nearby missing depth values so the sparse LiDAR becomes a more usable depth label.

### What is a valid mask?

A valid mask is a trust map for the depth label.

1. `1` means this pixel is trusted enough to use.
2. `0` means do not trust or score this pixel.

The mask is not the same thing as densification. Densification creates label values; the mask tells us which values are safe to use.

### Why does the built dataset contain several data types?

Each item has a different job:

1. RGB image = model input
2. raw LiDAR scan = source measurement used to create the label
3. dense LiDAR label = the depth target we evaluate against
4. valid mask = tells us which label pixels are trustworthy
5. ZED depth path/metrics = an extra sanity check, not the main training target

At runtime, the robot still uses only RGB. The extra data types are for offline research, checking, and evaluation.

### Which folders are real data and which are testing folders?

Real extracted data:

1. `citrus_project/dataset_workspace/extracted_rgbd/zed2i_zed_node_left_image_rect_color/`
2. `citrus_project/dataset_workspace/extracted_rgbd/zed2i_zed_node_depth_depth_registered/`
3. `citrus_project/dataset_workspace/extracted_lidar/velodyne_points/`

Testing/diagnostic folders:

1. `citrus_project/dataset_workspace/projection_alignment_audit/`

This testing folder helps us compare routes and inspect quality. It is not the final dataset.

### What did the testing stage actually show?

We tested four possible LiDAR-to-camera alignment routes.

Result:

1. two routes were clearly wrong
2. two routes were believable
3. `production_current` gave more filled pixels
4. `exact_lidar_parent_child_inverted` agreed much better with ZED depth
5. after visual checks and a 200-sample metrics probe, we chose `exact_lidar_parent_child_inverted` as the final/default route

### About how many samples do we expect in the final built dataset?

Current local snapshot:

1. about 6047 RGB frames
2. about 6049 ZED depth maps
3. about 5235 LiDAR scans
4. about 5282 matched RGB-LiDAR pairs in the time-spread probe

So the final built dataset will likely be around 5.2k samples, though the exact final count depends on filtering and the full build results.

### What is already done, and what is still left?

Done:

1. extraction
2. timestamp pairing logic
3. projection audit
4. densification-method cleanup
5. final label-route decision

Still left:

1. run the full dataset build
2. record final split counts and summary metrics
3. run the original Lite-Mono baseline properly on Citrus
4. start the adaptation/improvement experiments

### Where do we write things down for later paper use?

Use this simple rule:

1. `citrus_project/research/paper_shortlist.md` = the shortlist of results that may later go into the paper
2. `citrus_project/research/dataset_notes.md` = evidence for dataset-building and label-quality decisions
3. `citrus_project/research/baseline_notes.md` = evidence for original-model and baseline results
4. `citrus_project/research/student_qna.md` = simple explanations for us, not paper evidence
5. `AGENTS.md` = project status, milestones, defaults, and decisions

### Why do dense LiDAR labels not look like object outlines?

Dense LiDAR depth labels are depth maps, not segmentation masks or hand-drawn object boundaries.

LiDAR helps boundary learning only where nearby valid depth values change sharply. For example, a jump from about 3 m leaves to a 10 m background can become a depth edge. But plants are thin, irregular, partially transparent to LiDAR spacing, and heavily interpolated during densification, so the label may look like soft patches instead of clean plant outlines.

For a LiDAR-aware edge loss, we should not expect the dense label to visually outline every leaf or branch. We should compute trusted local depth jumps using the dense label plus valid mask, then train only on those reliable geometry-edge pixels.

### Are RGB and LiDAR stacked together before training?

No. The prepared dataset does not make one side-by-side image or one RGB+LiDAR input image.

Each training sample stores linked file paths:

1. the RGB image
2. the matched dense LiDAR depth label
3. the valid mask for trusted label pixels

During loading, RGB becomes the model input tensor. Dense LiDAR depth and valid mask become separate target tensors used for loss/evaluation. The only "stacking" done by PyTorch is batching: several samples are grouped along the batch dimension, like `[batch, channel, height, width]`.

