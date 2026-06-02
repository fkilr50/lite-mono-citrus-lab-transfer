import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple

import numpy as np
from PIL import Image


DEPTH_METRIC_NAMES = ("abs_rel", "sq_rel", "rmse", "rmse_log", "a1", "a2", "a3")


class LiteMonoModel(NamedTuple):
    encoder: object
    depth_decoder: object
    disp_to_depth: Callable
    device: object
    model_info: Dict[str, object]
    feed_height: int
    feed_width: int
    min_depth: float
    max_depth: float


class EvaluationResult(NamedTuple):
    index: int
    rgb_rel: str
    dense_rel: str
    valid_mask_rel: str
    valid_count: int
    valid_fraction: float
    gt_median: float
    pred_median: float
    scale_ratio: Optional[float]
    sample_wall_seconds: float
    model_forward_seconds: Optional[float]
    raw_metrics: Dict[str, float]
    scaled_metrics: Optional[Dict[str, float]]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_npz_array(path: Path) -> np.ndarray:
    with np.load(path) as data:
        if "arr_0" in data.files:
            return data["arr_0"]
        if len(data.files) == 1:
            return data[data.files[0]]
        raise ValueError(f"{path} contains multiple arrays and no arr_0 key: {data.files}")


def load_manifest(csv_path: Path) -> Dict[str, Dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    return {row["rgb_rel"]: row for row in rows}


def load_split_pairs(split_path: Path) -> List[Tuple[str, str]]:
    pairs = []
    with split_path.open(encoding="utf-8") as fp:
        for line_number, line in enumerate(fp, start=1):
            parts = line.strip().split()
            if not parts:
                continue
            if len(parts) != 2:
                raise ValueError(
                    f"{split_path}:{line_number} expected 2 columns, got {len(parts)}"
                )
            pairs.append((parts[0], parts[1]))
    return pairs


def finite_stats(values: np.ndarray) -> Dict[str, object]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {"count": 0, "min": None, "median": None, "max": None}
    return {
        "count": int(finite.size),
        "min": float(np.min(finite)),
        "median": float(np.median(finite)),
        "max": float(np.max(finite)),
    }


def format_stats(stats: Dict[str, object]) -> str:
    if stats["count"] == 0:
        return "count=0, min=n/a, median=n/a, max=n/a"
    return (
        f"count={stats['count']}, "
        f"min={stats['min']:.6f}, "
        f"median={stats['median']:.6f}, "
        f"max={stats['max']:.6f}"
    )


def compute_depth_errors_np(gt_depth: np.ndarray, pred_depth: np.ndarray) -> Dict[str, float]:
    thresh = np.maximum(gt_depth / pred_depth, pred_depth / gt_depth)
    a1 = float((thresh < 1.25).mean())
    a2 = float((thresh < 1.25**2).mean())
    a3 = float((thresh < 1.25**3).mean())

    rmse = float(np.sqrt(np.mean((gt_depth - pred_depth) ** 2)))
    rmse_log = float(
        np.sqrt(np.mean((np.log(gt_depth) - np.log(pred_depth)) ** 2))
    )
    abs_rel = float(np.mean(np.abs(gt_depth - pred_depth) / gt_depth))
    sq_rel = float(np.mean(((gt_depth - pred_depth) ** 2) / gt_depth))

    return dict(zip(DEPTH_METRIC_NAMES, (abs_rel, sq_rel, rmse, rmse_log, a1, a2, a3)))


def format_depth_metrics(metrics: Dict[str, float]) -> str:
    return ", ".join(f"{name}={metrics[name]:.4f}" for name in DEPTH_METRIC_NAMES)


def mean_depth_metrics(rows: List[Dict[str, float]]) -> Dict[str, float]:
    return {
        name: float(np.mean([row[name] for row in rows]))
        for name in DEPTH_METRIC_NAMES
    }


def build_aggregate_summary(
    results: List[EvaluationResult],
    requested_count: int,
    timing: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    summary: Dict[str, object] = {
        "requested_samples": requested_count,
        "samples_with_metrics": len(results),
        "averaging_rule": "per_image_metric_mean",
    }
    if timing is not None:
        summary["timing"] = timing
    if not results:
        return summary

    scale_ratios = [
        result.scale_ratio
        for result in results
        if result.scale_ratio is not None and np.isfinite(result.scale_ratio)
    ]
    scaled_rows = [
        result.scaled_metrics for result in results if result.scaled_metrics is not None
    ]

    summary.update(
        {
            "total_valid_pixels": int(sum(result.valid_count for result in results)),
            "mean_valid_fraction": float(
                np.mean([result.valid_fraction for result in results])
            ),
            "median_scale_ratio": (
                float(np.median(scale_ratios)) if scale_ratios else None
            ),
            "mean_scale_ratio": float(np.mean(scale_ratios)) if scale_ratios else None,
            "mean_raw_metrics": mean_depth_metrics(
                [result.raw_metrics for result in results]
            ),
            "mean_median_scaled_metrics": (
                mean_depth_metrics(scaled_rows) if scaled_rows else None
            ),
        }
    )
    return summary


def rate(count: int, seconds: Optional[float]) -> Optional[float]:
    if seconds is None or seconds <= 0:
        return None
    return count / seconds


def count_parameters(module: object, trainable_only: bool = False) -> int:
    params = module.parameters()
    if trainable_only:
        return int(sum(param.numel() for param in params if param.requires_grad))
    return int(sum(param.numel() for param in params))


def size_info(path: Path) -> Dict[str, float]:
    size_bytes = path.stat().st_size
    return {
        "bytes": int(size_bytes),
        "megabytes": size_bytes / (1024 * 1024),
    }


def build_model_info(
    encoder: object,
    depth_decoder: object,
    encoder_path: Path,
    decoder_path: Path,
) -> Dict[str, object]:
    encoder_params = count_parameters(encoder)
    decoder_params = count_parameters(depth_decoder)
    encoder_trainable = count_parameters(encoder, trainable_only=True)
    decoder_trainable = count_parameters(depth_decoder, trainable_only=True)
    total_params = encoder_params + decoder_params
    total_trainable = encoder_trainable + decoder_trainable
    encoder_size = size_info(encoder_path)
    decoder_size = size_info(decoder_path)
    total_checkpoint_bytes = encoder_size["bytes"] + decoder_size["bytes"]

    return {
        "encoder_parameters": encoder_params,
        "depth_decoder_parameters": decoder_params,
        "total_parameters": total_params,
        "total_parameters_millions": total_params / 1_000_000,
        "encoder_trainable_parameters": encoder_trainable,
        "depth_decoder_trainable_parameters": decoder_trainable,
        "total_trainable_parameters": total_trainable,
        "total_trainable_parameters_millions": total_trainable / 1_000_000,
        "encoder_checkpoint": encoder_size,
        "depth_decoder_checkpoint": decoder_size,
        "total_checkpoint": {
            "bytes": int(total_checkpoint_bytes),
            "megabytes": total_checkpoint_bytes / (1024 * 1024),
        },
        "parameter_note": (
            "Counts include the Lite-Mono encoder and depth decoder used for depth "
            "inference; they do not include the training-only pose network."
        ),
    }


def build_timing_summary(
    results: List[EvaluationResult],
    requested_count: int,
    model_load_seconds: Optional[float],
    evaluation_loop_seconds: float,
    total_run_seconds: float,
) -> Dict[str, object]:
    model_forward_times = [
        result.model_forward_seconds
        for result in results
        if result.model_forward_seconds is not None
    ]
    total_model_forward_seconds = (
        float(np.sum(model_forward_times)) if model_forward_times else None
    )

    return {
        "model_load_seconds": model_load_seconds,
        "evaluation_loop_seconds": evaluation_loop_seconds,
        "total_run_seconds": total_run_seconds,
        "requested_samples_per_second": rate(requested_count, evaluation_loop_seconds),
        "metric_samples_per_second": rate(len(results), evaluation_loop_seconds),
        "mean_sample_wall_seconds": (
            float(np.mean([result.sample_wall_seconds for result in results]))
            if results
            else None
        ),
        "total_model_forward_seconds": total_model_forward_seconds,
        "mean_model_forward_seconds": (
            float(np.mean(model_forward_times)) if model_forward_times else None
        ),
        "model_forward_fps": rate(
            len(model_forward_times), total_model_forward_seconds
        ),
        "timing_note": (
            "evaluation_loop includes image/label loading, inference, resizing, and metrics; "
            "model_forward includes encoder, decoder, disparity-depth conversion, and output resize."
        ),
    }


def result_to_csv_row(result: EvaluationResult) -> Dict[str, object]:
    row: Dict[str, object] = {
        "index": result.index,
        "rgb_rel": result.rgb_rel,
        "dense_rel": result.dense_rel,
        "valid_mask_rel": result.valid_mask_rel,
        "valid_count": result.valid_count,
        "valid_fraction": result.valid_fraction,
        "gt_median": result.gt_median,
        "pred_median": result.pred_median,
        "scale_ratio": result.scale_ratio,
        "sample_wall_seconds": result.sample_wall_seconds,
        "model_forward_seconds": result.model_forward_seconds,
        "model_forward_fps": rate(1, result.model_forward_seconds),
    }
    for name in DEPTH_METRIC_NAMES:
        row[f"raw_{name}"] = result.raw_metrics[name]
        row[f"median_scaled_{name}"] = (
            result.scaled_metrics[name] if result.scaled_metrics is not None else None
        )
    return row


def save_results(
    output_dir: Path,
    args: argparse.Namespace,
    model: Optional[LiteMonoModel],
    workspace_dir: Path,
    prepared_dir: Path,
    results: List[EvaluationResult],
    requested_count: int,
    split_count: int,
    timing: Dict[str, object],
) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    sample_tag = "full" if args.max_samples <= 0 else f"max{args.max_samples}"
    model_tag = args.model.replace("/", "_")
    prefix = f"{args.split}_{model_tag}_{sample_tag}"
    summary_path = output_dir / f"{prefix}_summary.json"
    per_sample_path = output_dir / f"{prefix}_per_sample.csv"

    summary = build_aggregate_summary(results, requested_count, timing=timing)
    summary.update(
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "split": args.split,
            "split_samples": split_count,
            "max_samples_arg": args.max_samples,
            "model": args.model,
            "weights_folder": str(args.weights_folder.resolve()),
            "device": str(model.device) if model is not None else None,
            "model_info": model.model_info if model is not None else None,
            "feed_width": model.feed_width if model is not None else None,
            "feed_height": model.feed_height if model is not None else None,
            "model_min_depth": args.min_depth,
            "model_max_depth": args.max_depth,
            "eval_min_depth": args.eval_min_depth,
            "eval_max_depth": args.eval_max_depth,
            "dataset_workspace": str(workspace_dir),
            "prepared_dataset": str(prepared_dir),
        }
    )

    with summary_path.open("w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2)
        fp.write("\n")

    rows = [result_to_csv_row(result) for result in results]
    fieldnames = [
        "index",
        "rgb_rel",
        "dense_rel",
        "valid_mask_rel",
        "valid_count",
        "valid_fraction",
        "gt_median",
        "pred_median",
        "scale_ratio",
        "sample_wall_seconds",
        "model_forward_seconds",
        "model_forward_fps",
    ]
    for name in DEPTH_METRIC_NAMES:
        fieldnames.append(f"raw_{name}")
        fieldnames.append(f"median_scaled_{name}")

    with per_sample_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return summary_path, per_sample_path


def ensure_repo_imports(root: Path) -> None:
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def load_lite_mono_model(
    weights_folder: Path,
    model_name: str,
    no_cuda: bool,
    min_depth: float,
    max_depth: float,
) -> LiteMonoModel:
    import torch

    root = repo_root()
    ensure_repo_imports(root)

    import networks
    from layers import disp_to_depth

    device = torch.device("cuda" if torch.cuda.is_available() and not no_cuda else "cpu")
    encoder_path = weights_folder / "encoder.pth"
    decoder_path = weights_folder / "depth.pth"

    encoder_dict = torch.load(encoder_path, map_location=device)
    decoder_dict = torch.load(decoder_path, map_location=device)
    feed_height = int(encoder_dict["height"])
    feed_width = int(encoder_dict["width"])

    encoder = networks.LiteMono(model=model_name, height=feed_height, width=feed_width)
    encoder.load_state_dict(
        {key: value for key, value in encoder_dict.items() if key in encoder.state_dict()}
    )
    encoder.to(device)
    encoder.eval()

    depth_decoder = networks.DepthDecoder(encoder.num_ch_enc, scales=range(3))
    depth_decoder.load_state_dict(
        {
            key: value
            for key, value in decoder_dict.items()
            if key in depth_decoder.state_dict()
        }
    )
    depth_decoder.to(device)
    depth_decoder.eval()
    model_info = build_model_info(
        encoder=encoder,
        depth_decoder=depth_decoder,
        encoder_path=encoder_path,
        decoder_path=decoder_path,
    )

    return LiteMonoModel(
        encoder=encoder,
        depth_decoder=depth_decoder,
        disp_to_depth=disp_to_depth,
        device=device,
        model_info=model_info,
        feed_height=feed_height,
        feed_width=feed_width,
        min_depth=min_depth,
        max_depth=max_depth,
    )


def image_to_input_tensor(image: Image.Image, model: LiteMonoModel):
    import torch
    from torchvision import transforms

    resized = image.resize((model.feed_width, model.feed_height), Image.LANCZOS)
    tensor = transforms.ToTensor()(resized).unsqueeze(0)
    return tensor.to(model.device)


def run_lite_mono_inference(
    rgb_path: Path,
    label_shape: Tuple[int, int],
    model: LiteMonoModel,
    print_details: bool,
) -> Tuple[np.ndarray, float]:
    import torch
    import torch.nn.functional as F

    with Image.open(rgb_path) as image:
        input_image = image.convert("RGB")
        original_width, original_height = input_image.size
        input_tensor = image_to_input_tensor(input_image, model)

    if getattr(model.device, "type", None) == "cuda":
        torch.cuda.synchronize(model.device)
    model_forward_start = time.perf_counter()
    with torch.no_grad():
        features = model.encoder(input_tensor)
        outputs = model.depth_decoder(features)
        raw_disp = outputs[("disp", 0)]
        scaled_disp, depth = model.disp_to_depth(
            raw_disp, model.min_depth, model.max_depth
        )
        depth_resized = F.interpolate(
            depth,
            size=label_shape,
            mode="bilinear",
            align_corners=False,
        )
    if getattr(model.device, "type", None) == "cuda":
        torch.cuda.synchronize(model.device)
    model_forward_seconds = time.perf_counter() - model_forward_start

    raw_disp_np = raw_disp.detach().cpu().numpy()
    scaled_disp_np = scaled_disp.detach().cpu().numpy()
    depth_np = depth.detach().cpu().numpy()
    depth_resized_np = depth_resized.detach().cpu().numpy()

    if print_details:
        print("  Model inference:")
        print(
            "    Input tensor: "
            f"shape={tuple(input_tensor.shape)}, "
            f"dtype={input_tensor.dtype}, "
            f"device={input_tensor.device}, "
            f"range={float(input_tensor.min()):.6f}..{float(input_tensor.max()):.6f}"
        )
        print(
            "    Original RGB size: "
            f"width={original_width}, height={original_height}; "
            f"model feed size: width={model.feed_width}, height={model.feed_height}"
        )
        print(
            "    Raw closeness level: "
            f"shape={tuple(raw_disp.shape)}, {format_stats(finite_stats(raw_disp_np))}"
        )
        print(
            "    Scaled disparity:   "
            f"shape={tuple(scaled_disp.shape)}, {format_stats(finite_stats(scaled_disp_np))}"
        )
        print(
            "    Predicted depth:    "
            f"shape={tuple(depth.shape)}, {format_stats(finite_stats(depth_np))}"
        )
        print(
            "    Resized depth:      "
            f"shape={tuple(depth_resized.shape)}, {format_stats(finite_stats(depth_resized_np))}"
        )
        print(f"    Model forward time: {model_forward_seconds:.6f} s")
    return depth_resized_np[0, 0], model_forward_seconds


def evaluate_prediction_against_label(
    dense: np.ndarray,
    valid_mask: np.ndarray,
    pred_depth: np.ndarray,
    eval_min_depth: float,
    eval_max_depth: float,
    print_details: bool,
) -> Optional[EvaluationResult]:
    eval_mask = (
        (valid_mask > 0)
        & np.isfinite(dense)
        & (dense > eval_min_depth)
        & (dense < eval_max_depth)
        & np.isfinite(pred_depth)
        & (pred_depth > 0)
    )

    valid_count = int(np.count_nonzero(eval_mask))
    valid_fraction = valid_count / dense.size
    if print_details:
        print(
            "  Evaluation mask: "
            f"{valid_count}/{dense.size} "
            f"({valid_fraction:.4%}) after valid mask and "
            f"{eval_min_depth}..{eval_max_depth} m label cap"
        )

    if valid_count == 0:
        if print_details:
            print("  Depth metrics: skipped because no valid comparison pixels remain")
        return None

    gt_eval = dense[eval_mask].astype(np.float64)
    pred_eval = pred_depth[eval_mask].astype(np.float64)
    pred_raw = np.clip(pred_eval, eval_min_depth, eval_max_depth)
    raw_metrics = compute_depth_errors_np(gt_eval, pred_raw)

    gt_median = float(np.median(gt_eval))
    pred_median = float(np.median(pred_eval))
    scale_ratio = None
    if np.isfinite(gt_median) and np.isfinite(pred_median) and pred_median > 0:
        scale_ratio = gt_median / pred_median

    ratio_text = f"{scale_ratio:.6f}" if scale_ratio is not None else "n/a"
    if print_details:
        print(
            "  Metric medians: "
            f"label={gt_median:.6f} m, raw_pred={pred_median:.6f} m, "
            f"median_scale_ratio={ratio_text}"
        )
        print(f"  Raw-scale metrics:        {format_depth_metrics(raw_metrics)}")

    if scale_ratio is None:
        if print_details:
            print("  Median-scaled metrics:    skipped because scale ratio is invalid")
        return EvaluationResult(
            index=-1,
            rgb_rel="",
            dense_rel="",
            valid_mask_rel="",
            valid_count=valid_count,
            valid_fraction=valid_fraction,
            gt_median=gt_median,
            pred_median=pred_median,
            scale_ratio=scale_ratio,
            sample_wall_seconds=0.0,
            model_forward_seconds=None,
            raw_metrics=raw_metrics,
            scaled_metrics=None,
        )

    pred_scaled = np.clip(pred_eval * scale_ratio, eval_min_depth, eval_max_depth)
    scaled_metrics = compute_depth_errors_np(gt_eval, pred_scaled)
    if print_details:
        print(f"  Median-scaled metrics:    {format_depth_metrics(scaled_metrics)}")

    return EvaluationResult(
        index=-1,
        rgb_rel="",
        dense_rel="",
        valid_mask_rel="",
        valid_count=valid_count,
        valid_fraction=valid_fraction,
        gt_median=gt_median,
        pred_median=pred_median,
        scale_ratio=scale_ratio,
        sample_wall_seconds=0.0,
        model_forward_seconds=None,
        raw_metrics=raw_metrics,
        scaled_metrics=scaled_metrics,
    )


def print_aggregate_summary(
    results: List[EvaluationResult],
    requested_count: int,
    timing: Optional[Dict[str, object]] = None,
) -> None:
    print("\nAggregate evaluation summary")
    print("  Averaging rule: per-image metric mean, matching original Lite-Mono evaluation style")
    print(f"  Requested samples:        {requested_count}")
    print(f"  Samples with metrics:     {len(results)}")

    if not results:
        print("  No valid metric rows were produced.")
        return

    total_valid_pixels = sum(result.valid_count for result in results)
    mean_valid_fraction = float(np.mean([result.valid_fraction for result in results]))
    print(f"  Total valid pixels:       {total_valid_pixels}")
    print(f"  Mean valid fraction:      {mean_valid_fraction:.4%}")

    scale_ratios = [
        result.scale_ratio
        for result in results
        if result.scale_ratio is not None and np.isfinite(result.scale_ratio)
    ]
    if scale_ratios:
        print(f"  Median scale ratio:       {float(np.median(scale_ratios)):.6f}")
        print(f"  Mean scale ratio:         {float(np.mean(scale_ratios)):.6f}")
    else:
        print("  Scale ratios:             none valid")

    raw_means = mean_depth_metrics([result.raw_metrics for result in results])
    print(f"  Mean raw-scale metrics:   {format_depth_metrics(raw_means)}")

    scaled_rows = [
        result.scaled_metrics for result in results if result.scaled_metrics is not None
    ]
    if scaled_rows:
        scaled_means = mean_depth_metrics(scaled_rows)
        print(f"  Mean median-scaled metrics: {format_depth_metrics(scaled_means)}")
    else:
        print("  Mean median-scaled metrics: skipped because no scale ratios were valid")

    if timing is not None:
        print("  Timing:")
        if timing["model_load_seconds"] is not None:
            print(f"    model_load_seconds:        {timing['model_load_seconds']:.3f}")
        print(f"    evaluation_loop_seconds:   {timing['evaluation_loop_seconds']:.3f}")
        print(f"    total_run_seconds:         {timing['total_run_seconds']:.3f}")
        if timing["metric_samples_per_second"] is not None:
            print(f"    metric_samples_per_second: {timing['metric_samples_per_second']:.3f}")
        if timing["model_forward_fps"] is not None:
            print(f"    model_forward_fps:         {timing['model_forward_fps']:.3f}")


def inspect_sample(
    index: int,
    rgb_rel: str,
    dense_rel: str,
    manifest: Dict[str, Dict[str, str]],
    workspace_dir: Path,
    model: Optional[LiteMonoModel],
    eval_min_depth: float,
    eval_max_depth: float,
    print_details: bool,
) -> Optional[EvaluationResult]:
    sample_start = time.perf_counter()
    if rgb_rel not in manifest:
        raise KeyError(f"{rgb_rel} is present in split file but missing from all_samples.csv")

    row = manifest[rgb_rel]
    valid_mask_rel = row["valid_mask_rel"]
    manifest_dense_rel = row["dense_rel"]
    if manifest_dense_rel != dense_rel:
        raise ValueError(
            "Split dense path does not match manifest dense path:\n"
            f"  split:    {dense_rel}\n"
            f"  manifest: {manifest_dense_rel}"
        )

    rgb_path = workspace_dir / rgb_rel
    dense_path = workspace_dir / dense_rel
    valid_mask_path = workspace_dir / valid_mask_rel

    rgb_size = None
    if print_details:
        with Image.open(rgb_path) as image:
            rgb_size = image.size

    dense = load_npz_array(dense_path)
    valid_mask = load_npz_array(valid_mask_path)
    valid = (valid_mask > 0) & np.isfinite(dense) & (dense > 0)
    valid_depths = dense[valid]

    if print_details:
        print(f"\nSample {index}")
        print(f"  RGB:        {rgb_rel}")
        print(f"  Dense:      {dense_rel}")
        print(f"  Valid mask: {valid_mask_rel}")
        print(f"  RGB size:   width={rgb_size[0]}, height={rgb_size[1]}")
        print(f"  Dense:      shape={dense.shape}, dtype={dense.dtype}")
        print(f"  Mask:       shape={valid_mask.shape}, dtype={valid_mask.dtype}")
        print(f"  Dense all finite stats:   {format_stats(finite_stats(dense))}")
        print(f"  Dense valid-mask stats:   {format_stats(finite_stats(valid_depths))}")
        print(
            "  Valid pixels: "
            f"{int(np.count_nonzero(valid))}/{dense.size} "
            f"({np.count_nonzero(valid) / dense.size:.4%})"
        )
        print(f"  Pair delta ms: {row.get('time_delta_ms', 'n/a')}")
        print(f"  Dense fill ratio from manifest: {row.get('dense_fill_ratio', 'n/a')}")
    if model is not None:
        pred_depth, model_forward_seconds = run_lite_mono_inference(
            rgb_path, dense.shape, model, print_details=print_details
        )
        result = evaluate_prediction_against_label(
            dense=dense,
            valid_mask=valid_mask,
            pred_depth=pred_depth,
            eval_min_depth=eval_min_depth,
            eval_max_depth=eval_max_depth,
            print_details=print_details,
        )
        if result is None:
            return None
        return result._replace(
            index=index,
            rgb_rel=rgb_rel,
            dense_rel=dense_rel,
            valid_mask_rel=valid_mask_rel,
            sample_wall_seconds=time.perf_counter() - sample_start,
            model_forward_seconds=model_forward_seconds,
        )
    return None


def parse_args() -> argparse.Namespace:
    default_workspace = repo_root() / "citrus_project" / "dataset_workspace"
    parser = argparse.ArgumentParser(
        description="Inspect Citrus prepared split samples for Lite-Mono baseline evaluation."
    )
    parser.add_argument(
        "--dataset_workspace",
        type=Path,
        default=default_workspace,
        help="Path to citrus_project/dataset_workspace.",
    )
    parser.add_argument(
        "--prepared_name",
        default="prepared_training_dataset",
        help="Prepared dataset folder name inside the dataset workspace.",
    )
    parser.add_argument(
        "--split",
        choices=["train", "val", "test"],
        default="val",
        help="Prepared split to inspect.",
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=3,
        help="Number of samples to inspect from the selected split; use 0 or less for the full split.",
    )
    parser.add_argument(
        "--run_model",
        action="store_true",
        help="Also run original Lite-Mono inference for the selected samples.",
    )
    parser.add_argument(
        "--weights_folder",
        type=Path,
        default=repo_root() / "weights" / "lite-mono",
        help="Folder containing encoder.pth and depth.pth.",
    )
    parser.add_argument(
        "--model",
        default="lite-mono",
        choices=["lite-mono", "lite-mono-small", "lite-mono-tiny", "lite-mono-8m"],
        help="Lite-Mono model variant that matches the weights.",
    )
    parser.add_argument(
        "--no_cuda",
        action="store_true",
        help="Force CPU inference even if CUDA is available.",
    )
    parser.add_argument(
        "--min_depth",
        type=float,
        default=0.1,
        help="Minimum depth used by Lite-Mono disp_to_depth conversion.",
    )
    parser.add_argument(
        "--max_depth",
        type=float,
        default=100.0,
        help="Maximum depth used by Lite-Mono disp_to_depth conversion.",
    )
    parser.add_argument(
        "--eval_min_depth",
        type=float,
        default=1e-3,
        help="Minimum label depth kept for metric evaluation.",
    )
    parser.add_argument(
        "--eval_max_depth",
        type=float,
        default=80.0,
        help="Maximum label depth kept for metric evaluation, matching Lite-Mono/KITTI convention.",
    )
    parser.add_argument(
        "--summary_only",
        action="store_true",
        help="Suppress per-sample details and print only aggregate metric summary.",
    )
    parser.add_argument(
        "--progress_interval",
        type=int,
        default=50,
        help="When --summary_only is used, print progress every N samples.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=None,
        help="Optional folder for summary JSON and per-sample CSV result files.",
    )
    return parser.parse_args()


def main() -> None:
    run_start = time.perf_counter()
    args = parse_args()
    workspace_dir = args.dataset_workspace.resolve()
    prepared_dir = workspace_dir / args.prepared_name
    split_path = prepared_dir / "splits" / f"{args.split}_pairs.txt"
    manifest_path = prepared_dir / "metrics" / "all_samples.csv"

    manifest = load_manifest(manifest_path)
    pairs = load_split_pairs(split_path)
    selected_pairs = pairs if args.max_samples <= 0 else pairs[: args.max_samples]

    model = None
    model_load_seconds = None
    if args.run_model:
        model_load_start = time.perf_counter()
        model = load_lite_mono_model(
            weights_folder=args.weights_folder.resolve(),
            model_name=args.model,
            no_cuda=args.no_cuda,
            min_depth=args.min_depth,
            max_depth=args.max_depth,
        )
        model_load_seconds = time.perf_counter() - model_load_start

    print("Citrus Lite-Mono baseline evaluator")
    print(f"  Dataset workspace: {workspace_dir}")
    print(f"  Prepared dataset:  {prepared_dir}")
    print(f"  Split:             {args.split}")
    print(f"  Split samples:     {len(pairs)}")
    print(f"  Inspecting:        {len(selected_pairs)}")
    print(f"  Manifest rows:     {len(manifest)}")
    print(f"  Model inference:   {'enabled' if model is not None else 'disabled'}")
    print(f"  Summary only:      {args.summary_only}")
    print(f"  Output dir:        {args.output_dir.resolve() if args.output_dir else 'disabled'}")
    if model is not None:
        print(f"  Weights folder:    {args.weights_folder.resolve()}")
        print(f"  Model variant:     {args.model}")
        print(f"  Device:            {model.device}")
        print(f"  Feed size:         width={model.feed_width}, height={model.feed_height}")
        print(f"  Depth range:       {model.min_depth}..{model.max_depth} m")
        print(f"  Eval depth range:  {args.eval_min_depth}..{args.eval_max_depth} m")
        print(
            "  Parameters:        "
            f"total={model.model_info['total_parameters']} "
            f"({model.model_info['total_parameters_millions']:.3f}M), "
            f"encoder={model.model_info['encoder_parameters']}, "
            f"decoder={model.model_info['depth_decoder_parameters']}"
        )
        print(
            "  Checkpoint size:   "
            f"{model.model_info['total_checkpoint']['megabytes']:.2f} MiB"
        )

    results = []
    evaluation_loop_start = time.perf_counter()
    for index, (rgb_rel, dense_rel) in enumerate(selected_pairs, start=1):
        result = inspect_sample(
            index,
            rgb_rel,
            dense_rel,
            manifest,
            workspace_dir,
            model,
            args.eval_min_depth,
            args.eval_max_depth,
            print_details=not args.summary_only,
        )
        if result is not None:
            results.append(result)
        if (
            args.summary_only
            and args.progress_interval > 0
            and index % args.progress_interval == 0
        ):
            print(f"  Processed {index}/{len(selected_pairs)} samples")
    evaluation_loop_seconds = time.perf_counter() - evaluation_loop_start
    total_run_seconds = time.perf_counter() - run_start
    timing = build_timing_summary(
        results=results,
        requested_count=len(selected_pairs),
        model_load_seconds=model_load_seconds,
        evaluation_loop_seconds=evaluation_loop_seconds,
        total_run_seconds=total_run_seconds,
    )

    if model is not None:
        print_aggregate_summary(results, len(selected_pairs), timing=timing)
        if args.output_dir is not None:
            summary_path, per_sample_path = save_results(
                output_dir=args.output_dir.resolve(),
                args=args,
                model=model,
                workspace_dir=workspace_dir,
                prepared_dir=prepared_dir,
                results=results,
                requested_count=len(selected_pairs),
                split_count=len(pairs),
                timing=timing,
            )
            print("\nSaved result files")
            print(f"  Summary JSON:    {summary_path}")
            print(f"  Per-sample CSV:  {per_sample_path}")


if __name__ == "__main__":
    main()
