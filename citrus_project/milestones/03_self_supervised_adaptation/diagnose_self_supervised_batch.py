from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import torch
from torch.utils.data import DataLoader


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from options import LiteMonoOptions  # noqa: E402
import trainer as trainer_module  # noqa: E402
from layers import get_smooth_loss  # noqa: E402


class NullSummaryWriter:
    def __init__(self, *args, **kwargs):
        pass

    def add_scalar(self, *args, **kwargs):
        pass

    def add_image(self, *args, **kwargs):
        pass

    def close(self):
        pass


trainer_module.SummaryWriter = NullSummaryWriter


def skip_save_opts(self):
    pass


trainer_module.Trainer.save_opts = skip_save_opts
Trainer = trainer_module.Trainer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a few Citrus self-supervised batches without optimizer updates. "
            "Reports photometric, automask, pose, and depth-monitor signals."
        )
    )
    parser.add_argument(
        "--weights_folder",
        type=Path,
        default=REPO_ROOT / "weights" / "lite-mono",
        help="Checkpoint folder to load.",
    )
    parser.add_argument(
        "--models_to_load",
        nargs="+",
        default=["encoder", "depth"],
        help="Model files to load from the checkpoint folder.",
    )
    parser.add_argument(
        "--weights_init",
        choices=["pretrained", "scratch"],
        default="scratch",
        help=(
            "Pose encoder initialization before checkpoint loading. This is useful "
            "when comparing original depth weights against pretrained-pose pilots."
        ),
    )
    parser.add_argument(
        "--frame_ids",
        nargs="+",
        default=None,
        help=(
            "Optional Lite-Mono frame ids for diagnostics, for example: "
            "--frame_ids 0 -1 for previous-only checkpoints."
        ),
    )
    parser.add_argument(
        "--name",
        default="diagnostic",
        help="Short label included in printed rows and saved outputs.",
    )
    parser.add_argument(
        "--split",
        choices=["train", "val"],
        default="train",
        help="Which trainer loader to inspect.",
    )
    parser.add_argument(
        "--batches",
        type=int,
        default=5,
        help="Number of batches to inspect.",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="Batch size for inspection.",
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=0,
        help="DataLoader workers for inspection.",
    )
    parser.add_argument(
        "--no_cuda",
        action="store_true",
        help="Force CPU.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=None,
        help="Optional directory for CSV/JSON diagnostic outputs.",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Inspect shuffled batches instead of fixed-order batches.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for deterministic diagnostic construction.",
    )
    parser.add_argument(
        "--freeze_depth_encoder",
        action="store_true",
        help=(
            "Build the trainer with --freeze_depth_encoder. Use this when "
            "diagnosing checkpoints trained with a frozen depth encoder."
        ),
    )
    return parser.parse_args()


def build_options(args: argparse.Namespace):
    option_args = [
        "diagnose_self_supervised_batch.py",
        "--dataset", "citrus",
        "--load_weights_folder", str(args.weights_folder),
        "--models_to_load", *args.models_to_load,
        "--weights_init", args.weights_init,
        "--batch_size", str(args.batch_size),
        "--num_workers", str(args.num_workers),
        "--num_epochs", "1",
        "--max_train_steps", "1",
        "--log_frequency", "999999",
        "--log_dir", str(REPO_ROOT / "citrus_project" / "milestones"
                         / "03_self_supervised_adaptation" / "runs"
                         / "_diagnostic_tmp"),
        "--model_name", args.name,
    ]
    if args.frame_ids is not None:
        option_args.extend(["--frame_ids", *args.frame_ids])
    if args.freeze_depth_encoder:
        option_args.append("--freeze_depth_encoder")
    if args.no_cuda:
        option_args.append("--no_cuda")
    sys.argv = option_args
    return LiteMonoOptions().parse()


def close_writers(trainer: Trainer) -> None:
    for writer in getattr(trainer, "writers", {}).values():
        writer.close()


def to_float(value) -> float:
    if isinstance(value, np.ndarray):
        return float(value)
    if torch.is_tensor(value):
        return float(value.detach().cpu())
    return float(value)


def tensor_stats(prefix: str, tensor: torch.Tensor) -> Dict[str, float]:
    data = tensor.detach()
    finite = data[torch.isfinite(data)]
    if finite.numel() == 0:
        return {
            f"{prefix}_min": float("nan"),
            f"{prefix}_median": float("nan"),
            f"{prefix}_mean": float("nan"),
            f"{prefix}_max": float("nan"),
        }
    return {
        f"{prefix}_min": float(finite.min().cpu()),
        f"{prefix}_median": float(torch.median(finite).cpu()),
        f"{prefix}_mean": float(finite.mean().cpu()),
        f"{prefix}_max": float(finite.max().cpu()),
    }


def mean_reprojection(
    trainer: Trainer,
    pred: torch.Tensor,
    target: torch.Tensor,
) -> float:
    loss = trainer.compute_reprojection_loss(pred, target)
    return float(loss.detach().mean().cpu())


def add_loss_decomposition(
    row: Dict[str, float],
    trainer: Trainer,
    inputs: Dict,
    outputs: Dict,
) -> None:
    """Recompute existing loss pieces for diagnostics without changing training."""
    source_frame_ids = [
        frame_id for frame_id in trainer.opt.frame_ids[1:] if frame_id != "s"
    ]
    for scale in trainer.opt.scales:
        source_scale = scale if trainer.opt.v1_multiscale else 0
        disp = outputs[("disp", scale)]
        color = inputs[("color", 0, scale)]
        target = inputs[("color", 0, source_scale)]

        reprojection_losses = []
        identity_losses = []
        for frame_id in source_frame_ids:
            reprojection_loss = trainer.compute_reprojection_loss(
                outputs[("color", frame_id, scale)], target
            )
            reprojection_losses.append(reprojection_loss)
            row[f"reprojection_loss_{frame_id}_s{scale}"] = float(
                reprojection_loss.detach().mean().cpu()
            )
            if not trainer.opt.disable_automasking:
                identity_loss = trainer.compute_reprojection_loss(
                    inputs[("color", frame_id, source_scale)], target
                )
                identity_losses.append(identity_loss)
                row[f"identity_loss_{frame_id}_s{scale}"] = float(
                    identity_loss.detach().mean().cpu()
                )

        reprojection_losses = torch.cat(reprojection_losses, 1)
        if trainer.opt.avg_reprojection:
            reprojection_for_selection = reprojection_losses.mean(1, keepdim=True)
        else:
            reprojection_for_selection = reprojection_losses

        row[f"reprojection_mean_loss_s{scale}"] = float(
            reprojection_losses.detach().mean().cpu()
        )
        row[f"reprojection_min_loss_s{scale}"] = float(
            reprojection_for_selection.detach().min(1)[0].mean().cpu()
        )

        if not trainer.opt.disable_automasking:
            identity_losses = torch.cat(identity_losses, 1)
            if trainer.opt.avg_reprojection:
                identity_for_selection = identity_losses.mean(1, keepdim=True)
            else:
                identity_for_selection = identity_losses
            combined = torch.cat((identity_for_selection, reprojection_for_selection), dim=1)
            identity_channels = identity_for_selection.shape[1]
            row[f"identity_mean_loss_s{scale}"] = float(
                identity_losses.detach().mean().cpu()
            )
            row[f"identity_min_loss_s{scale}"] = float(
                identity_for_selection.detach().min(1)[0].mean().cpu()
            )
        else:
            combined = reprojection_for_selection
            identity_channels = 0

        if combined.shape[1] == 1:
            selected_photo_loss = combined[:, 0]
            selected_indices = torch.zeros_like(selected_photo_loss, dtype=torch.long)
        else:
            selected_photo_loss, selected_indices = torch.min(combined, dim=1)
        row[f"selected_photo_loss_s{scale}"] = float(
            selected_photo_loss.detach().mean().cpu()
        )

        if not trainer.opt.disable_automasking:
            reprojection_selected = selected_indices >= identity_channels
            row[f"automask_reprojection_fraction_calc_s{scale}"] = float(
                reprojection_selected.float().detach().mean().cpu()
            )
            if not trainer.opt.avg_reprojection:
                selected_source_indices = selected_indices - identity_channels
                selected_source_indices = torch.where(
                    reprojection_selected,
                    selected_source_indices,
                    torch.full_like(selected_source_indices, -1),
                )
                selected_count = reprojection_selected.float().sum().clamp_min(1.0)
                for source_index, frame_id in enumerate(source_frame_ids):
                    source_mask = reprojection_selected & (
                        selected_source_indices == source_index
                    )
                    row[f"selected_source_fraction_all_{frame_id}_s{scale}"] = float(
                        source_mask.float().detach().mean().cpu()
                    )
                    row[f"selected_source_fraction_reproj_{frame_id}_s{scale}"] = float(
                        (source_mask.float().sum() / selected_count).detach().cpu()
                    )

        mean_disp = disp.mean(2, True).mean(3, True)
        norm_disp = disp / (mean_disp + 1e-7)
        smooth_loss = get_smooth_loss(norm_disp, color)
        weighted_smooth_loss = (
            trainer.opt.disparity_smoothness * smooth_loss / (2 ** scale)
        )
        row[f"smooth_loss_s{scale}"] = float(smooth_loss.detach().cpu())
        row[f"weighted_smooth_loss_s{scale}"] = float(
            weighted_smooth_loss.detach().cpu()
        )
        row[f"smooth_fraction_of_scale_loss_s{scale}"] = float(
            (
                weighted_smooth_loss
                / (selected_photo_loss.mean() + weighted_smooth_loss + 1e-7)
            ).detach().cpu()
        )


def inspect_batches(args: argparse.Namespace) -> List[Dict[str, float]]:
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    opts = build_options(args)
    trainer = Trainer(opts)
    rows: List[Dict[str, float]] = []
    try:
        trainer.set_eval()
        base_loader = trainer.train_loader if args.split == "train" else trainer.val_loader
        loader = DataLoader(
            base_loader.dataset,
            args.batch_size,
            shuffle=args.shuffle,
            num_workers=args.num_workers,
            pin_memory=True,
            drop_last=True,
        )
        for batch_idx, inputs in enumerate(loader):
            if batch_idx >= args.batches:
                break
            with torch.no_grad():
                outputs, losses = trainer.process_batch(inputs)
                trainer.compute_depth_losses(inputs, outputs, losses)

            row: Dict[str, float] = {
                "name": args.name,
                "split": args.split,
                "batch_index": batch_idx,
                "loss": to_float(losses["loss"]),
            }
            for scale in trainer.opt.scales:
                row[f"loss_scale_{scale}"] = to_float(losses[f"loss/{scale}"])
                if f"identity_selection/{scale}" in outputs:
                    row[f"automask_reprojection_fraction_s{scale}"] = float(
                        outputs[f"identity_selection/{scale}"].detach().mean().cpu()
                    )
            add_loss_decomposition(row, trainer, inputs, outputs)

            for metric in trainer.depth_metric_names:
                if metric in losses:
                    safe_metric = metric.replace("/", "_")
                    row[safe_metric] = to_float(losses[metric])

            row.update(tensor_stats("depth_s0", outputs[("depth", 0, 0)]))
            row.update(tensor_stats("disp_s0", outputs[("disp", 0)]))

            target = inputs[("color", 0, 0)]
            for frame_id in trainer.opt.frame_ids[1:]:
                if frame_id == "s":
                    continue
                translation = outputs[("translation", 0, frame_id)][:, 0]
                axisangle = outputs[("axisangle", 0, frame_id)][:, 0]
                sample_grid = outputs[("sample", frame_id, 0)]
                row[f"translation_norm_{frame_id}"] = float(
                    torch.linalg.norm(translation, dim=1).mean().detach().cpu()
                )
                row[f"axisangle_norm_{frame_id}"] = float(
                    torch.linalg.norm(axisangle, dim=1).mean().detach().cpu()
                )
                row[f"reprojection_loss_{frame_id}"] = mean_reprojection(
                    trainer, outputs[("color", frame_id, 0)], target
                )
                row[f"identity_loss_{frame_id}"] = mean_reprojection(
                    trainer, inputs[("color", frame_id, 0)], target
                )
                outside = (
                    (sample_grid[..., 0] < -1.0)
                    | (sample_grid[..., 0] > 1.0)
                    | (sample_grid[..., 1] < -1.0)
                    | (sample_grid[..., 1] > 1.0)
                )
                row[f"warp_oob_fraction_{frame_id}"] = float(
                    outside.float().mean().detach().cpu()
                )
            rows.append(row)
    finally:
        close_writers(trainer)
    return rows


def summarize(rows: Iterable[Dict[str, float]]) -> Dict[str, float]:
    rows = list(rows)
    numeric_keys = [
        key
        for key, value in rows[0].items()
        if isinstance(value, (int, float)) and key != "batch_index"
    ] if rows else []
    summary = {"batches": len(rows)}
    for key in numeric_keys:
        values = [row[key] for row in rows if np.isfinite(row[key])]
        summary[f"{key}_mean"] = float(np.mean(values)) if values else float("nan")
    return summary


def save_outputs(args: argparse.Namespace, rows: List[Dict[str, float]]) -> None:
    if args.output_dir is None:
        return
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{args.name}_{args.split}_batch_diagnostics.csv"
    json_path = output_dir / f"{args.name}_{args.split}_batch_diagnostics_summary.json"

    fieldnames = sorted({key for row in rows for key in row})
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with json_path.open("w", encoding="utf-8") as fp:
        json.dump(summarize(rows), fp, indent=2)

    print(f"Saved CSV:     {csv_path}")
    print(f"Saved summary: {json_path}")


def print_summary(args: argparse.Namespace, rows: List[Dict[str, float]]) -> None:
    summary = summarize(rows)
    print("Self-supervised batch diagnostics")
    print(f"  Name:           {args.name}")
    print(f"  Split:          {args.split}")
    print(f"  Weights folder: {args.weights_folder.resolve()}")
    print(f"  Models loaded:  {args.models_to_load}")
    print(f"  Batches:        {summary['batches']}")
    keys_to_print = [
        "loss_mean",
        "de_abs_rel_mean",
        "da_a1_mean",
        "depth_s0_median_mean",
        "automask_reprojection_fraction_s0_mean",
        "selected_photo_loss_s0_mean",
        "weighted_smooth_loss_s0_mean",
        "smooth_fraction_of_scale_loss_s0_mean",
        "identity_min_loss_s0_mean",
        "reprojection_min_loss_s0_mean",
        "selected_source_fraction_reproj_-1_s0_mean",
        "selected_source_fraction_reproj_1_s0_mean",
        "reprojection_loss_-1_mean",
        "identity_loss_-1_mean",
        "reprojection_loss_1_mean",
        "identity_loss_1_mean",
        "translation_norm_-1_mean",
        "translation_norm_1_mean",
        "warp_oob_fraction_-1_mean",
        "warp_oob_fraction_1_mean",
    ]
    for key in keys_to_print:
        if key in summary:
            print(f"  {key}: {summary[key]:.6f}")


def main() -> None:
    args = parse_args()
    rows = inspect_batches(args)
    print_summary(args, rows)
    save_outputs(args, rows)


if __name__ == "__main__":
    main()
