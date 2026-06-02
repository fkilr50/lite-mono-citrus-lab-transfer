import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


BASELINE_MODULE_DIR = Path(__file__).resolve().parents[2] / "01_original_lite_mono_baseline"
if str(BASELINE_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(BASELINE_MODULE_DIR))

from evaluate_lite_mono_citrus import (  # noqa: E402
    compute_depth_errors_np,
    load_lite_mono_model,
    load_npz_array,
    repo_root,
    run_lite_mono_inference,
)


@dataclass
class SelectedRow:
    role: str
    row: dict
    metric_value: float


def read_rows(csv_path):
    with csv_path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def select_rows(rows, metric):
    scored = []
    for row in rows:
        try:
            value = float(row[metric])
        except (KeyError, TypeError, ValueError):
            continue
        if np.isfinite(value):
            scored.append((value, row))
    if not scored:
        raise ValueError("No finite values found for metric {}".format(metric))

    scored.sort(key=lambda item: item[0])
    return [
        SelectedRow("bad", scored[0][1], scored[0][0]),
        SelectedRow("typical", scored[len(scored) // 2][1], scored[len(scored) // 2][0]),
        SelectedRow("good", scored[-1][1], scored[-1][0]),
    ]


def percentile_or(values, percentile, fallback):
    values = values[np.isfinite(values)]
    if values.size == 0:
        return fallback
    value = float(np.percentile(values, percentile))
    if not np.isfinite(value):
        return fallback
    return value


def median_scale(pred, dense, eval_mask):
    pred_eval = pred[eval_mask].astype(np.float64)
    gt_eval = dense[eval_mask].astype(np.float64)
    pred_median = float(np.median(pred_eval))
    gt_median = float(np.median(gt_eval))
    if not np.isfinite(pred_median) or pred_median <= 0:
        return None
    return gt_median / pred_median


def compute_metrics(pred, dense, eval_mask, eval_min_depth, eval_max_depth):
    gt_eval = dense[eval_mask].astype(np.float64)
    pred_eval = np.clip(pred[eval_mask], eval_min_depth, eval_max_depth).astype(np.float64)
    return compute_depth_errors_np(gt_eval, pred_eval)


def render_comparison(
    selected,
    workspace_dir,
    output_dir,
    plain_model,
    weights13_model,
    plain_name,
    weights13_name,
    eval_min_depth,
    eval_max_depth,
):
    row = selected.row
    rgb_path = workspace_dir / row["rgb_rel"]
    dense_path = workspace_dir / row["dense_rel"]
    mask_path = workspace_dir / row["valid_mask_rel"]

    dense = load_npz_array(dense_path).astype(np.float32)
    valid_mask = load_npz_array(mask_path) > 0
    plain_raw, _ = run_lite_mono_inference(rgb_path, dense.shape, plain_model, False)
    weights13_raw, _ = run_lite_mono_inference(rgb_path, dense.shape, weights13_model, False)

    eval_mask = (
        valid_mask
        & np.isfinite(dense)
        & (dense > eval_min_depth)
        & (dense < eval_max_depth)
        & np.isfinite(plain_raw)
        & np.isfinite(weights13_raw)
        & (plain_raw > 0)
        & (weights13_raw > 0)
    )
    if not np.any(eval_mask):
        raise ValueError("No valid comparison pixels for {}".format(row["rgb_rel"]))

    plain_scale = median_scale(plain_raw, dense, eval_mask)
    if plain_scale is None:
        raise ValueError("Invalid Plain Citrus median scale for {}".format(row["rgb_rel"]))

    plain_scaled = plain_raw * plain_scale
    weights13_display = weights13_raw
    plain_error = np.full(dense.shape, np.nan, dtype=np.float32)
    weights13_error = np.full(dense.shape, np.nan, dtype=np.float32)
    plain_error[eval_mask] = np.abs(plain_scaled[eval_mask] - dense[eval_mask])
    weights13_error[eval_mask] = np.abs(weights13_display[eval_mask] - dense[eval_mask])
    error_delta = weights13_error - plain_error
    label_display = np.where(eval_mask, dense, np.nan)

    plain_metrics = compute_metrics(
        plain_scaled, dense, eval_mask, eval_min_depth, eval_max_depth
    )
    weights13_metrics = compute_metrics(
        weights13_display, dense, eval_mask, eval_min_depth, eval_max_depth
    )

    depth_values = np.concatenate(
        [
            label_display[np.isfinite(label_display)].reshape(-1),
            plain_scaled[eval_mask].reshape(-1),
            weights13_display[eval_mask].reshape(-1),
        ]
    )
    vmin = percentile_or(depth_values, 2, 0.0)
    vmax = percentile_or(depth_values, 98, 10.0)
    if vmax <= vmin:
        vmax = vmin + 1.0

    err_max = percentile_or(
        np.concatenate(
            [
                plain_error[np.isfinite(plain_error)],
                weights13_error[np.isfinite(weights13_error)],
            ]
        ),
        98,
        1.0,
    )
    if err_max <= 0:
        err_max = 1.0

    delta_abs = percentile_or(np.abs(error_delta[np.isfinite(error_delta)]), 98, 1.0)
    if delta_abs <= 0:
        delta_abs = 1.0

    rgb = Image.open(rgb_path).convert("RGB")
    index = int(row["index"])
    output_path = output_dir / "{}_index_{:04d}_plain_medianscaled_vs_weights13_raw.png".format(
        selected.role, index
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 4, figsize=(22, 10), constrained_layout=True)
    fig.suptitle(
        "{} sample index {} | {} median-scaled a1={:.3f}, abs_rel={:.3f} | {} raw a1={:.3f}, abs_rel={:.3f}".format(
            selected.role.title(),
            index,
            plain_name,
            plain_metrics["a1"],
            plain_metrics["abs_rel"],
            weights13_name,
            weights13_metrics["a1"],
            weights13_metrics["abs_rel"],
        ),
        fontsize=13,
    )

    axes[0, 0].imshow(rgb)
    axes[0, 0].set_title("RGB")
    im = axes[0, 1].imshow(label_display, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[0, 1].set_title("Dense LiDAR label")
    fig.colorbar(im, ax=axes[0, 1], fraction=0.046, pad=0.04)
    im = axes[0, 2].imshow(plain_scaled, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[0, 2].set_title("{} median-scaled".format(plain_name))
    fig.colorbar(im, ax=axes[0, 2], fraction=0.046, pad=0.04)
    im = axes[0, 3].imshow(weights13_display, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[0, 3].set_title("{} raw".format(weights13_name))
    fig.colorbar(im, ax=axes[0, 3], fraction=0.046, pad=0.04)

    axes[1, 0].imshow(eval_mask, cmap="gray")
    axes[1, 0].set_title("Valid eval mask ({:.1%})".format(eval_mask.mean()))
    im = axes[1, 1].imshow(plain_error, cmap="inferno", vmin=0.0, vmax=err_max)
    axes[1, 1].set_title("{} median-scaled abs error".format(plain_name))
    fig.colorbar(im, ax=axes[1, 1], fraction=0.046, pad=0.04)
    im = axes[1, 2].imshow(weights13_error, cmap="inferno", vmin=0.0, vmax=err_max)
    axes[1, 2].set_title("{} raw abs error".format(weights13_name))
    fig.colorbar(im, ax=axes[1, 2], fraction=0.046, pad=0.04)
    im = axes[1, 3].imshow(error_delta, cmap="coolwarm", vmin=-delta_abs, vmax=delta_abs)
    axes[1, 3].set_title("Error delta: weights_13 raw - Plain scaled")
    fig.colorbar(im, ax=axes[1, 3], fraction=0.046, pad=0.04)

    for ax in axes.ravel():
        ax.axis("off")
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return {
        "role": selected.role,
        "index": index,
        "rgb_rel": row["rgb_rel"],
        "panel_path": str(output_path),
        "plain_median_scale_ratio": plain_scale,
        "plain_median_scaled_abs_rel": plain_metrics["abs_rel"],
        "plain_median_scaled_a1": plain_metrics["a1"],
        "weights13_raw_abs_rel": weights13_metrics["abs_rel"],
        "weights13_raw_a1": weights13_metrics["a1"],
        "weights13_raw_minus_plain_scaled_abs_rel": (
            weights13_metrics["abs_rel"] - plain_metrics["abs_rel"]
        ),
        "weights13_raw_minus_plain_scaled_a1": weights13_metrics["a1"] - plain_metrics["a1"],
    }


def write_outputs(output_dir, summaries, split):
    json_path = output_dir / "{}_plain_medianscaled_vs_weights13_summary.json".format(split)
    csv_path = output_dir / "{}_plain_medianscaled_vs_weights13_summary.csv".format(split)
    with json_path.open("w", encoding="utf-8") as fp:
        json.dump(summaries, fp, indent=2)
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)
    return json_path, csv_path


def parse_args():
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Render Plain Citrus median-scaled versus Hybrid weights_13 raw panels."
    )
    parser.add_argument("--split", choices=["val", "test"], required=True)
    parser.add_argument("--phase2_per_sample", type=Path, required=True)
    parser.add_argument(
        "--dataset_workspace",
        type=Path,
        default=root / "citrus_project" / "dataset_workspace",
    )
    parser.add_argument(
        "--plain_weights",
        type=Path,
        default=(
            root
            / "citrus_project"
            / "milestones"
            / "04_lightweight_vegetation_improvement"
            / "levinson"
            / "snapshots"
            / "00_plain_citrus_baseline"
            / "checkpoint"
        ),
    )
    parser.add_argument("--weights13", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--selection_metric", default="median_scaled_a1")
    parser.add_argument("--model", default="lite-mono")
    parser.add_argument("--plain_name", default="Plain Citrus")
    parser.add_argument("--weights13_name", default="Hybrid weights_13")
    parser.add_argument("--no_cuda", action="store_true")
    parser.add_argument("--min_depth", type=float, default=0.1)
    parser.add_argument("--max_depth", type=float, default=100.0)
    parser.add_argument("--eval_min_depth", type=float, default=1e-3)
    parser.add_argument("--eval_max_depth", type=float, default=80.0)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_rows(args.phase2_per_sample.resolve())
    selected = select_rows(rows, args.selection_metric)

    plain_model = load_lite_mono_model(
        args.plain_weights.resolve(),
        args.model,
        args.no_cuda,
        args.min_depth,
        args.max_depth,
    )
    weights13_model = load_lite_mono_model(
        args.weights13.resolve(),
        args.model,
        args.no_cuda,
        args.min_depth,
        args.max_depth,
    )

    output_dir = args.output_dir.resolve()
    summaries = [
        render_comparison(
            selected=item,
            workspace_dir=args.dataset_workspace.resolve(),
            output_dir=output_dir,
            plain_model=plain_model,
            weights13_model=weights13_model,
            plain_name=args.plain_name,
            weights13_name=args.weights13_name,
            eval_min_depth=args.eval_min_depth,
            eval_max_depth=args.eval_max_depth,
        )
        for item in selected
    ]
    json_path, csv_path = write_outputs(output_dir, summaries, args.split)
    print("Wrote", json_path)
    print("Wrote", csv_path)
    for item in summaries:
        print("Panel:", item["panel_path"])


if __name__ == "__main__":
    main()
