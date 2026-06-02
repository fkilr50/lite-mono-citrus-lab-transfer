import argparse
import csv
import json
import os
import random
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional

import cv2
import numpy as np

import densify_lidar as dld


def to_rel(path: str, root: str) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def save_csv(path: str, rows: List[Dict[str, object]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_split_file(path: str, items: List[Dict[str, object]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        for item in items:
            fp.write(f"{item['rgb_rel']} {item['dense_rel']}\n")


def write_json(path: str, data: Dict[str, object]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)


def positive_finite_mask(depth: np.ndarray) -> np.ndarray:
    return np.isfinite(depth) & (depth > 0)


def roughness_median(depth: np.ndarray) -> Optional[float]:
    valid = positive_finite_mask(depth)
    if np.count_nonzero(valid) <= 1:
        return None
    grad_y, grad_x = np.gradient(np.nan_to_num(depth, nan=0.0, posinf=0.0, neginf=0.0))
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    vals = grad_mag[valid]
    return float(np.median(vals)) if vals.size else None


def dense_stats(depth: np.ndarray) -> Dict[str, object]:
    valid = positive_finite_mask(depth)
    vals = depth[valid]
    return {
        "dense_fill_ratio": float(np.mean(valid)),
        "dense_min": float(np.min(vals)) if vals.size else None,
        "dense_median": float(np.median(vals)) if vals.size else None,
        "dense_max": float(np.max(vals)) if vals.size else None,
        "roughness_median": roughness_median(depth),
    }


def load_npz_array(path: str) -> np.ndarray:
    with np.load(path) as data:
        return data["arr_0"]


def save_valid_mask(path: str, dense_depth: np.ndarray) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    valid_mask = positive_finite_mask(dense_depth).astype(np.uint8)
    np.savez_compressed(path, arr_0=valid_mask)


def depth_to_meters(depth: np.ndarray, uint16_scale: float) -> np.ndarray:
    if depth.dtype == np.uint16:
        return depth.astype(np.float32) * uint16_scale
    return depth.astype(np.float32)


def compute_zed_depth_metrics(
    dense_depth: np.ndarray,
    zed_depth_path: Optional[str],
    zed_delta_ns: Optional[int],
    zed_uint16_scale: float,
) -> Dict[str, object]:
    metrics = {
        "zed_depth_rel": None,
        "zed_depth_error": None,
        "zed_time_delta_ms": None,
        "zed_valid_ratio": None,
        "zed_lidar_overlap_ratio": None,
        "zed_median_abs_diff_m": None,
        "zed_median_rel_diff": None,
    }
    if zed_depth_path is None:
        return metrics

    try:
        zed_depth = depth_to_meters(load_npz_array(zed_depth_path), zed_uint16_scale)
    except Exception as exc:
        metrics["zed_depth_error"] = f"{os.path.basename(zed_depth_path)}:{exc}"
        return metrics

    if zed_depth.shape != dense_depth.shape:
        zed_depth = cv2.resize(
            zed_depth,
            (dense_depth.shape[1], dense_depth.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        )

    dense_valid = positive_finite_mask(dense_depth)
    zed_valid = positive_finite_mask(zed_depth)
    overlap = dense_valid & zed_valid

    metrics["zed_time_delta_ms"] = (
        round(zed_delta_ns / 1e6, 3) if zed_delta_ns is not None else None
    )
    metrics["zed_valid_ratio"] = round(float(np.mean(zed_valid)), 6)
    metrics["zed_lidar_overlap_ratio"] = round(float(np.mean(overlap)), 6)

    if np.any(overlap):
        dense_vals = dense_depth[overlap]
        zed_vals = zed_depth[overlap]
        abs_diff = np.abs(dense_vals - zed_vals)
        rel_diff = abs_diff / np.maximum(zed_vals, 1e-6)
        metrics["zed_median_abs_diff_m"] = round(float(np.median(abs_diff)), 6)
        metrics["zed_median_rel_diff"] = round(float(np.median(rel_diff)), 6)

    return metrics


def split_group_key(
    item: Dict[str, object],
    strategy: str,
    index: int,
    time_block_sec: float,
) -> str:
    if strategy == "random":
        return f"item:{index}"

    rgb_rel = str(item["rgb_rel"])
    session = str(item.get("session") or "unknown")

    if strategy == "session":
        return f"session:{session}"

    timestamp = dld.extract_timestamp(rgb_rel)
    if strategy == "time_block":
        block_ns = max(int(time_block_sec * 1e9), 1)
        return f"session:{session}:time_block:{timestamp // block_ns}"

    if strategy == "bag":
        base = os.path.basename(rgb_rel)
        parts = base.split("_")
        if len(parts) >= 5 and parts[3] == "bag":
            return "_".join(parts[:4])
        return f"bag:{session}"

    raise ValueError(f"Unknown split strategy: {strategy}")


def split_items(
    items: List[Dict[str, object]],
    train_ratio: float,
    val_ratio: float,
    seed: int,
    strategy: str = "time_block",
    time_block_sec: float = 60.0,
) -> Dict[str, List[Dict[str, object]]]:
    rng = random.Random(seed)
    n_total = len(items)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    if strategy == "random":
        shuffled = list(items)
        rng.shuffle(shuffled)
        train = shuffled[:n_train]
        val = shuffled[n_train : n_train + n_val]
        test = shuffled[n_train + n_val :]
        return {"train": train, "val": val, "test": test}

    groups = defaultdict(list)
    for index, item in enumerate(items):
        groups[split_group_key(item, strategy, index, time_block_sec)].append(item)

    group_keys = sorted(groups)
    rng.shuffle(group_keys)

    split_map = {"train": [], "val": [], "test": []}
    for key in group_keys:
        target = "test"
        if len(split_map["train"]) < n_train:
            target = "train"
        elif len(split_map["val"]) < n_val:
            target = "val"
        split_map[target].extend(groups[key])

    return split_map


def split_group_counts(
    items: List[Dict[str, object]],
    strategy: str,
    time_block_sec: float,
) -> int:
    return len(
        {
            split_group_key(item, strategy, index, time_block_sec)
            for index, item in enumerate(items)
        }
    )


def build_row(
    rgb_path: str,
    dense_path: str,
    lidar_path: str,
    delta_ns: int,
    script_root: str,
    reused_existing: bool,
    dense_depth: np.ndarray,
    map_diag: Optional[Dict[str, object]],
    projection_diag: Optional[Dict[str, object]],
    support_path: str,
    zed_metrics: Dict[str, object],
    transform_mode: str,
) -> Dict[str, object]:
    dense_diag = dense_stats(dense_depth)
    row = {
        "rgb_rel": to_rel(rgb_path, script_root),
        "dense_rel": to_rel(dense_path, script_root),
        "valid_mask_rel": to_rel(support_path, script_root),
        "lidar_rel": to_rel(lidar_path, script_root),
        "session": dld.extract_session_token(rgb_path),
        "reused_existing_dense": reused_existing,
        "transform_mode": transform_mode,
        "time_delta_ms": round(delta_ns / 1e6, 3),
        "dense_fill_ratio": round(float(dense_diag["dense_fill_ratio"]), 6),
        "dense_min": dense_diag["dense_min"],
        "dense_median": dense_diag["dense_median"],
        "dense_max": dense_diag["dense_max"],
        "roughness_median": dense_diag["roughness_median"],
        "sparse_fill_ratio": None,
        "valid_ratio": None,
        "masked_by_distance_ratio": None,
        "num_projected_points": None,
    }

    if map_diag is not None:
        row["sparse_fill_ratio"] = round(float(map_diag["sparse_fill_ratio"]), 6)
        row["masked_by_distance_ratio"] = round(
            float(map_diag["masked_by_distance_ratio"]), 6
        )
    if projection_diag is not None:
        row["valid_ratio"] = round(float(projection_diag["valid_ratio"]), 6)
        row["num_projected_points"] = projection_diag["num_points"]

    row.update(zed_metrics)
    return row


def process_single_sample(args_tuple) -> Optional[Dict[str, object]]:
    """Worker function for parallel processing."""
    (
        rgb_path, 
        lidar_path, 
        delta_ns, 
        dense_path, 
        support_path,
        zed_depth_path,
        zed_delta_ns,
        rvec, 
        tvec, 
        params, 
        script_root
    ) = args_tuple

    img_bgr = cv2.imread(rgb_path)
    if img_bgr is None:
        return None
    img_shape = (img_bgr.shape[0], img_bgr.shape[1])

    try:
        if params["skip_existing"] and os.path.exists(dense_path):
            dense_depth = load_npz_array(dense_path).astype(np.float32)
            save_valid_mask(support_path, dense_depth)
            dense_fill_ratio = float(np.mean(positive_finite_mask(dense_depth)))
            if dense_fill_ratio < params["min_dense_fill_ratio"]:
                return None
            zed_metrics = compute_zed_depth_metrics(
                dense_depth,
                zed_depth_path,
                zed_delta_ns,
                params["zed_uint16_scale"],
            )
            if zed_depth_path is not None:
                zed_metrics["zed_depth_rel"] = to_rel(zed_depth_path, script_root)
            return build_row(
                rgb_path,
                dense_path,
                lidar_path,
                delta_ns,
                script_root,
                reused_existing=True,
                dense_depth=dense_depth,
                map_diag=None,
                projection_diag=None,
                support_path=support_path,
                zed_metrics=zed_metrics,
                transform_mode=params.get("transform_mode", dld.TRANSFORM_MODE),
            )

        point_cloud = np.load(lidar_path)["arr_0"]
        dense_depth, debug = dld.project_and_densify(
            point_cloud,
            rvec,
            tvec,
            img_shape=img_shape,
            interpolation_method=params["interpolation_method"],
            distance_mask_px=params["distance_mask_px"],
            enable_sparse_morph=params["enable_sparse_morph"],
            sparse_morph_kernel=params["sparse_morph_kernel"],
            sparse_morph_iters=params["sparse_morph_iters"],
            max_interp_depth_m=params["max_interp_depth_m"],
            clamp_only_interpolated=params["clamp_only_interpolated"],
            local_idw_k=params["local_idw_k"],
            local_idw_power=params["local_idw_power"],
            local_idw_max_depth_spread_m=params["local_idw_max_depth_spread_m"],
            local_idw_max_relative_depth_spread=params[
                "local_idw_max_relative_depth_spread"
            ],
            verbose=False,
            return_extras=True,
        )
        
        dense_fill_ratio = float(debug["map_diag"]["dense_fill_ratio"])
        if dense_fill_ratio < params["min_dense_fill_ratio"]:
            return None

        os.makedirs(os.path.dirname(dense_path), exist_ok=True)
        np.savez_compressed(dense_path, arr_0=dense_depth)
        save_valid_mask(support_path, dense_depth)

        zed_metrics = compute_zed_depth_metrics(
            dense_depth,
            zed_depth_path,
            zed_delta_ns,
            params["zed_uint16_scale"],
        )
        if zed_depth_path is not None:
            zed_metrics["zed_depth_rel"] = to_rel(zed_depth_path, script_root)

        return build_row(
            rgb_path,
            dense_path,
            lidar_path,
            delta_ns,
            script_root,
            reused_existing=False,
            dense_depth=dense_depth,
            map_diag=debug["map_diag"],
            projection_diag=debug["projection_diag"],
            support_path=support_path,
            zed_metrics=zed_metrics,
            transform_mode=params.get("transform_mode", dld.TRANSFORM_MODE),
        )
    except Exception as e:
        print(f"Error processing {os.path.basename(rgb_path)}: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optimized Parallel Builder for Citrus Farm Dataset."
    )
    parser.add_argument("--rgb_dir", default="extracted_rgbd/zed2i_zed_node_left_image_rect_color")
    parser.add_argument("--lidar_dir", default="extracted_lidar/velodyne_points")
    parser.add_argument("--zed_depth_dir", default="extracted_rgbd/zed2i_zed_node_depth_depth_registered")
    parser.add_argument(
        "--output_dir",
        default=None,
        help=(
            "Output folder. Defaults to prepared_training_dataset for the current final/default "
            "transform, or prepared_training_dataset_<transform_mode> for alternate transforms."
        ),
    )
    parser.add_argument(
        "--transform_mode",
        default=dld.TRANSFORM_MODE,
        choices=dld.SUPPORTED_TRANSFORM_MODES,
        help="LiDAR-to-ZED calibration convention used to generate dense labels.",
    )
    parser.add_argument("--max_time_delta_sec", type=float, default=0.5)
    parser.add_argument("--max_zed_depth_delta_sec", type=float, default=0.25)
    parser.add_argument(
        "--require_same_session",
        dest="require_same_session",
        action="store_true",
        default=True,
        help="Enforce same-session match first.",
    )
    parser.add_argument(
        "--no_require_same_session",
        dest="require_same_session",
        action="store_false",
        help="Allow nearest timestamp matching without session restriction.",
    )
    parser.add_argument(
        "--fallback_to_any_session",
        dest="fallback_to_any_session",
        action="store_true",
        default=True,
        help="If same-session match fails, retry nearest timestamp across sessions.",
    )
    parser.add_argument(
        "--no_fallback_to_any_session",
        dest="fallback_to_any_session",
        action="store_false",
        help="Disable cross-session fallback when same-session is required.",
    )
    parser.add_argument(
        "--interpolation_method",
        default="local_idw",
        choices=dld.SUPPORTED_INTERPOLATION_METHODS,
        help="Sparse-to-dense fill method. local_idw is safer for vegetation because it refuses large local depth jumps.",
    )
    parser.add_argument("--distance_mask_px", type=int, default=25)
    parser.add_argument("--local_idw_k", type=int, default=4)
    parser.add_argument("--local_idw_power", type=float, default=2.0)
    parser.add_argument("--local_idw_max_depth_spread_m", type=float, default=1.25)
    parser.add_argument("--local_idw_max_relative_depth_spread", type=float, default=0.35)
    parser.add_argument("--enable_sparse_morph", action="store_true", default=True)
    parser.add_argument("--sparse_morph_kernel", type=int, default=3)
    parser.add_argument("--sparse_morph_iters", type=int, default=1)
    parser.add_argument("--max_interp_depth_m", type=float, default=28.0)
    parser.add_argument("--clamp_only_interpolated", action="store_true", default=True)
    parser.add_argument("--min_dense_fill_ratio", type=float, default=0.0)
    parser.add_argument("--train_ratio", type=float, default=0.8)
    parser.add_argument("--val_ratio", type=float, default=0.1)
    parser.add_argument(
        "--split_strategy",
        default="time_block",
        choices=["random", "time_block", "bag", "session"],
        help="Use grouped splits to avoid adjacent-frame leakage. random keeps legacy behavior.",
    )
    parser.add_argument(
        "--time_block_sec",
        type=float,
        default=60.0,
        help="Time block size for --split_strategy time_block.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    parser.add_argument("--max_samples", type=int, default=0)
    parser.add_argument("--skip_existing", action="store_true", default=True)
    parser.add_argument(
        "--no_skip_existing",
        dest="skip_existing",
        action="store_false",
        help="Regenerate dense outputs even if files already exist.",
    )
    parser.add_argument(
        "--enable_zed_depth_metrics",
        dest="enable_zed_depth_metrics",
        action="store_true",
        default=True,
        help="Compare LiDAR-derived labels with nearest extracted ZED depth when available.",
    )
    parser.add_argument(
        "--no_zed_depth_metrics",
        dest="enable_zed_depth_metrics",
        action="store_false",
        help="Disable ZED-depth sanity-check metrics.",
    )
    parser.add_argument(
        "--zed_uint16_scale",
        type=float,
        default=0.001,
        help="Scale applied if extracted ZED depth is uint16; float depth is assumed meters.",
    )
    args = parser.parse_args()

    script_root = os.path.dirname(os.path.abspath(__file__))
    rgb_dir = os.path.abspath(os.path.join(script_root, args.rgb_dir))
    lidar_dir = os.path.abspath(os.path.join(script_root, args.lidar_dir))
    zed_depth_dir = os.path.abspath(os.path.join(script_root, args.zed_depth_dir))
    output_dir_name = args.output_dir
    if output_dir_name is None:
        output_dir_name = (
            "prepared_training_dataset"
            if args.transform_mode == dld.TRANSFORM_MODE
            else f"prepared_training_dataset_{args.transform_mode}"
        )
    output_dir = os.path.abspath(os.path.join(script_root, output_dir_name))

    dense_dir = os.path.join(output_dir, "dense_lidar_npz")
    valid_mask_dir = os.path.join(output_dir, "dense_lidar_valid_mask_npz")
    os.makedirs(dense_dir, exist_ok=True)
    os.makedirs(valid_mask_dir, exist_ok=True)

    print(f"Output directory: {output_dir}")
    print(f"Transform mode: {args.transform_mode}")
    print("Loading file lists and pre-caching timestamps...")
    all_rgb = sorted([f for f in dld.glob.glob(os.path.join(rgb_dir, "*.png"))])
    all_lidar_raw = sorted([f for f in dld.glob.glob(os.path.join(lidar_dir, "*.npz"))])
    all_zed_depth = []
    if args.enable_zed_depth_metrics and os.path.isdir(zed_depth_dir):
        all_zed_depth = sorted(
            [f for f in dld.glob.glob(os.path.join(zed_depth_dir, "*.npz"))]
        )
    
    if not all_rgb or not all_lidar_raw:
        print("Error: RGB or LiDAR directory is empty.")
        return

    lidar_map = dld.get_file_timestamp_map(all_lidar_raw)
    zed_depth_map = dld.get_file_timestamp_map(all_zed_depth) if all_zed_depth else []
    rvec, tvec = dld.get_lidar_to_zed_transform(args.transform_mode)
    max_delta_ns = int(args.max_time_delta_sec * 1e9)
    max_zed_depth_delta_ns = int(args.max_zed_depth_delta_sec * 1e9)

    params = {
        "transform_mode": args.transform_mode,
        "interpolation_method": args.interpolation_method,
        "distance_mask_px": args.distance_mask_px,
        "local_idw_k": args.local_idw_k,
        "local_idw_power": args.local_idw_power,
        "local_idw_max_depth_spread_m": args.local_idw_max_depth_spread_m,
        "local_idw_max_relative_depth_spread": args.local_idw_max_relative_depth_spread,
        "enable_sparse_morph": args.enable_sparse_morph,
        "sparse_morph_kernel": args.sparse_morph_kernel,
        "sparse_morph_iters": args.sparse_morph_iters,
        "max_interp_depth_m": args.max_interp_depth_m,
        "clamp_only_interpolated": args.clamp_only_interpolated,
        "min_dense_fill_ratio": args.min_dense_fill_ratio,
        "max_time_delta_sec": args.max_time_delta_sec,
        "require_same_session": args.require_same_session,
        "fallback_to_any_session": args.fallback_to_any_session,
        "skip_existing": args.skip_existing,
        "split_strategy": args.split_strategy,
        "time_block_sec": args.time_block_sec,
        "enable_zed_depth_metrics": args.enable_zed_depth_metrics,
        "max_zed_depth_delta_sec": args.max_zed_depth_delta_sec,
        "zed_uint16_scale": args.zed_uint16_scale,
    }

    print(f"Pairing {len(all_rgb)} RGB frames with LiDAR...")
    tasks = []
    reused_existing_count = 0
    
    for rgb_path in all_rgb:
        if args.max_samples > 0 and len(tasks) >= args.max_samples:
            break
            
        target_session = dld.extract_session_token(rgb_path)
        rgb_timestamp = dld.extract_timestamp(rgb_path)
        lidar_path, delta_ns = dld.find_closest_optimized(
            rgb_timestamp,
            target_session,
            lidar_map,
            require_same_session=args.require_same_session,
            max_delta_ns=max_delta_ns,
            fallback_to_any_session=args.fallback_to_any_session,
        )

        if lidar_path:
            base_name = os.path.splitext(os.path.basename(rgb_path))[0]
            dense_path = os.path.join(dense_dir, f"{base_name}.npz")
            support_path = os.path.join(valid_mask_dir, f"{base_name}.npz")
            zed_depth_path = None
            zed_delta_ns = None

            if zed_depth_map:
                zed_depth_path, zed_delta_ns = dld.find_closest_optimized(
                    rgb_timestamp,
                    target_session,
                    zed_depth_map,
                    require_same_session=True,
                    max_delta_ns=max_zed_depth_delta_ns,
                    fallback_to_any_session=False,
                )

            if args.skip_existing and os.path.exists(dense_path):
                reused_existing_count += 1

            tasks.append(
                (
                    rgb_path,
                    lidar_path,
                    delta_ns,
                    dense_path,
                    support_path,
                    zed_depth_path,
                    zed_delta_ns,
                    rvec,
                    tvec,
                    params,
                    script_root,
                )
            )

    print(
        f"Paired {len(tasks)} samples. "
        f"(Will reuse existing dense files: {reused_existing_count})"
    )
    
    if not tasks:
        print("No samples matched current constraints.")
        return

    print(f"Starting build with {args.workers} workers...")
    start_time = time.time()
    rows = []
    
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_single_sample, t) for t in tasks]
        
        done_count = 0
        for future in as_completed(futures):
            res = future.result()
            if res:
                rows.append(res)
            done_count += 1
            if done_count % 10 == 0 or done_count == len(tasks):
                elapsed = time.time() - start_time
                per_sample = elapsed / done_count
                eta = per_sample * (len(tasks) - done_count)
                print(f"  Progress: {done_count}/{len(tasks)} | ETA: {int(eta)}s | {1/per_sample:.2f} items/s", end="\r")

    print(f"\nProcessing complete in {time.time() - start_time:.2f}s")
    
    if not rows:
        print("No valid samples produced.")
        return

    print("Generating splits and metrics...")
    rows.sort(key=lambda r: str(r["rgb_rel"]))
    split_map = split_items(
        rows,
        args.train_ratio,
        args.val_ratio,
        args.seed,
        strategy=args.split_strategy,
        time_block_sec=args.time_block_sec,
    )
    
    splits_dir = os.path.join(output_dir, "splits")
    metrics_dir = os.path.join(output_dir, "metrics")
    os.makedirs(splits_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)

    write_split_file(os.path.join(splits_dir, "train_pairs.txt"), split_map["train"])
    write_split_file(os.path.join(splits_dir, "val_pairs.txt"), split_map["val"])
    write_split_file(os.path.join(splits_dir, "test_pairs.txt"), split_map["test"])
    save_csv(os.path.join(metrics_dir, "all_samples.csv"), rows)

    total_groups = split_group_counts(rows, args.split_strategy, args.time_block_sec)
    split_group_summary = {
        name: split_group_counts(items, args.split_strategy, args.time_block_sec)
        for name, items in split_map.items()
    }

    summary = {
        "num_total": len(rows),
        "num_train": len(split_map["train"]),
        "num_val": len(split_map["val"]),
        "num_test": len(split_map["test"]),
        "num_reused_existing_dense": sum(
            1 for row in rows if row.get("reused_existing_dense")
        ),
        "num_split_groups_total": total_groups,
        "num_split_groups": split_group_summary,
        "params": params,
    }
    write_json(os.path.join(metrics_dir, "summary.json"), summary)

    print(f"Build complete. Total samples: {len(rows)}")


if __name__ == "__main__":
    main()
