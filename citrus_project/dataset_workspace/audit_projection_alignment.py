import argparse
import csv
import json
import os
from typing import Dict, List, Optional, Tuple

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from scipy.spatial.transform import Rotation as R

import densify_lidar as dld


def load_npz_array(path: str) -> np.ndarray:
    with np.load(path) as data:
        return data["arr_0"]


def to_rel(path: str, root: str) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def positive_depth_mask(depth: np.ndarray) -> np.ndarray:
    return np.isfinite(depth) & (depth > 0)


def read_zed_left_transform(calibration_yaml: str) -> np.ndarray:
    with open(calibration_yaml, "r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    return np.array(data["cam1"]["T_cn_cnm1"], dtype=np.float64)


def current_hardcoded_chain_matrix(invert: bool) -> np.ndarray:
    """Rebuild the current densify_lidar transform chain for visual comparison."""
    t_v_b = np.array([0.2178, 0.0049, -0.0645], dtype=np.float64)
    q_v_b = [0.5076, -0.4989, 0.4960, -0.4974]

    t_b_z = np.array(
        [0.0662723093557627, -0.09569616160968707, 0.015430994971725126],
        dtype=np.float64,
    )
    q_b_z = [0.0020, -0.0081, 0.0031, 1.0000]

    t_blackfly_in_velodyne = np.eye(4, dtype=np.float64)
    t_blackfly_in_velodyne[:3, :3] = R.from_quat(q_v_b).as_matrix()
    t_blackfly_in_velodyne[:3, 3] = t_v_b

    t_zed_in_blackfly = np.eye(4, dtype=np.float64)
    t_zed_in_blackfly[:3, :3] = R.from_quat(q_b_z).as_matrix()
    t_zed_in_blackfly[:3, 3] = t_b_z

    # Mirrors the current densify_lidar.py chain so we can audit its convention.
    chain = t_blackfly_in_velodyne @ t_zed_in_blackfly
    return np.linalg.inv(chain) if invert else chain


def exact_calibration_chain_matrix(calibration_yaml: str, invert_lidar_to_blackfly: bool) -> np.ndarray:
    """Build LiDAR-to-ZED candidates from calibration files.

    The LiDAR calibration text says parent frame is lidar and child frame is
    Blackfly. Depending on interpretation, that transform can be used directly
    as lidar->Blackfly, or inverted first. The audit renders both variants so
    humans can decide from visual alignment before changing production code.
    """
    t_v_b = np.array([0.2178, 0.0049, -0.0645], dtype=np.float64)
    q_v_b = [0.5076, -0.4989, 0.4960, -0.4974]

    t_blackfly_in_velodyne = np.eye(4, dtype=np.float64)
    t_blackfly_in_velodyne[:3, :3] = R.from_quat(q_v_b).as_matrix()
    t_blackfly_in_velodyne[:3, 3] = t_v_b

    t_lidar_to_blackfly = (
        np.linalg.inv(t_blackfly_in_velodyne)
        if invert_lidar_to_blackfly
        else t_blackfly_in_velodyne
    )
    t_blackfly_to_zed = read_zed_left_transform(calibration_yaml)
    return t_blackfly_to_zed @ t_lidar_to_blackfly


def matrix_to_rvec_tvec(transform: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    rvec, _ = cv2.Rodrigues(transform[:3, :3])
    return rvec, transform[:3, 3]


def transform_candidates(calibration_yaml: str) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    candidates = {
        "production_current": dld.get_lidar_to_zed_transform("production_current"),
        "current_chain_no_invert": matrix_to_rvec_tvec(
            current_hardcoded_chain_matrix(invert=False)
        ),
        "exact_lidar_parent_child_direct": matrix_to_rvec_tvec(
            exact_calibration_chain_matrix(
                calibration_yaml, invert_lidar_to_blackfly=False
            )
        ),
        "exact_lidar_parent_child_inverted": dld.get_lidar_to_zed_transform(
            "exact_lidar_parent_child_inverted"
        ),
    }
    return candidates


def project_sparse(
    point_cloud: np.ndarray,
    rvec: np.ndarray,
    tvec: np.ndarray,
    img_shape: Tuple[int, int],
) -> Tuple[np.ndarray, np.ndarray, Dict[str, object]]:
    pts_3d = np.ascontiguousarray(point_cloud[:, :3], dtype=np.float32)
    img_pts, _ = cv2.projectPoints(
        pts_3d, rvec, tvec, dld.camera_matrix, dld.dist_coeffs
    )
    img_pts = np.squeeze(img_pts)

    r_mat, _ = cv2.Rodrigues(rvec)
    pts_3d_cam = (r_mat @ pts_3d.T).T + tvec
    depths = pts_3d_cam[:, 2]
    diag = dld.projection_diagnostics(img_pts, depths, img_shape)

    sparse_depth = np.zeros(img_shape, dtype=np.float32)
    for i in range(len(img_pts)):
        x, y = img_pts[i, 0], img_pts[i, 1]
        z = depths[i]
        if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(z)):
            continue
        u, v = int(np.round(x)), int(np.round(y))
        if 0 <= u < img_shape[1] and 0 <= v < img_shape[0] and z > 0:
            if sparse_depth[v, u] == 0 or z < sparse_depth[v, u]:
                sparse_depth[v, u] = z

    return sparse_depth, depths, diag


def safe_load_zed_depth(
    zed_path: Optional[str],
    target_shape: Tuple[int, int],
    uint16_scale: float,
) -> Optional[np.ndarray]:
    if zed_path is None:
        return None
    depth = load_npz_array(zed_path)
    if depth.dtype == np.uint16:
        depth = depth.astype(np.float32) * uint16_scale
    else:
        depth = depth.astype(np.float32)
    if depth.shape != target_shape:
        depth = cv2.resize(
            depth, (target_shape[1], target_shape[0]), interpolation=cv2.INTER_NEAREST
        )
    return depth


def zed_overlap_metrics(
    lidar_depth: np.ndarray,
    zed_depth: Optional[np.ndarray],
) -> Dict[str, object]:
    metrics = {
        "zed_valid_ratio": None,
        "zed_lidar_overlap_ratio": None,
        "zed_median_abs_diff_m": None,
        "zed_median_rel_diff": None,
    }
    if zed_depth is None:
        return metrics

    lidar_valid = positive_depth_mask(lidar_depth)
    zed_valid = positive_depth_mask(zed_depth)
    overlap = lidar_valid & zed_valid
    metrics["zed_valid_ratio"] = round(float(np.mean(zed_valid)), 6)
    metrics["zed_lidar_overlap_ratio"] = round(float(np.mean(overlap)), 6)

    if np.any(overlap):
        lidar_vals = lidar_depth[overlap]
        zed_vals = zed_depth[overlap]
        abs_diff = np.abs(lidar_vals - zed_vals)
        rel_diff = abs_diff / np.maximum(zed_vals, 1e-6)
        metrics["zed_median_abs_diff_m"] = round(float(np.median(abs_diff)), 6)
        metrics["zed_median_rel_diff"] = round(float(np.median(rel_diff)), 6)
    return metrics


def prefix_metrics(metrics: Dict[str, object], prefix: str) -> Dict[str, object]:
    return {f"{prefix}_{key}": value for key, value in metrics.items()}


def make_overlay_panel(
    rgb: np.ndarray,
    sparse_maps: Dict[str, np.ndarray],
    zed_depth: Optional[np.ndarray],
    output_path: str,
    title: str,
) -> None:
    n_variants = len(sparse_maps)
    n_cols = 2
    n_rows = int(np.ceil((n_variants + 2) / n_cols))
    plt.figure(figsize=(14, 5 * n_rows))

    ax = plt.subplot(n_rows, n_cols, 1)
    ax.set_title("RGB reference")
    ax.imshow(rgb)
    ax.axis("off")

    subplot_idx = 2
    for name, sparse in sparse_maps.items():
        ax = plt.subplot(n_rows, n_cols, subplot_idx)
        ax.set_title(name)
        ax.imshow(rgb)
        ys, xs = np.nonzero(sparse > 0)
        if xs.size:
            vals = sparse[ys, xs]
            ax.scatter(xs, ys, c=vals, s=2, cmap="turbo", alpha=0.85)
        ax.axis("off")
        subplot_idx += 1

    ax = plt.subplot(n_rows, n_cols, subplot_idx)
    ax.set_title("ZED depth reference" if zed_depth is not None else "ZED depth missing")
    if zed_depth is not None:
        ax.imshow(np.ma.masked_where(~positive_depth_mask(zed_depth), zed_depth), cmap="magma")
    else:
        ax.imshow(np.zeros(rgb.shape[:2]), cmap="gray")
    ax.axis("off")

    plt.suptitle(title)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=120)
    plt.close()


def masked_depth_for_display(depth: Optional[np.ndarray]) -> np.ma.MaskedArray:
    if depth is None:
        return np.ma.masked_where(True, np.zeros((1, 1), dtype=np.float32))
    return np.ma.masked_where(~positive_depth_mask(depth), depth)


def inverse_depth_for_display(
    depth: Optional[np.ndarray],
    min_depth_m: float = 1.0,
    max_depth_m: float = 28.0,
) -> np.ma.MaskedArray:
    """Paper-style depth visualization: nearer valid pixels appear brighter."""
    if depth is None:
        return np.ma.masked_where(True, np.zeros((1, 1), dtype=np.float32))

    valid = positive_depth_mask(depth)
    clipped = np.clip(depth.astype(np.float32), min_depth_m, max_depth_m)
    inverse = np.zeros_like(clipped, dtype=np.float32)
    inverse[valid] = 1.0 / clipped[valid]
    return np.ma.masked_where(~valid, inverse)


def brightened_colormap(name: str, brighten_floor: float = 0.35) -> matplotlib.colors.ListedColormap:
    base = plt.get_cmap(name)(np.linspace(0.0, 1.0, 256))
    base[:, :3] = brighten_floor + (1.0 - brighten_floor) * base[:, :3]
    cmap = matplotlib.colors.ListedColormap(base, name=f"{name}_bright")
    cmap.set_bad(color="black", alpha=1.0)
    return cmap


def sparse_depth_rgb_for_display(
    sparse_depth: np.ndarray,
    min_depth_m: float = 1.0,
    max_depth_m: float = 28.0,
    brighten_floor: float = 0.6,
    line_dilate_px: int = 3,
) -> np.ndarray:
    valid = positive_depth_mask(sparse_depth)
    rgb = np.zeros((*sparse_depth.shape, 3), dtype=np.uint8)
    if not np.any(valid):
        return rgb

    clipped = np.clip(sparse_depth.astype(np.float32), min_depth_m, max_depth_m)
    inverse = np.zeros_like(clipped, dtype=np.float32)
    inverse[valid] = 1.0 / clipped[valid]
    inverse_vals = inverse[valid]

    lo, hi = np.percentile(inverse_vals, [1.0, 99.0])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        lo = float(np.min(inverse_vals))
        hi = float(np.max(inverse_vals))
    hi = max(hi, lo + 1e-6)

    normalized = np.zeros_like(inverse, dtype=np.float32)
    normalized[valid] = np.clip((inverse[valid] - lo) / (hi - lo), 0.0, 1.0)

    sparse_cmap = brightened_colormap("turbo", brighten_floor=brighten_floor)
    colored = (sparse_cmap(normalized)[..., :3] * 255.0).astype(np.uint8)
    rgb[valid] = colored[valid]

    if line_dilate_px > 1:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (line_dilate_px, line_dilate_px))
        dilated_mask = cv2.dilate(valid.astype(np.uint8), kernel, iterations=1).astype(bool)
        dilated_rgb = np.zeros_like(rgb)
        for ch in range(3):
            dilated_rgb[:, :, ch] = cv2.dilate(rgb[:, :, ch], kernel, iterations=1)
        rgb = np.where(dilated_mask[..., None], dilated_rgb, 0)

    return rgb


def show_missing_depth(ax, rgb: np.ndarray) -> None:
    ax.imshow(np.zeros(rgb.shape[:2]), cmap="gray")


def make_detail_panel(
    rgb: np.ndarray,
    sparse_depth: np.ndarray,
    dense_depth: Optional[np.ndarray],
    dist_to_laser: Optional[np.ndarray],
    support_mask: Optional[np.ndarray],
    zed_depth: Optional[np.ndarray],
    output_path: str,
    title: str,
    transform_label: str,
) -> None:
    plt.figure(figsize=(20, 10))

    ax = plt.subplot(2, 4, 1)
    ax.set_title(f"RGB + sparse LiDAR ({transform_label})")
    ax.imshow(rgb)
    ys, xs = np.nonzero(sparse_depth > 0)
    if xs.size:
        ax.scatter(xs, ys, c=sparse_depth[ys, xs], s=2, cmap="turbo", alpha=0.85)
    ax.axis("off")

    ax = plt.subplot(2, 4, 2)
    ax.set_title(f"Sparse LiDAR depth ({transform_label})")
    ax.imshow(sparse_depth_rgb_for_display(sparse_depth))
    ax.axis("off")

    ax = plt.subplot(2, 4, 3)
    ax.set_title(f"LiDAR label visual ({transform_label})")
    if dense_depth is not None:
        ax.imshow(
            inverse_depth_for_display(dense_depth),
            cmap="magma",
            vmin=1.0 / 28.0,
            vmax=1.0,
        )
    else:
        show_missing_depth(ax, rgb)
    ax.axis("off")

    ax = plt.subplot(2, 4, 4)
    ax.set_title(f"LiDAR label depth ({transform_label})")
    if dense_depth is not None:
        ax.imshow(masked_depth_for_display(dense_depth), cmap="turbo", vmin=1.0, vmax=28.0)
    else:
        show_missing_depth(ax, rgb)
    ax.axis("off")

    ax = plt.subplot(2, 4, 5)
    ax.set_title("Valid label mask")
    if support_mask is not None:
        ax.imshow(support_mask, cmap="gray")
    elif dense_depth is not None:
        ax.imshow(positive_depth_mask(dense_depth), cmap="gray")
    else:
        show_missing_depth(ax, rgb)
    ax.axis("off")

    ax = plt.subplot(2, 4, 6)
    ax.set_title("Support distance, not depth")
    if dist_to_laser is not None:
        ax.imshow(dist_to_laser, cmap="Reds")
    else:
        show_missing_depth(ax, rgb)
    ax.axis("off")

    ax = plt.subplot(2, 4, 7)
    ax.set_title("ZED depth visual (near bright)")
    if zed_depth is not None:
        ax.imshow(
            inverse_depth_for_display(zed_depth),
            cmap="magma",
            vmin=1.0 / 28.0,
            vmax=1.0,
        )
    else:
        show_missing_depth(ax, rgb)
    ax.axis("off")

    ax = plt.subplot(2, 4, 8)
    ax.set_title("ZED depth (meters)")
    if zed_depth is not None:
        ax.imshow(masked_depth_for_display(zed_depth), cmap="turbo", vmin=1.0, vmax=28.0)
    else:
        show_missing_depth(ax, rgb)
    ax.axis("off")

    plt.suptitle(title)
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=120)
    plt.close()


def select_sample_indices(total: int, count: int) -> List[int]:
    if count <= 0 or total == 0:
        return []
    if count >= total:
        return list(range(total))
    return sorted(set(np.linspace(0, total - 1, num=count, dtype=int).tolist()))


def collect_matched_pairs(
    rgb_files: List[str],
    lidar_map: List[Tuple[int, str, Optional[str]]],
    max_delta_ns: int,
) -> List[Tuple[str, str, int]]:
    pairs = []
    for rgb_path in rgb_files:
        rgb_ts = dld.extract_timestamp(rgb_path)
        session = dld.extract_session_token(rgb_path)
        lidar_path, delta_ns = dld.find_closest_optimized(
            rgb_ts,
            session,
            lidar_map,
            require_same_session=True,
            max_delta_ns=max_delta_ns,
            fallback_to_any_session=True,
        )
        if lidar_path is not None:
            pairs.append((rgb_path, lidar_path, delta_ns))
    return pairs


def write_csv(path: str, rows: List[Dict[str, object]]) -> None:
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate small RGB/LiDAR/ZED projection audit panels."
    )
    parser.add_argument("--rgb_dir", default="extracted_rgbd/zed2i_zed_node_left_image_rect_color")
    parser.add_argument("--lidar_dir", default="extracted_lidar/velodyne_points")
    parser.add_argument("--zed_depth_dir", default="extracted_rgbd/zed2i_zed_node_depth_depth_registered")
    parser.add_argument("--output_dir", default="projection_alignment_audit")
    parser.add_argument("--max_samples", type=int, default=5)
    parser.add_argument("--max_time_delta_sec", type=float, default=0.5)
    parser.add_argument("--max_zed_depth_delta_sec", type=float, default=0.25)
    parser.add_argument(
        "--interpolation_method",
        default="local_idw",
        choices=dld.SUPPORTED_INTERPOLATION_METHODS,
        help="Dense-label interpolation method for the detail panels.",
    )
    parser.add_argument("--distance_mask_px", type=int, default=25)
    parser.add_argument("--local_idw_k", type=int, default=4)
    parser.add_argument("--local_idw_power", type=float, default=2.0)
    parser.add_argument("--local_idw_max_depth_spread_m", type=float, default=1.25)
    parser.add_argument("--local_idw_max_relative_depth_spread", type=float, default=0.35)
    parser.add_argument("--zed_uint16_scale", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--metrics_only",
        action="store_true",
        help="Compute audit CSV/summary metrics without writing overlay/detail PNG panels.",
    )
    args = parser.parse_args()

    script_root = os.path.dirname(os.path.abspath(__file__))
    rgb_dir = os.path.abspath(os.path.join(script_root, args.rgb_dir))
    lidar_dir = os.path.abspath(os.path.join(script_root, args.lidar_dir))
    zed_depth_dir = os.path.abspath(os.path.join(script_root, args.zed_depth_dir))
    output_dir = os.path.abspath(os.path.join(script_root, args.output_dir))
    calibration_yaml = os.path.join(script_root, "Calibration", "results", "01-multi-cam-result.yaml")
    os.makedirs(output_dir, exist_ok=True)

    all_rgb = sorted(dld.glob.glob(os.path.join(rgb_dir, "*.png")))
    all_lidar = sorted(dld.glob.glob(os.path.join(lidar_dir, "*.npz")))
    all_zed_depth = sorted(dld.glob.glob(os.path.join(zed_depth_dir, "*.npz")))

    if not all_rgb:
        raise SystemExit(f"No RGB files found in: {rgb_dir}")
    if not all_lidar:
        raise SystemExit(f"No LiDAR files found in: {lidar_dir}")
    if not os.path.exists(calibration_yaml):
        raise SystemExit(f"Missing calibration YAML: {calibration_yaml}")

    lidar_map = dld.get_file_timestamp_map(all_lidar)
    zed_map = dld.get_file_timestamp_map(all_zed_depth) if all_zed_depth else []
    max_delta_ns = int(args.max_time_delta_sec * 1e9)
    max_zed_delta_ns = int(args.max_zed_depth_delta_sec * 1e9)
    candidates = transform_candidates(calibration_yaml)

    matched_pairs = collect_matched_pairs(all_rgb, lidar_map, max_delta_ns)
    if not matched_pairs:
        raise SystemExit("No RGB-LiDAR pairs matched current constraints.")

    rows = []
    sample_indices = select_sample_indices(len(matched_pairs), args.max_samples)
    print(
        f"Auditing {len(sample_indices)} samples from "
        f"{len(matched_pairs)} matched RGB-LiDAR pairs into: {output_dir}"
    )

    for sample_number, pair_index in enumerate(sample_indices, start=1):
        rgb_path, lidar_path, delta_ns = matched_pairs[pair_index]
        rgb_ts = dld.extract_timestamp(rgb_path)
        session = dld.extract_session_token(rgb_path)

        zed_path = None
        zed_delta_ns = None
        if zed_map:
            zed_path, zed_delta_ns = dld.find_closest_optimized(
                rgb_ts,
                session,
                zed_map,
                require_same_session=True,
                max_delta_ns=max_zed_delta_ns,
                fallback_to_any_session=False,
            )

        img_bgr = cv2.imread(rgb_path)
        if img_bgr is None:
            print(f"[{sample_number}] Could not read RGB: {rgb_path}")
            continue
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_shape = (rgb.shape[0], rgb.shape[1])
        point_cloud = load_npz_array(lidar_path)
        zed_depth = safe_load_zed_depth(zed_path, img_shape, args.zed_uint16_scale)

        sparse_maps: Dict[str, np.ndarray] = {}
        diagnostics: Dict[str, Dict[str, object]] = {}
        for candidate_name, (rvec, tvec) in candidates.items():
            sparse, _, diag = project_sparse(point_cloud, rvec, tvec, img_shape)
            sparse_maps[candidate_name] = sparse
            diagnostics[candidate_name] = diag

        base_name = os.path.splitext(os.path.basename(rgb_path))[0]
        title = (
            f"{base_name} | lidar={os.path.basename(lidar_path)} | "
            f"delta={delta_ns / 1e6:.3f} ms"
        )
        overlay_path = None
        if not args.metrics_only:
            overlay_path = os.path.join(output_dir, "overlays", f"{sample_number:02d}_{base_name}.png")
            make_overlay_panel(rgb, sparse_maps, zed_depth, overlay_path, title)

        row = {
            "sample": sample_number,
            "rgb_rel": to_rel(rgb_path, script_root),
            "lidar_rel": to_rel(lidar_path, script_root),
            "zed_depth_rel": to_rel(zed_path, script_root) if zed_path else None,
            "time_delta_ms": round(delta_ns / 1e6, 3),
            "zed_time_delta_ms": round(zed_delta_ns / 1e6, 3) if zed_delta_ns is not None else None,
            "overlay_rel": to_rel(overlay_path, script_root) if overlay_path else None,
        }

        detail_modes = ["production_current", "exact_lidar_parent_child_inverted"]
        for detail_mode in detail_modes:
            rvec, tvec = candidates[detail_mode]
            dense_depth = None
            dist_to_laser = None
            support_mask = None
            map_diag = {}
            detail_path = os.path.join(
                output_dir,
                f"details_{detail_mode}",
                f"{sample_number:02d}_{base_name}.png",
            )

            try:
                dense_depth, debug = dld.project_and_densify(
                    point_cloud,
                    rvec,
                    tvec,
                    img_shape=img_shape,
                    interpolation_method=args.interpolation_method,
                    distance_mask_px=args.distance_mask_px,
                    enable_sparse_morph=True,
                    sparse_morph_kernel=3,
                    sparse_morph_iters=1,
                    max_interp_depth_m=28.0,
                    clamp_only_interpolated=True,
                    local_idw_k=args.local_idw_k,
                    local_idw_power=args.local_idw_power,
                    local_idw_max_depth_spread_m=args.local_idw_max_depth_spread_m,
                    local_idw_max_relative_depth_spread=args.local_idw_max_relative_depth_spread,
                    verbose=False,
                    return_extras=True,
                )
                dist_to_laser = debug["dist_to_laser"]
                support_mask = debug["support_mask"]
                map_diag = debug["map_diag"]
            except Exception as exc:
                print(f"[{sample_number}] Dense {detail_mode} projection failed: {exc}")

            if not args.metrics_only:
                make_detail_panel(
                    rgb,
                    sparse_maps[detail_mode],
                    dense_depth,
                    dist_to_laser,
                    support_mask,
                    zed_depth,
                    detail_path,
                    title,
                    detail_mode,
                )
            row[f"{detail_mode}_detail_rel"] = (
                to_rel(detail_path, script_root) if not args.metrics_only else None
            )
            row[f"{detail_mode}_dense_fill_ratio"] = round(
                float(map_diag.get("dense_fill_ratio", 0.0)), 6
            )
            if dense_depth is not None:
                row.update(prefix_metrics(zed_overlap_metrics(dense_depth, zed_depth), detail_mode))

        for candidate_name, diag in diagnostics.items():
            row[f"{candidate_name}_valid_ratio"] = round(float(diag["valid_ratio"]), 6)
            row[f"{candidate_name}_in_bounds_ratio"] = round(float(diag["in_bounds_ratio"]), 6)
            row[f"{candidate_name}_positive_depth_ratio"] = round(
                float(diag["positive_depth_ratio"]), 6
            )
            row[f"{candidate_name}_depth_median"] = diag["depth_median"]
        rows.append(row)

        if args.metrics_only:
            print(f"[{sample_number}] computed metrics for {base_name}")
        else:
            print(
                f"[{sample_number}] wrote {to_rel(overlay_path, script_root)} and "
                f"{len(detail_modes)} detail panels"
            )

    write_csv(os.path.join(output_dir, "audit_metrics.csv"), rows)
    with open(os.path.join(output_dir, "audit_summary.json"), "w", encoding="utf-8") as fp:
        json.dump(
            {
                "num_samples": len(rows),
                "params": vars(args),
                "candidate_names": list(candidates.keys()),
                "detail_transform_modes": [
                    "production_current",
                    "exact_lidar_parent_child_inverted",
                ],
                "manual_review_note": (
                    "This run was metrics-only; use audit_metrics.csv for route comparison."
                    if args.metrics_only
                    else (
                        "Open overlays/ to compare all transform candidates. Open "
                        "details_production_current/ and details_exact_lidar_parent_child_inverted/ "
                        "to compare dense-label diagnostics for the two plausible routes."
                    )
                ),
            },
            fp,
            indent=2,
        )

    print(f"Audit complete. Metrics: {os.path.join(output_dir, 'audit_metrics.csv')}")


if __name__ == "__main__":
    main()
