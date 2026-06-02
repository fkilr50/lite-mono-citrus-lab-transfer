from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, NamedTuple, Optional

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[3]
EVALUATOR_DIR = (
    REPO_ROOT / "citrus_project" / "milestones" / "01_original_lite_mono_baseline"
)
if str(EVALUATOR_DIR) not in sys.path:
    sys.path.insert(0, str(EVALUATOR_DIR))

from evaluate_lite_mono_citrus import (  # noqa: E402
    load_lite_mono_model,
    load_npz_array,
    run_lite_mono_inference,
)


HIGHER_IS_BETTER = {
    "a1",
    "a2",
    "a3",
    "median_scaled_a1",
    "median_scaled_a2",
    "median_scaled_a3",
    "raw_a1",
    "raw_a2",
    "raw_a3",
}


class SelectedSample(NamedTuple):
    role: str
    adapted_row: Dict[str, str]
    baseline_row: Optional[Dict[str, str]]
    metric_value: float


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def finite_float(row: Dict[str, str], key: str) -> float:
    value = row.get(key, "")
    if value == "":
        return float("nan")
    return float(value)


def finite_rows(rows: Iterable[Dict[str, str]], metric: str):
    for row in rows:
        value = finite_float(row, metric)
        if np.isfinite(value):
            yield row, value


def select_samples(
    adapted_rows: List[Dict[str, str]],
    baseline_by_rgb: Dict[str, Dict[str, str]],
    metric: str,
) -> List[SelectedSample]:
    pairs = list(finite_rows(adapted_rows, metric))
    if not pairs:
        raise ValueError(f"No finite adapted metric values for {metric}")

    values = np.array([value for _, value in pairs], dtype=np.float64)
    median_value = float(np.median(values))
    higher_is_better = metric in HIGHER_IS_BETTER

    good_row, good_value = (
        max(pairs, key=lambda item: item[1])
        if higher_is_better
        else min(pairs, key=lambda item: item[1])
    )
    bad_row, bad_value = (
        min(pairs, key=lambda item: item[1])
        if higher_is_better
        else max(pairs, key=lambda item: item[1])
    )
    typical_row, typical_value = min(
        pairs, key=lambda item: abs(item[1] - median_value)
    )

    selected = [
        ("adapted_good", good_row, good_value),
        ("adapted_typical", typical_row, typical_value),
        ("adapted_bad", bad_row, bad_value),
    ]

    drop_pairs = []
    for adapted_row, _ in pairs:
        baseline_row = baseline_by_rgb.get(adapted_row["rgb_rel"])
        if baseline_row is None:
            continue
        baseline_value = finite_float(baseline_row, metric)
        adapted_value = finite_float(adapted_row, metric)
        if not (np.isfinite(baseline_value) and np.isfinite(adapted_value)):
            continue
        drop = baseline_value - adapted_value if higher_is_better else adapted_value - baseline_value
        drop_pairs.append((adapted_row, drop))

    if drop_pairs:
        drop_row, drop_value = max(drop_pairs, key=lambda item: item[1])
        selected.append(("largest_drop_vs_original", drop_row, drop_value))

    results = []
    seen = set()
    for role, row, value in selected:
        key = row["rgb_rel"]
        if key in seen:
            continue
        seen.add(key)
        results.append(
            SelectedSample(
                role=role,
                adapted_row=row,
                baseline_row=baseline_by_rgb.get(key),
                metric_value=float(value),
            )
        )
    return results


def metric_label(row: Optional[Dict[str, str]], prefix: str) -> str:
    if row is None:
        return f"{prefix}: metrics unavailable"
    return (
        f"{prefix}: a1={finite_float(row, 'median_scaled_a1'):.3f}, "
        f"abs_rel={finite_float(row, 'median_scaled_abs_rel'):.3f}, "
        f"scale={finite_float(row, 'scale_ratio'):.3f}"
    )


def safe_percentile(values: np.ndarray, percentile: float, fallback: float) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return fallback
    value = float(np.percentile(finite, percentile))
    return value if np.isfinite(value) else fallback


def model_prediction(
    rgb_path: Path,
    dense_shape,
    row: Dict[str, str],
    model,
    eval_min_depth: float,
    eval_max_depth: float,
):
    pred_raw, _ = run_lite_mono_inference(
        rgb_path=rgb_path,
        label_shape=dense_shape,
        model=model,
        print_details=False,
    )
    scale_ratio = finite_float(row, "scale_ratio")
    pred_scaled = pred_raw * scale_ratio
    pred_scaled = np.clip(pred_scaled, eval_min_depth, eval_max_depth)
    return pred_raw, pred_scaled


def render_comparison(
    sample: SelectedSample,
    workspace_dir: Path,
    output_dir: Path,
    baseline_model,
    adapted_model,
    eval_min_depth: float,
    eval_max_depth: float,
) -> Dict[str, object]:
    row = sample.adapted_row
    baseline_row = sample.baseline_row
    rgb_path = workspace_dir / row["rgb_rel"]
    dense = load_npz_array(workspace_dir / row["dense_rel"]).astype(np.float32)
    valid_mask = load_npz_array(workspace_dir / row["valid_mask_rel"]) > 0

    eval_mask = (
        valid_mask
        & np.isfinite(dense)
        & (dense > eval_min_depth)
        & (dense < eval_max_depth)
    )

    if baseline_row is not None:
        baseline_raw, baseline_scaled = model_prediction(
            rgb_path,
            dense.shape,
            baseline_row,
            baseline_model,
            eval_min_depth,
            eval_max_depth,
        )
    else:
        baseline_raw = np.full(dense.shape, np.nan, dtype=np.float32)
        baseline_scaled = np.full(dense.shape, np.nan, dtype=np.float32)

    adapted_raw, adapted_scaled = model_prediction(
        rgb_path,
        dense.shape,
        row,
        adapted_model,
        eval_min_depth,
        eval_max_depth,
    )

    baseline_error = np.full(dense.shape, np.nan, dtype=np.float32)
    adapted_error = np.full(dense.shape, np.nan, dtype=np.float32)
    baseline_error[eval_mask] = np.abs(baseline_scaled[eval_mask] - dense[eval_mask])
    adapted_error[eval_mask] = np.abs(adapted_scaled[eval_mask] - dense[eval_mask])
    label_display = np.where(eval_mask, dense, np.nan)

    depth_values = np.concatenate(
        [
            label_display[np.isfinite(label_display)],
            baseline_scaled[eval_mask & np.isfinite(baseline_scaled)],
            adapted_scaled[eval_mask & np.isfinite(adapted_scaled)],
        ]
    )
    vmin = safe_percentile(depth_values, 2, 0.0)
    vmax = safe_percentile(depth_values, 98, 10.0)
    if vmax <= vmin:
        vmax = vmin + 1.0

    error_values = np.concatenate(
        [
            baseline_error[np.isfinite(baseline_error)],
            adapted_error[np.isfinite(adapted_error)],
        ]
    )
    err_max = safe_percentile(error_values, 98, 1.0)
    if err_max <= 0:
        err_max = 1.0

    index = int(row["index"])
    output_path = output_dir / f"{sample.role}_index_{index:04d}_comparison.png"

    rgb = Image.open(rgb_path).convert("RGB")
    fig, axes = plt.subplots(3, 3, figsize=(18, 13), constrained_layout=True)
    fig.suptitle(
        f"{sample.role.replace('_', ' ').title()} | index {index}\n"
        f"{metric_label(baseline_row, 'Original')} | {metric_label(row, 'Adapted')}",
        fontsize=13,
    )

    axes[0, 0].imshow(rgb)
    axes[0, 0].set_title("RGB input")
    im = axes[0, 1].imshow(label_display, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[0, 1].set_title("LiDAR depth label (valid pixels)")
    fig.colorbar(im, ax=axes[0, 1], fraction=0.046, pad=0.04)
    axes[0, 2].imshow(eval_mask, cmap="gray")
    axes[0, 2].set_title(f"Evaluation mask ({eval_mask.mean():.1%})")

    im = axes[1, 0].imshow(baseline_raw, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[1, 0].set_title("Original raw prediction")
    fig.colorbar(im, ax=axes[1, 0], fraction=0.046, pad=0.04)
    im = axes[1, 1].imshow(baseline_scaled, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[1, 1].set_title("Original median-scaled prediction")
    fig.colorbar(im, ax=axes[1, 1], fraction=0.046, pad=0.04)
    im = axes[1, 2].imshow(baseline_error, cmap="inferno", vmin=0.0, vmax=err_max)
    axes[1, 2].set_title("Original absolute error")
    fig.colorbar(im, ax=axes[1, 2], fraction=0.046, pad=0.04)

    im = axes[2, 0].imshow(adapted_raw, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[2, 0].set_title("Adapted raw prediction")
    fig.colorbar(im, ax=axes[2, 0], fraction=0.046, pad=0.04)
    im = axes[2, 1].imshow(adapted_scaled, cmap="magma_r", vmin=vmin, vmax=vmax)
    axes[2, 1].set_title("Adapted median-scaled prediction")
    fig.colorbar(im, ax=axes[2, 1], fraction=0.046, pad=0.04)
    im = axes[2, 2].imshow(adapted_error, cmap="inferno", vmin=0.0, vmax=err_max)
    axes[2, 2].set_title("Adapted absolute error")
    fig.colorbar(im, ax=axes[2, 2], fraction=0.046, pad=0.04)

    for ax in axes.ravel():
        ax.axis("off")

    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return {
        "role": sample.role,
        "index": index,
        "rgb_rel": row["rgb_rel"],
        "panel_path": str(output_path),
        "valid_fraction": float(eval_mask.mean()),
        "original_median_scaled_abs_rel": finite_float(
            baseline_row, "median_scaled_abs_rel"
        )
        if baseline_row is not None
        else float("nan"),
        "original_median_scaled_a1": finite_float(baseline_row, "median_scaled_a1")
        if baseline_row is not None
        else float("nan"),
        "adapted_median_scaled_abs_rel": finite_float(row, "median_scaled_abs_rel"),
        "adapted_median_scaled_a1": finite_float(row, "median_scaled_a1"),
        "adapted_selection_metric_value": sample.metric_value,
    }


def write_outputs(output_dir: Path, summaries: List[Dict[str, object]]) -> None:
    json_path = output_dir / "original_vs_adapted_selection_summary.json"
    csv_path = output_dir / "original_vs_adapted_selection_summary.csv"
    with json_path.open("w", encoding="utf-8") as fp:
        json.dump(summaries, fp, indent=2)
        fp.write("\n")
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)
    print(f"Saved summary JSON: {json_path}")
    print(f"Saved summary CSV:  {csv_path}")


def parse_args() -> argparse.Namespace:
    run_dir = (
        REPO_ROOT
        / "citrus_project"
        / "milestones"
        / "03_self_supervised_adaptation"
        / "runs"
        / "citrus_ss_seed0_decoderonly_lowdepthlr_1epoch_1000steps"
    )
    parser = argparse.ArgumentParser(
        description="Render original Lite-Mono versus adapted checkpoint comparison panels."
    )
    parser.add_argument(
        "--adapted_results",
        type=Path,
        default=run_dir / "eval_val100_weights_0" / "val_lite-mono_max100_per_sample.csv",
    )
    parser.add_argument(
        "--baseline_results",
        type=Path,
        default=(
            REPO_ROOT
            / "citrus_project"
            / "milestones"
            / "01_original_lite_mono_baseline"
            / "results"
            / "val_lite-mono_full_per_sample.csv"
        ),
    )
    parser.add_argument(
        "--dataset_workspace",
        type=Path,
        default=REPO_ROOT / "citrus_project" / "dataset_workspace",
    )
    parser.add_argument(
        "--baseline_weights_folder",
        type=Path,
        default=REPO_ROOT / "weights" / "lite-mono",
    )
    parser.add_argument(
        "--adapted_weights_folder",
        type=Path,
        default=run_dir / "models" / "weights_0",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=run_dir / "visual_compare_original_vs_adapted_val100_weights_0",
    )
    parser.add_argument("--metric", default="median_scaled_a1")
    parser.add_argument("--model", default="lite-mono")
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

    adapted_rows = read_csv_rows(args.adapted_results.resolve())
    baseline_rows = read_csv_rows(args.baseline_results.resolve())
    baseline_by_rgb = {row["rgb_rel"]: row for row in baseline_rows}
    selected = select_samples(adapted_rows, baseline_by_rgb, args.metric)

    print("Original vs adapted visual comparison")
    print(f"  Adapted rows:   {len(adapted_rows)}")
    print(f"  Baseline rows:  {len(baseline_rows)}")
    print(f"  Metric:         {args.metric}")
    print(f"  Output dir:     {output_dir}")

    baseline_model = load_lite_mono_model(
        weights_folder=args.baseline_weights_folder.resolve(),
        model_name=args.model,
        no_cuda=args.no_cuda,
        min_depth=args.min_depth,
        max_depth=args.max_depth,
    )
    adapted_model = load_lite_mono_model(
        weights_folder=args.adapted_weights_folder.resolve(),
        model_name=args.model,
        no_cuda=args.no_cuda,
        min_depth=args.min_depth,
        max_depth=args.max_depth,
    )

    summaries = []
    for sample in selected:
        print(
            f"  Rendering {sample.role}: index={sample.adapted_row['index']}, "
            f"{args.metric}={finite_float(sample.adapted_row, args.metric):.4f}"
        )
        summaries.append(
            render_comparison(
                sample=sample,
                workspace_dir=args.dataset_workspace.resolve(),
                output_dir=output_dir,
                baseline_model=baseline_model,
                adapted_model=adapted_model,
                eval_min_depth=args.eval_min_depth,
                eval_max_depth=args.eval_max_depth,
            )
        )

    write_outputs(output_dir, summaries)
    for summary in summaries:
        print(f"  Panel: {summary['panel_path']}")


if __name__ == "__main__":
    sys.exit(main())
