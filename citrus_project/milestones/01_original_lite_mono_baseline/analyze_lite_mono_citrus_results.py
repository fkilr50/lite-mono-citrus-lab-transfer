import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from evaluate_lite_mono_citrus import (
    compute_depth_errors_np,
    load_lite_mono_model,
    load_npz_array,
    repo_root,
    run_lite_mono_inference,
)


HIGHER_IS_BETTER = {"a1", "a2", "a3", "median_scaled_a1", "median_scaled_a2", "median_scaled_a3"}


class SelectedSample(NamedTuple):
    role: str
    row: Dict[str, str]
    metric_value: float


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def metric_value(row: Dict[str, str], metric_name: str) -> float:
    value = row.get(metric_name)
    if value is None or value == "":
        raise KeyError(f"Metric column not found or empty: {metric_name}")
    return float(value)


def select_samples(rows: List[Dict[str, str]], metric_name: str) -> List[SelectedSample]:
    finite_rows = [
        (row, metric_value(row, metric_name))
        for row in rows
        if np.isfinite(metric_value(row, metric_name))
    ]
    if not finite_rows:
        raise ValueError(f"No finite values found for {metric_name}")

    values = np.array([value for _, value in finite_rows], dtype=np.float64)
    median_value = float(np.median(values))
    higher_is_better = metric_name in HIGHER_IS_BETTER

    best_row, best_value = max(finite_rows, key=lambda item: item[1]) if higher_is_better else min(finite_rows, key=lambda item: item[1])
    worst_row, worst_value = min(finite_rows, key=lambda item: item[1]) if higher_is_better else max(finite_rows, key=lambda item: item[1])
    typical_row, typical_value = min(
        finite_rows, key=lambda item: abs(item[1] - median_value)
    )

    return [
        SelectedSample("good", best_row, best_value),
        SelectedSample("typical", typical_row, typical_value),
        SelectedSample("bad", worst_row, worst_value),
    ]


def masked_depth_values(*arrays: np.ndarray, valid_mask: np.ndarray) -> np.ndarray:
    values = []
    for array in arrays:
        current = array[valid_mask]
        current = current[np.isfinite(current)]
        if current.size:
            values.append(current)
    if not values:
        return np.array([], dtype=np.float32)
    return np.concatenate(values)


def safe_percentile(values: np.ndarray, percentile: float, fallback: float) -> float:
    if values.size == 0:
        return fallback
    value = float(np.percentile(values, percentile))
    if not np.isfinite(value):
        return fallback
    return value


def render_panel(
    sample: SelectedSample,
    workspace_dir: Path,
    output_dir: Path,
    model,
    eval_min_depth: float,
    eval_max_depth: float,
) -> Dict[str, object]:
    row = sample.row
    rgb_path = workspace_dir / row["rgb_rel"]
    dense_path = workspace_dir / row["dense_rel"]
    mask_path = workspace_dir / row["valid_mask_rel"]

    dense = load_npz_array(dense_path).astype(np.float32)
    valid_mask = load_npz_array(mask_path) > 0
    pred_raw, _ = run_lite_mono_inference(
        rgb_path=rgb_path,
        label_shape=dense.shape,
        model=model,
        print_details=False,
    )

    scale_ratio = float(row["scale_ratio"])
    pred_scaled = pred_raw * scale_ratio
    eval_mask = (
        valid_mask
        & np.isfinite(dense)
        & (dense > eval_min_depth)
        & (dense < eval_max_depth)
        & np.isfinite(pred_raw)
        & (pred_raw > 0)
    )

    gt_eval = dense[eval_mask].astype(np.float64)
    raw_eval = np.clip(pred_raw[eval_mask], eval_min_depth, eval_max_depth).astype(
        np.float64
    )
    scaled_eval = np.clip(
        pred_scaled[eval_mask], eval_min_depth, eval_max_depth
    ).astype(np.float64)
    raw_metrics = compute_depth_errors_np(gt_eval, raw_eval)
    scaled_metrics = compute_depth_errors_np(gt_eval, scaled_eval)

    abs_error = np.full(dense.shape, np.nan, dtype=np.float32)
    abs_error[eval_mask] = np.abs(pred_scaled[eval_mask] - dense[eval_mask])
    label_display = np.where(eval_mask, dense, np.nan)

    depth_values = masked_depth_values(
        dense, pred_scaled, valid_mask=eval_mask
    )
    vmin = safe_percentile(depth_values, 2, 0.0)
    vmax = safe_percentile(depth_values, 98, 10.0)
    if vmax <= vmin:
        vmax = vmin + 1.0
    error_values = abs_error[np.isfinite(abs_error)]
    err_max = safe_percentile(error_values, 98, 1.0)
    if err_max <= 0:
        err_max = 1.0

    rgb = Image.open(rgb_path).convert("RGB")
    index = int(row["index"])
    output_name = (
        f"{sample.role}_index_{index:04d}_"
        f"median_scaled_a1_{scaled_metrics['a1']:.3f}.png"
    )
    output_path = output_dir / output_name

    fig, axes = plt.subplots(2, 3, figsize=(18, 9), constrained_layout=True)
    fig.suptitle(
        f"{sample.role.title()} sample, index {index}: "
        f"median-scaled a1={scaled_metrics['a1']:.3f}, "
        f"abs_rel={scaled_metrics['abs_rel']:.3f}, "
        f"scale={scale_ratio:.3f}",
        fontsize=14,
    )

    axes[0, 0].imshow(rgb)
    axes[0, 0].set_title("RGB input")

    im = axes[0, 1].imshow(pred_raw, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[0, 1].set_title("Prediction: raw depth (m)")
    fig.colorbar(im, ax=axes[0, 1], fraction=0.046, pad=0.04)

    im = axes[0, 2].imshow(pred_scaled, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[0, 2].set_title("Prediction: median-scaled depth (m)")
    fig.colorbar(im, ax=axes[0, 2], fraction=0.046, pad=0.04)

    im = axes[1, 0].imshow(label_display, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[1, 0].set_title("Dense LiDAR label on valid pixels (m)")
    fig.colorbar(im, ax=axes[1, 0], fraction=0.046, pad=0.04)

    axes[1, 1].imshow(eval_mask, cmap="gray")
    axes[1, 1].set_title(f"Evaluation valid mask ({eval_mask.mean():.1%} pixels)")

    im = axes[1, 2].imshow(abs_error, cmap="inferno", vmin=0.0, vmax=err_max)
    axes[1, 2].set_title("Absolute error after median scaling (m)")
    fig.colorbar(im, ax=axes[1, 2], fraction=0.046, pad=0.04)

    for ax in axes.ravel():
        ax.axis("off")

    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return {
        "role": sample.role,
        "index": index,
        "rgb_rel": row["rgb_rel"],
        "dense_rel": row["dense_rel"],
        "valid_mask_rel": row["valid_mask_rel"],
        "panel_path": str(output_path),
        "valid_fraction": float(eval_mask.mean()),
        "scale_ratio": scale_ratio,
        "raw_abs_rel": raw_metrics["abs_rel"],
        "raw_a1": raw_metrics["a1"],
        "median_scaled_abs_rel": scaled_metrics["abs_rel"],
        "median_scaled_a1": scaled_metrics["a1"],
        "display_depth_min_m": vmin,
        "display_depth_max_m": vmax,
        "error_display_max_m": err_max,
    }


def write_selection_outputs(output_dir: Path, prefix: str, summaries: List[Dict[str, object]]) -> Tuple[Path, Path]:
    json_path = output_dir / f"{prefix}_selection_summary.json"
    csv_path = output_dir / f"{prefix}_selection_summary.csv"

    with json_path.open("w", encoding="utf-8") as fp:
        json.dump(summaries, fp, indent=2)
        fp.write("\n")

    fieldnames = [
        "role",
        "index",
        "rgb_rel",
        "dense_rel",
        "valid_mask_rel",
        "panel_path",
        "valid_fraction",
        "scale_ratio",
        "raw_abs_rel",
        "raw_a1",
        "median_scaled_abs_rel",
        "median_scaled_a1",
        "display_depth_min_m",
        "display_depth_max_m",
        "error_display_max_m",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    return json_path, csv_path


def parse_args() -> argparse.Namespace:
    root = repo_root()
    milestone_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Select good/typical/bad Citrus baseline samples and render visual panels."
        )
    )
    parser.add_argument("--split", choices=["val", "test"], default="val")
    parser.add_argument(
        "--results_dir",
        type=Path,
        default=milestone_dir / "results",
        help="Folder containing full per-sample CSV outputs.",
    )
    parser.add_argument(
        "--dataset_workspace",
        type=Path,
        default=root / "citrus_project" / "dataset_workspace",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=milestone_dir / "visuals",
        help="Folder where visual panels and selection summaries are saved.",
    )
    parser.add_argument(
        "--metric",
        default="median_scaled_a1",
        help="Per-sample CSV metric used for good/typical/bad selection.",
    )
    parser.add_argument(
        "--model",
        default="lite-mono",
        choices=["lite-mono", "lite-mono-small", "lite-mono-tiny", "lite-mono-8m"],
    )
    parser.add_argument(
        "--weights_folder",
        type=Path,
        default=root / "weights" / "lite-mono",
    )
    parser.add_argument("--no_cuda", action="store_true")
    parser.add_argument("--min_depth", type=float, default=0.1)
    parser.add_argument("--max_depth", type=float, default=100.0)
    parser.add_argument("--eval_min_depth", type=float, default=1e-3)
    parser.add_argument("--eval_max_depth", type=float, default=80.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    per_sample_path = args.results_dir.resolve() / f"{args.split}_lite-mono_full_per_sample.csv"
    rows = read_csv_rows(per_sample_path)
    selected = select_samples(rows, args.metric)

    model = load_lite_mono_model(
        weights_folder=args.weights_folder.resolve(),
        model_name=args.model,
        no_cuda=args.no_cuda,
        min_depth=args.min_depth,
        max_depth=args.max_depth,
    )

    print("Citrus baseline result visual analyzer")
    print(f"  Split:          {args.split}")
    print(f"  Rows:           {len(rows)}")
    print(f"  Selection metric: {args.metric}")
    print(f"  Device:         {model.device}")
    print(f"  Output dir:     {output_dir}")

    summaries = []
    for sample in selected:
        print(
            f"  Rendering {sample.role}: index={sample.row['index']}, "
            f"{args.metric}={sample.metric_value:.4f}"
        )
        summaries.append(
            render_panel(
                sample=sample,
                workspace_dir=args.dataset_workspace.resolve(),
                output_dir=output_dir,
                model=model,
                eval_min_depth=args.eval_min_depth,
                eval_max_depth=args.eval_max_depth,
            )
        )

    prefix = f"{args.split}_lite-mono_{args.metric}"
    json_path, csv_path = write_selection_outputs(output_dir, prefix, summaries)
    print("Saved analysis outputs")
    print(f"  Selection JSON: {json_path}")
    print(f"  Selection CSV:  {csv_path}")
    for summary in summaries:
        print(f"  Panel:          {summary['panel_path']}")


if __name__ == "__main__":
    sys.exit(main())
