# File: densify_lidar.py

# Projects 3D LiDAR point clouds onto 2D ZED images and densifies them


import argparse

import numpy as np

import cv2

import os

import glob

import csv

import json

from itertools import product

from bisect import bisect_left

import matplotlib.pyplot as plt

from scipy.spatial import cKDTree

from scipy.spatial.transform import Rotation as R

from scipy.interpolate import griddata


SUPPORTED_TRANSFORM_MODES = (
    "production_current",
    "exact_lidar_parent_child_inverted",
)

SUPPORTED_INTERPOLATION_METHODS = (
    "local_idw",
    "nearest",
    "linear",
    "cubic",
)

# --- 1. SENSOR CALIBRATION MATH ---


# ZED Left Camera Intrinsics (from 01-multi-cam-result.yaml)

# Format: [fx, fy, cx, cy]

intrinsics = [
    527.5591059906969,
    528.5624579927512,
    647.1975009993375,
    357.2476935284654,
]

camera_matrix = np.array(
    [[intrinsics[0], 0, intrinsics[2]], [0, intrinsics[1], intrinsics[3]], [0, 0, 1]],
    dtype=np.float64,
)


# Lens Distortion (radtan)

dist_coeffs = np.array(
    [
        0.004262406434905663,
        -0.030631455483041737,
        5.567440162484537e-05,
        -0.00079751451332914,
    ],
    dtype=np.float64,
)


def _blackfly_in_velodyne_matrix():
    """LiDAR/Velodyne to Blackfly calibration from 03-lidar-cam-result.txt."""

    t_v_b = np.array([0.2178, 0.0049, -0.0645], dtype=np.float64)

    q_v_b = [0.5076, -0.4989, 0.4960, -0.4974]  # qx, qy, qz, qw

    transform = np.eye(4, dtype=np.float64)

    transform[:3, :3] = R.from_quat(q_v_b).as_matrix()

    transform[:3, 3] = t_v_b

    return transform


def _zed_in_blackfly_approx_matrix():
    """Current production approximation of ZED-left relative to Blackfly."""

    t_b_z = np.array(
        [0.0662723093557627, -0.09569616160968707, 0.015430994971725126],
        dtype=np.float64,
    )

    q_b_z = [0.0020, -0.0081, 0.0031, 1.0000]

    transform = np.eye(4, dtype=np.float64)

    transform[:3, :3] = R.from_quat(q_b_z).as_matrix()

    transform[:3, 3] = t_b_z

    return transform


def _zed_in_blackfly_exact_matrix():
    """Exact cam1 T_cn_cnm1 matrix from Calibration/results/01-multi-cam-result.yaml."""

    return np.array(
        [
            [
                0.9998650339614799,
                0.0031122479822752415,
                0.016131576913166447,
                0.0662723093557627,
            ],
            [
                -0.003176059444429916,
                0.9999872275888487,
                0.00393157800043866,
                -0.09569616160968707,
            ],
            [
                -0.016119134828334568,
                -0.003982282218139419,
                0.9998621479587678,
                0.015430994971725126,
            ],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def matrix_to_rvec_tvec(transform):
    rvec, _ = cv2.Rodrigues(transform[:3, :3])

    tvec = transform[:3, 3]

    return rvec, tvec


def lidar_to_zed_matrix(transform_mode="exact_lidar_parent_child_inverted"):
    """Build LiDAR-to-ZED transform variants for production and comparison runs."""

    if transform_mode == "production_current":

        # Mirrors the original densify_lidar chain exactly so old results remain reproducible.
        t_blackfly_in_velodyne = _blackfly_in_velodyne_matrix()

        t_zed_in_blackfly = _zed_in_blackfly_approx_matrix()

        t_zed_in_velodyne = t_blackfly_in_velodyne @ t_zed_in_blackfly

        return np.linalg.inv(t_zed_in_velodyne)

    if transform_mode == "exact_lidar_parent_child_inverted":

        # Uses the exact ZED-left YAML matrix and the visually plausible inverted LiDAR->Blackfly convention.
        t_lidar_to_blackfly = np.linalg.inv(_blackfly_in_velodyne_matrix())

        t_blackfly_to_zed = _zed_in_blackfly_exact_matrix()

        return t_blackfly_to_zed @ t_lidar_to_blackfly

    raise ValueError(
        f"Unknown transform_mode '{transform_mode}'. "
        f"Expected one of: {', '.join(SUPPORTED_TRANSFORM_MODES)}"
    )


def get_lidar_to_zed_transform(transform_mode="exact_lidar_parent_child_inverted"):
    """Return OpenCV rvec/tvec for a named LiDAR-to-ZED transform mode."""

    return matrix_to_rvec_tvec(lidar_to_zed_matrix(transform_mode))


# --- 2. PIPELINE LOGIC ---


def extract_timestamp(filename):

    base = os.path.basename(filename)

    timestamp_str = base.split("_")[-1].split(".")[0]

    return int(timestamp_str)


def extract_session_token(filename):

    base = os.path.basename(filename)

    parts = base.split("_")

    # Expected: <sensor>_<datetime>_<segment>_bag_<timestamp>.<ext>
    # Use segment id as a robust coarse session key across sensors.
    if len(parts) >= 5 and parts[3] == "bag":

        return parts[2]

    return None


def get_timestamp_bounds(files):

    if not files:

        return None, None

    times = [extract_timestamp(f) for f in files]

    return min(times), max(times)


def validate_timestamp_overlap(rgb_files, lidar_files):

    rgb_min, rgb_max = get_timestamp_bounds(rgb_files)

    lidar_min, lidar_max = get_timestamp_bounds(lidar_files)

    if rgb_min is None or lidar_min is None:

        raise ValueError(
            "Could not compute timestamp bounds because one modality is empty."
        )

    overlap_start = max(rgb_min, lidar_min)

    overlap_end = min(rgb_max, lidar_max)

    if overlap_start > overlap_end:

        gap_sec = (overlap_start - overlap_end) / 1e9

        raise ValueError(
            "RGB and LiDAR folders have no timestamp overlap. "
            f"RGB range: [{rgb_min}, {rgb_max}], LiDAR range: [{lidar_min}, {lidar_max}], "
            f"gap: {gap_sec:.2f}s. Check folder selection."
        )


def find_nearest_file_by_timestamp(target_time, files):

    if not files:

        return None, float("inf")

    sorted_pairs = sorted((extract_timestamp(f), f) for f in files)

    times = [t for t, _ in sorted_pairs]

    idx = bisect_left(times, target_time)

    candidates = []

    if idx < len(sorted_pairs):

        candidates.append(sorted_pairs[idx])

    if idx > 0:

        candidates.append(sorted_pairs[idx - 1])

    best_time, best_file = min(candidates, key=lambda x: abs(x[0] - target_time))

    return best_file, abs(best_time - target_time)


def find_closest_lidar(
    rgb_path,
    lidar_dir=None,
    lidar_files=None,
    require_same_session=True,
    max_delta_ns=None,
    fallback_to_any_session=False,
):

    target_time = extract_timestamp(rgb_path)

    all_lidar_files = lidar_files

    if all_lidar_files is None:

        if lidar_dir is None:

            raise ValueError("Either lidar_dir or lidar_files must be provided.")

        all_lidar_files = glob.glob(os.path.join(lidar_dir, "*.npz"))

    if not all_lidar_files:

        return None, float("inf")

    def _match_with(files):

        if not files:

            return None, float("inf")

        closest_file, min_diff = find_nearest_file_by_timestamp(target_time, files)

        if max_delta_ns is not None and min_diff > max_delta_ns:

            return None, min_diff

        return closest_file, min_diff

    if require_same_session:

        session_token = extract_session_token(rgb_path)

        same_session_files = [
            f for f in all_lidar_files if extract_session_token(f) == session_token
        ]

        closest_file, min_diff = _match_with(same_session_files)

        if closest_file is not None:

            return closest_file, min_diff

        if not fallback_to_any_session:

            return None, min_diff

    return _match_with(all_lidar_files)


def find_first_valid_pair(
    rgb_files,
    lidar_files,
    require_same_session=True,
    max_delta_ns=None,
    fallback_to_any_session=False,
):

    for rgb_path in rgb_files:

        lidar_path, delta_ns = find_closest_lidar(
            rgb_path,
            lidar_files=lidar_files,
            require_same_session=require_same_session,
            max_delta_ns=max_delta_ns,
            fallback_to_any_session=fallback_to_any_session,
        )

        if lidar_path is not None:

            return rgb_path, lidar_path, delta_ns

    return None, None, float("inf")


def projection_diagnostics(img_pts, depths, img_shape):

    in_bounds = (
        (img_pts[:, 0] >= 0)
        & (img_pts[:, 0] < img_shape[1])
        & (img_pts[:, 1] >= 0)
        & (img_pts[:, 1] < img_shape[0])
    )

    positive_depth = depths > 0

    valid = in_bounds & positive_depth

    depth_stats = (None, None, None)

    if np.any(positive_depth):

        pos_depths = depths[positive_depth]

        depth_stats = (
            float(np.min(pos_depths)),
            float(np.median(pos_depths)),
            float(np.max(pos_depths)),
        )

    return {
        "num_points": int(len(img_pts)),
        "in_bounds_ratio": float(np.mean(in_bounds)) if len(img_pts) else 0.0,
        "positive_depth_ratio": float(np.mean(positive_depth)) if len(img_pts) else 0.0,
        "valid_ratio": float(np.mean(valid)) if len(img_pts) else 0.0,
        "depth_min": depth_stats[0],
        "depth_median": depth_stats[1],
        "depth_max": depth_stats[2],
    }


def dense_map_diagnostics(
    sparse_depth_map, dense_depth_map, dist_to_laser, distance_mask_px
):

    sparse_fill_ratio = float(np.mean(sparse_depth_map > 0))

    dense_fill_ratio = float(np.mean(dense_depth_map > 0))

    masked_by_distance_ratio = float(np.mean(dist_to_laser > distance_mask_px))

    nonzero_dense = dense_depth_map[dense_depth_map > 0]

    roughness_median = None

    if np.count_nonzero(dense_depth_map) > 1:

        grad_y, grad_x = np.gradient(dense_depth_map)

        grad_mag = np.sqrt(grad_x**2 + grad_y**2)

        roughness_vals = grad_mag[dense_depth_map > 0]

        if roughness_vals.size:

            roughness_median = float(np.median(roughness_vals))

    if nonzero_dense.size:

        dense_min = float(np.min(nonzero_dense))

        dense_median = float(np.median(nonzero_dense))

        dense_max = float(np.max(nonzero_dense))

    else:

        dense_min = None

        dense_median = None

        dense_max = None

    return {
        "sparse_fill_ratio": sparse_fill_ratio,
        "dense_fill_ratio": dense_fill_ratio,
        "masked_by_distance_ratio": masked_by_distance_ratio,
        "dense_min": dense_min,
        "dense_median": dense_median,
        "dense_max": dense_max,
        "roughness_median": roughness_median,
    }


def local_idw_interpolate(
    sparse_depth_map,
    candidate_mask,
    k=4,
    power=2.0,
    max_depth_spread_m=1.25,
    max_relative_depth_spread=0.35,
):
    valid_mask = sparse_depth_map > 0
    dense_depth_map = np.zeros_like(sparse_depth_map, dtype=np.float32)
    dense_depth_map[valid_mask] = sparse_depth_map[valid_mask]

    coords = np.array(np.nonzero(valid_mask)).T.astype(np.float32)
    values = sparse_depth_map[valid_mask].astype(np.float32)
    if values.size == 0:
        return dense_depth_map

    fill_mask = candidate_mask & (~valid_mask)
    fill_coords = np.array(np.nonzero(fill_mask)).T.astype(np.float32)
    if fill_coords.size == 0:
        return dense_depth_map

    query_k = min(max(int(k), 1), values.size)
    tree = cKDTree(coords)
    distances, indices = tree.query(fill_coords, k=query_k)

    if query_k == 1:
        distances = distances[:, None]
        indices = indices[:, None]

    neighbor_depths = values[indices]
    depth_min = np.min(neighbor_depths, axis=1)
    depth_max = np.max(neighbor_depths, axis=1)
    depth_median = np.median(neighbor_depths, axis=1)
    depth_spread = depth_max - depth_min
    relative_spread = depth_spread / np.maximum(depth_median, 1e-6)

    consistent = (depth_spread <= max_depth_spread_m) | (
        relative_spread <= max_relative_depth_spread
    )
    if not np.any(consistent):
        return dense_depth_map

    safe_distances = np.maximum(distances[consistent], 1e-3)
    weights = 1.0 / np.power(safe_distances, power)
    weighted_depths = np.sum(weights * neighbor_depths[consistent], axis=1) / np.sum(
        weights, axis=1
    )

    accepted_coords = fill_coords[consistent].astype(np.int32)
    dense_depth_map[accepted_coords[:, 0], accepted_coords[:, 1]] = weighted_depths.astype(
        np.float32
    )
    return dense_depth_map


def build_metrics_row(
    rgb_file,
    lidar_file,
    delta_ns,
    projection_diag,
    map_diag,
    interpolation_method,
    distance_mask_px,
    enable_sparse_morph,
    sparse_morph_kernel,
    sparse_morph_iters,
    max_interp_depth_m,
    clamp_only_interpolated,
    transform_mode="exact_lidar_parent_child_inverted",
):

    return {
        "rgb_file": os.path.basename(rgb_file),
        "lidar_file": os.path.basename(lidar_file),
        "time_delta_ms": round(delta_ns / 1e6, 3),
        "transform_mode": transform_mode,
        "interpolation_method": interpolation_method,
        "distance_mask_px": distance_mask_px,
        "enable_sparse_morph": enable_sparse_morph,
        "sparse_morph_kernel": sparse_morph_kernel,
        "sparse_morph_iters": sparse_morph_iters,
        "max_interp_depth_m": max_interp_depth_m,
        "clamp_only_interpolated": clamp_only_interpolated,
        "num_points": projection_diag["num_points"],
        "in_bounds_ratio": round(projection_diag["in_bounds_ratio"], 6),
        "positive_depth_ratio": round(projection_diag["positive_depth_ratio"], 6),
        "valid_ratio": round(projection_diag["valid_ratio"], 6),
        "sparse_fill_ratio": round(map_diag["sparse_fill_ratio"], 6),
        "dense_fill_ratio": round(map_diag["dense_fill_ratio"], 6),
        "masked_by_distance_ratio": round(map_diag["masked_by_distance_ratio"], 6),
        "depth_min": projection_diag["depth_min"],
        "depth_median": projection_diag["depth_median"],
        "depth_max": projection_diag["depth_max"],
        "dense_min": map_diag["dense_min"],
        "dense_median": map_diag["dense_median"],
        "dense_max": map_diag["dense_max"],
        "roughness_median": map_diag["roughness_median"],
    }


def save_metrics_csv(csv_path, row):

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    fieldnames = list(row.keys())

    write_header = not os.path.exists(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as fp:

        writer = csv.DictWriter(fp, fieldnames=fieldnames)

        if write_header:

            writer.writeheader()

        writer.writerow(row)


def save_metrics_json(json_path, data):

    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as fp:

        json.dump(data, fp, indent=2)


def save_diagnostic_panel(
    rgb_img,
    sparse_depth_map,
    dist_to_laser,
    dense_depth_map,
    distance_mask_px,
    output_path,
    frame_label,
):

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    sparse_mask = sparse_depth_map > 0

    ys, xs = np.nonzero(sparse_mask)

    sparse_vals = sparse_depth_map[sparse_mask]

    sparse_masked = np.ma.masked_where(sparse_depth_map == 0, sparse_depth_map)

    dense_masked = np.ma.masked_where(dense_depth_map == 0, dense_depth_map)

    plt.figure(figsize=(14, 10))

    plt.subplot(2, 2, 1)

    plt.title("RGB + Projected Sparse Depth")

    plt.imshow(rgb_img)

    if xs.size:

        plt.scatter(xs, ys, s=3, c=sparse_vals, cmap="viridis", alpha=0.75)

    plt.axis("off")

    plt.subplot(2, 2, 2)

    plt.title("Sparse LiDAR Depth")

    plt.imshow(sparse_masked, cmap="viridis")

    plt.axis("off")

    plt.colorbar(fraction=0.046, pad=0.04)

    plt.subplot(2, 2, 3)

    plt.title(f"Distance To Nearest Hit (mask>{distance_mask_px}px)")

    plt.imshow(dist_to_laser, cmap="Reds")

    plt.axis("off")

    plt.colorbar(fraction=0.046, pad=0.04)

    plt.subplot(2, 2, 4)

    plt.title("Dense Depth After Mask")

    plt.imshow(dense_masked, cmap="magma")

    plt.axis("off")

    plt.colorbar(fraction=0.046, pad=0.04)

    plt.suptitle(frame_label)

    plt.tight_layout()

    plt.savefig(output_path, dpi=110)

    plt.close()


def get_file_timestamp_map(files):
    """Returns a sorted list of (timestamp, path, session) for fast lookups."""
    mapping = []
    for f in files:
        mapping.append((extract_timestamp(f), f, extract_session_token(f)))
    # Sort by timestamp
    mapping.sort(key=lambda x: x[0])
    return mapping


def find_closest_optimized(
    target_time,
    target_session,
    lidar_map,
    require_same_session=True,
    max_delta_ns=None,
    fallback_to_any_session=False,
):
    """Uses binary search on a pre-cached map for 1000x faster pairing."""
    if not lidar_map:
        return None, float("inf")

    def _closest_from(candidates):
        if not candidates:
            return None, float("inf")

        times = [item[0] for item in candidates]
        idx = bisect_left(times, target_time)

        best_candidate = None
        min_diff = float("inf")

        # Check current and previous for closest
        for i in [idx, idx - 1]:
            if 0 <= i < len(candidates):
                diff = abs(candidates[i][0] - target_time)
                if diff < min_diff:
                    min_diff = diff
                    best_candidate = candidates[i][1]

        if max_delta_ns is not None and min_diff > max_delta_ns:
            return None, min_diff

        return best_candidate, min_diff

    if require_same_session:
        same_session_candidates = [item for item in lidar_map if item[2] == target_session]
        best_candidate, min_diff = _closest_from(same_session_candidates)
        if best_candidate is not None:
            return best_candidate, min_diff
        if not fallback_to_any_session:
            return None, min_diff

    return _closest_from(lidar_map)


def project_and_densify(
    point_cloud,
    rvec,
    tvec,
    img_shape=(720, 1280),
    interpolation_method="local_idw",
    distance_mask_px=25,
    enable_sparse_morph=False,
    sparse_morph_kernel=3,
    sparse_morph_iters=1,
    max_interp_depth_m=None,
    clamp_only_interpolated=True,
    local_idw_k=4,
    local_idw_power=2.0,
    local_idw_max_depth_spread_m=1.25,
    local_idw_max_relative_depth_spread=0.35,
    verbose=True,
    return_extras=False,
):
    """Projects 3D points to 2D, applies interpolation, and masks out hallucinated sky."""
    if point_cloud is None or point_cloud.size == 0:
        raise ValueError(
            "Loaded LiDAR point cloud is empty. Check that the matched .npz file contains points."
        )
    if point_cloud.ndim != 2 or point_cloud.shape[1] < 3:
        raise ValueError(
            f"Expected point cloud shape (N, >=3), got {point_cloud.shape}."
        )

    # Strip intensity, we only need X, Y, Z for math
    pts_3d = np.ascontiguousarray(point_cloud[:, :3], dtype=np.float32)

    # Project 3D points to 2D image pixels mathematically
    img_pts, _ = cv2.projectPoints(pts_3d, rvec, tvec, camera_matrix, dist_coeffs)
    img_pts = np.squeeze(img_pts)

    # Calculate physical Z-depth
    R_mat, _ = cv2.Rodrigues(rvec)
    pts_3d_cam = (R_mat @ pts_3d.T).T + tvec
    depths = pts_3d_cam[:, 2]

    diag = projection_diagnostics(img_pts, depths, img_shape)

    if verbose:

        print(
            "Projection diagnostics: "
            f"in-bounds={diag['in_bounds_ratio'] * 100:.2f}%, "
            f"positive-z={diag['positive_depth_ratio'] * 100:.2f}%, "
            f"valid={diag['valid_ratio'] * 100:.2f}%, "
            f"depth[m] min/med/max={diag['depth_min']}/{diag['depth_median']}/{diag['depth_max']}"
        )

    if diag["valid_ratio"] == 0.0:

        raise ValueError(
            "No valid projected points (inside image and in front of camera). "
            "Check data pairing and extrinsics."
        )

    # Create an empty 2D canvas of 0.0s
    sparse_depth_map = np.zeros(img_shape, dtype=np.float32)

    # Paint the valid laser dots onto the canvas
    for i in range(len(img_pts)):
        x, y = img_pts[i, 0], img_pts[i, 1]
        z = depths[i]
        if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(z)):
            continue
        u, v = int(np.round(x)), int(np.round(y))

        # Only keep points inside the 720p image and physically in front of the lens
        if 0 <= u < img_shape[1] and 0 <= v < img_shape[0] and z > 0:
            if sparse_depth_map[v, u] == 0 or z < sparse_depth_map[v, u]:
                sparse_depth_map[v, u] = z

    # --- TRUE SPARSE-TO-DENSE INTERPOLATION ---
    valid_mask = sparse_depth_map > 0
    measured_mask = valid_mask.copy()
    coords = np.array(np.nonzero(valid_mask)).T
    values = sparse_depth_map[valid_mask]

    if values.size < 3:

        raise ValueError(
            f"Too few valid sparse depth points ({values.size}) for interpolation."
        )

    if verbose:

        sparse_fill_ratio = float(np.mean(valid_mask))

        print(f"Sparse fill ratio: {sparse_fill_ratio * 100:.4f}%")

    support_mask = measured_mask.astype(np.uint8)

    if enable_sparse_morph and sparse_morph_kernel > 1 and sparse_morph_iters > 0:

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (sparse_morph_kernel, sparse_morph_kernel)
        )

        support_mask = cv2.dilate(support_mask, kernel, iterations=sparse_morph_iters)

    # 1. Create a binary image where empty space is 255, and support pixels are 0
    binary_empty = (support_mask == 0).astype(np.uint8) * 255

    # 2. Calculate the pixel distance from every empty spot to the nearest real laser dot
    dist_to_laser = cv2.distanceTransform(binary_empty, cv2.DIST_L2, 3)

    candidate_mask = dist_to_laser <= distance_mask_px

    if verbose:
        print("      Interpolating sparse points (this takes a second)...")
    if interpolation_method == "local_idw":
        dense_depth_map = local_idw_interpolate(
            sparse_depth_map,
            candidate_mask,
            k=local_idw_k,
            power=local_idw_power,
            max_depth_spread_m=local_idw_max_depth_spread_m,
            max_relative_depth_spread=local_idw_max_relative_depth_spread,
        )
    else:
        grid_y, grid_x = np.mgrid[0 : img_shape[0], 0 : img_shape[1]]
        dense_depth_map = griddata(
            coords, values, (grid_y, grid_x), method=interpolation_method
        )

        nan_mask = np.isnan(dense_depth_map)
        if np.any(nan_mask):
            nearest_fill = griddata(coords, values, (grid_y, grid_x), method="nearest")
            dense_depth_map[nan_mask] = nearest_fill[nan_mask]

    if max_interp_depth_m is not None:

        if clamp_only_interpolated:

            clamp_mask = (dense_depth_map > max_interp_depth_m) & (~measured_mask)

        else:

            clamp_mask = dense_depth_map > max_interp_depth_m

        dense_depth_map[clamp_mask] = 0

    # 3. Chop off the hallucinations: If an interpolated pixel is more than the
    # allowed distance from sparse LiDAR support, delete it (set it to 0).
    dense_depth_map[dist_to_laser > distance_mask_px] = 0

    dense_depth_map = dense_depth_map.astype(np.float32)

    map_diag = dense_map_diagnostics(
        sparse_depth_map, dense_depth_map, dist_to_laser, distance_mask_px
    )

    if verbose:

        print(
            "Map diagnostics: "
            f"sparse-fill={map_diag['sparse_fill_ratio'] * 100:.4f}%, "
            f"dense-fill={map_diag['dense_fill_ratio'] * 100:.4f}%, "
            f"masked-by-distance={map_diag['masked_by_distance_ratio'] * 100:.2f}%, "
            f"roughness-med={map_diag['roughness_median']}"
        )

    if return_extras:

        return dense_depth_map, {
            "projection_diag": diag,
            "map_diag": map_diag,
            "sparse_depth_map": sparse_depth_map,
            "dist_to_laser": dist_to_laser,
            "support_mask": support_mask,
        }

    return dense_depth_map


# --- 3. EXECUTION ---


rgb_folder = "extracted_rgbd/zed2i_zed_node_left_image_rect_color"

lidar_folder = "extracted_lidar/velodyne_points"

output_folder = "extracted_dense_lidar"


TRANSFORM_MODE = "exact_lidar_parent_child_inverted"


MAX_TIME_DELTA_SEC = 0.5

REQUIRE_SAME_SESSION = True

FALLBACK_TO_ANY_SESSION = True

INTERPOLATION_METHOD = "local_idw"

DISTANCE_MASK_PX = 25

ENABLE_DIAGNOSTIC_PANEL = True

SAVE_METRICS = True

ENABLE_SPARSE_MORPH = True

SPARSE_MORPH_KERNEL = 3

SPARSE_MORPH_ITERS = 1

MAX_INTERP_DEPTH_M = 28.0

CLAMP_ONLY_INTERPOLATED = True

RUN_PARAMETER_SWEEP = False

SWEEP_DISTANCE_MASK_PX = [18, 25, 35]

SWEEP_INTERPOLATION_METHODS = ["local_idw", "linear"]

SWEEP_MAX_INTERP_DEPTH_M = [20.0, 28.0, None]


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Project Citrus Farm LiDAR into ZED image space and create dense labels."
    )

    parser.add_argument(
        "--transform_mode",
        default=TRANSFORM_MODE,
        choices=SUPPORTED_TRANSFORM_MODES,
        help="LiDAR-to-ZED calibration convention to use.",
    )

    parser.add_argument(
        "--compare_transform_modes",
        action="store_true",
        help="Run the two visually plausible transform modes side by side on the debug pair.",
    )

    parser.add_argument(
        "--output_folder",
        default=output_folder,
        help="Folder for diagnostic dense outputs, metrics, and panels.",
    )

    args = parser.parse_args()

    output_folder = args.output_folder

    os.makedirs(output_folder, exist_ok=True)

    transform_modes = (
        list(SUPPORTED_TRANSFORM_MODES)
        if args.compare_transform_modes
        else [args.transform_mode]
    )

    # Grab the first RGB image just to test one pair visually

    all_rgb = sorted(glob.glob(os.path.join(rgb_folder, "*.png")))

    all_lidar = sorted(glob.glob(os.path.join(lidar_folder, "*.npz")))

    if not all_rgb:

        raise SystemExit(f"No RGB files found in: {rgb_folder}")

    if not all_lidar:

        raise SystemExit(f"No LiDAR files found in: {lidar_folder}")

    try:

        validate_timestamp_overlap(all_rgb, all_lidar)

    except ValueError as exc:

        raise SystemExit(f"Dataset pairing error: {exc}")

    test_rgb_path, matched_lidar_path, delta_ns = find_first_valid_pair(
        all_rgb,
        all_lidar,
        require_same_session=REQUIRE_SAME_SESSION,
        max_delta_ns=int(MAX_TIME_DELTA_SEC * 1e9),
        fallback_to_any_session=FALLBACK_TO_ANY_SESSION,
    )

    if test_rgb_path is None or matched_lidar_path is None:

        first_rgb = all_rgb[0]

        fallback_lidar, fallback_delta_ns = find_closest_lidar(
            first_rgb,
            lidar_files=all_lidar,
            require_same_session=False,
            max_delta_ns=None,
        )

        fallback_msg = "none"

        if fallback_lidar is not None:

            fallback_msg = (
                f"closest any-session delta for first RGB is {fallback_delta_ns / 1e6:.3f} ms "
                f"({os.path.basename(fallback_lidar)})"
            )

        raise SystemExit(
            "Could not find any valid RGB-LiDAR pair under current constraints. "
            f"Constraint: delta <= {MAX_TIME_DELTA_SEC:.3f}s, "
            f"same-session={REQUIRE_SAME_SESSION}, "
            f"fallback-any-session={FALLBACK_TO_ANY_SESSION}. "
            f"Diagnostic: {fallback_msg}."
        )

    print(f"Testing Projection...")

    print(f"RGB: {os.path.basename(test_rgb_path)}")

    print(f"LiDAR: {os.path.basename(matched_lidar_path)}")

    print(f"Time delta: {delta_ns / 1e6:.3f} ms")

    # Load data

    img = cv2.cvtColor(cv2.imread(test_rgb_path), cv2.COLOR_BGR2RGB)

    point_cloud = np.load(matched_lidar_path)["arr_0"]

    img_shape = (img.shape[0], img.shape[1])

    configs = []

    if RUN_PARAMETER_SWEEP:

        for transform_mode in transform_modes:

            for idx, (interp, mask_px, max_depth) in enumerate(
                product(
                    SWEEP_INTERPOLATION_METHODS,
                    SWEEP_DISTANCE_MASK_PX,
                    SWEEP_MAX_INTERP_DEPTH_M,
                ),
                start=1,
            ):

                configs.append(
                    {
                        "transform_mode": transform_mode,
                        "interpolation_method": interp,
                        "distance_mask_px": mask_px,
                        "max_interp_depth_m": max_depth,
                        "name_suffix": (
                            f"{transform_mode}_cfg_{idx:02d}_{interp}_m{mask_px}_"
                            f"d{str(max_depth).replace('.', 'p')}"
                        ),
                    }
                )

    else:

        for transform_mode in transform_modes:

            configs.append(
                {
                    "transform_mode": transform_mode,
                    "interpolation_method": INTERPOLATION_METHOD,
                    "distance_mask_px": DISTANCE_MASK_PX,
                    "max_interp_depth_m": MAX_INTERP_DEPTH_M,
                    "name_suffix": transform_mode,
                }
            )

    run_results = []

    for cfg_idx, cfg in enumerate(configs, start=1):

        print(
            f"\nRunning config {cfg_idx}/{len(configs)}: "
            f"transform={cfg['transform_mode']}, "
            f"interp={cfg['interpolation_method']}, "
            f"mask={cfg['distance_mask_px']}px, "
            f"max_interp_depth={cfg['max_interp_depth_m']}"
        )

        rvec, tvec = get_lidar_to_zed_transform(cfg["transform_mode"])

        try:

            dense_depth, debug_data = project_and_densify(
                point_cloud,
                rvec,
                tvec,
                img_shape=img_shape,
                interpolation_method=cfg["interpolation_method"],
                distance_mask_px=cfg["distance_mask_px"],
                enable_sparse_morph=ENABLE_SPARSE_MORPH,
                sparse_morph_kernel=SPARSE_MORPH_KERNEL,
                sparse_morph_iters=SPARSE_MORPH_ITERS,
                max_interp_depth_m=cfg["max_interp_depth_m"],
                clamp_only_interpolated=CLAMP_ONLY_INTERPOLATED,
                verbose=True,
                return_extras=True,
            )

        except ValueError as exc:

            print(f"Skipped config due to input error: {exc}")

            continue

        frame_label = (
            f"{os.path.basename(test_rgb_path)} | {os.path.basename(matched_lidar_path)} | "
            f"{cfg['name_suffix']}"
        )

        metrics_row = build_metrics_row(
            test_rgb_path,
            matched_lidar_path,
            delta_ns,
            debug_data["projection_diag"],
            debug_data["map_diag"],
            cfg["interpolation_method"],
            cfg["distance_mask_px"],
            ENABLE_SPARSE_MORPH,
            SPARSE_MORPH_KERNEL,
            SPARSE_MORPH_ITERS,
            cfg["max_interp_depth_m"],
            CLAMP_ONLY_INTERPOLATED,
            cfg["transform_mode"],
        )

        run_results.append(
            {
                "dense_depth": dense_depth,
                "debug_data": debug_data,
                "metrics_row": metrics_row,
                "frame_label": frame_label,
                "config": cfg,
            }
        )

        if SAVE_METRICS:

            csv_path = os.path.join(output_folder, "diagnostics_metrics.csv")

            save_metrics_csv(csv_path, metrics_row)

            json_name = (
                os.path.splitext(os.path.basename(test_rgb_path))[0]
                + f"_{cfg['name_suffix']}.json"
            )

            json_path = os.path.join(output_folder, "diagnostics_json", json_name)

            save_metrics_json(
                json_path,
                {
                    "frame_label": frame_label,
                    "config": cfg,
                    "metrics": metrics_row,
                    "projection_diag": debug_data["projection_diag"],
                    "map_diag": debug_data["map_diag"],
                },
            )

            print(f"Saved metrics CSV: {csv_path}")

            print(f"Saved metrics JSON: {json_path}")

        if ENABLE_DIAGNOSTIC_PANEL:

            panel_name = (
                os.path.splitext(os.path.basename(test_rgb_path))[0]
                + f"_{cfg['name_suffix']}_panel.png"
            )

            panel_path = os.path.join(output_folder, "diagnostics_panels", panel_name)

            save_diagnostic_panel(
                img,
                debug_data["sparse_depth_map"],
                debug_data["dist_to_laser"],
                dense_depth,
                cfg["distance_mask_px"],
                panel_path,
                frame_label,
            )

            print(f"Saved diagnostic panel: {panel_path}")

    if not run_results:

        raise SystemExit(
            "All configs failed. Check calibration and input data quality."
        )

    def sort_key(result):

        rough = result["metrics_row"]["roughness_median"]

        return rough if rough is not None else float("inf")

    best_result = min(run_results, key=sort_key)

    dense_depth = best_result["dense_depth"]

    best_cfg = best_result["config"]

    print(
        "\nSelected best config for display: "
        f"{best_cfg['name_suffix']} "
        f"(roughness={best_result['metrics_row']['roughness_median']})"
    )

    # Display the result

    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)

    plt.title("Left RGB")

    plt.imshow(img)

    plt.axis("off")

    plt.subplot(1, 2, 2)

    plt.title("Dense LiDAR Depth Map")

    # We mask out the 0.0 values (sky) so they appear white instead of dark purple

    depth_masked = np.ma.masked_where(dense_depth == 0, dense_depth)

    plt.imshow(depth_masked, cmap="magma")

    plt.axis("off")

    plt.tight_layout()

    plt.show()
