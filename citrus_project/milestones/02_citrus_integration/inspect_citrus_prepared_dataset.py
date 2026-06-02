from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import torch
from torch.utils.data import DataLoader, Subset

from citrus_prepared_dataset import CitrusPreparedDataset, repo_root


def finite_tensor_stats(tensor: torch.Tensor) -> Dict[str, float]:
    finite = tensor[torch.isfinite(tensor)]
    if finite.numel() == 0:
        return {"count": 0, "min": float("nan"), "median": float("nan"), "max": float("nan")}
    return {
        "count": int(finite.numel()),
        "min": float(torch.min(finite).item()),
        "median": float(torch.median(finite).item()),
        "max": float(torch.max(finite).item()),
    }


def format_stats(stats: Dict[str, float]) -> str:
    if stats["count"] == 0:
        return "count=0, min=n/a, median=n/a, max=n/a"
    return (
        f"count={stats['count']}, "
        f"min={stats['min']:.6f}, "
        f"median={stats['median']:.6f}, "
        f"max={stats['max']:.6f}"
    )


def inspect_split(args: argparse.Namespace, split: str) -> None:
    image_size = None if args.native_rgb else (args.width, args.height)
    frame_ids = args.frame_ids if args.temporal else [0]
    dataset = CitrusPreparedDataset(
        dataset_workspace=args.dataset_workspace,
        prepared_name=args.prepared_name,
        split=split,
        image_size=image_size,
        frame_ids=frame_ids,
        num_scales=args.num_scales,
        max_neighbor_delta_ms=args.max_neighbor_delta_ms,
    )
    sample_count = min(args.samples_per_split, len(dataset))
    subset = Subset(dataset, range(sample_count))
    loader = DataLoader(
        subset,
        batch_size=min(args.batch_size, max(sample_count, 1)),
        shuffle=False,
        num_workers=0,
    )

    print(f"\nSplit: {split}")
    print(f"  Dataset samples: {len(dataset)}")
    print(f"  Inspecting:      {sample_count}")
    if args.temporal:
        print(f"  Temporal frames: {frame_ids}")
    if sample_count == 0:
        return

    batch = next(iter(loader))
    color = batch["color"]
    depth_gt = batch["depth_gt"]
    valid_mask = batch["valid_mask"]
    label_mask = batch["label_mask"]

    print(
        "  RGB batch:       "
        f"shape={tuple(color.shape)}, dtype={color.dtype}, "
        f"range={float(color.min()):.6f}..{float(color.max()):.6f}"
    )
    if args.temporal:
        for frame_id in frame_ids:
            temporal_color = batch[("color", frame_id, 0)]
            print(
                f"  RGB frame {frame_id:+}:   "
                f"shape={tuple(temporal_color.shape)}, dtype={temporal_color.dtype}, "
                f"range={float(temporal_color.min()):.6f}.."
                f"{float(temporal_color.max()):.6f}"
            )
    print(
        "  Depth batch:     "
        f"shape={tuple(depth_gt.shape)}, dtype={depth_gt.dtype}, "
        f"{format_stats(finite_tensor_stats(depth_gt))}"
    )
    valid_depths = depth_gt[label_mask > 0]
    print(f"  Valid depths:    {format_stats(finite_tensor_stats(valid_depths))}")
    print(
        "  Valid mask:      "
        f"shape={tuple(valid_mask.shape)}, dtype={valid_mask.dtype}, "
        f"mean={float(valid_mask.mean()):.6f}"
    )
    print(
        "  Label mask:      "
        f"shape={tuple(label_mask.shape)}, dtype={label_mask.dtype}, "
        f"mean={float(label_mask.mean()):.6f}"
    )
    print("  K[0]:")
    print(batch["K"][0].numpy())

    for item_idx in range(sample_count):
        metadata = {
            key: values[item_idx]
            for key, values in batch["metadata"].items()
            if key in {"time_delta_ms", "dense_fill_ratio", "valid_ratio", "transform_mode"}
        }
        print(f"  Sample {item_idx}:")
        print(f"    dataset_index:   {int(batch['index'][item_idx])}")
        print(f"    split_index:     {int(batch['split_index'][item_idx])}")
        print(f"    rgb_rel:        {batch['rgb_rel'][item_idx]}")
        print(f"    dense_rel:      {batch['dense_rel'][item_idx]}")
        print(f"    valid_mask_rel: {batch['valid_mask_rel'][item_idx]}")
        print(f"    session:        {batch['session'][item_idx]}")
        print(f"    timestamp_ns:   {int(batch['timestamp_ns'][item_idx])}")
        print(f"    native_size_hw: {batch['native_size_hw'][item_idx].tolist()}")
        print(f"    image_size_hw:  {batch['image_size_hw'][item_idx].tolist()}")
        if args.temporal:
            frame_paths = {
                frame_id: batch["frame_rgb_rel"][str(frame_id)][item_idx]
                for frame_id in frame_ids
            }
            frame_deltas = {
                frame_id: float(batch["neighbor_delta_ms"][str(frame_id)][item_idx])
                for frame_id in frame_ids
            }
            print(f"    frame_rgb_rel:  {frame_paths}")
            print(f"    delta_ms:       {frame_deltas}")
        print(f"    metadata:       {metadata}")


def parse_args() -> argparse.Namespace:
    default_workspace = repo_root() / "citrus_project" / "dataset_workspace"
    parser = argparse.ArgumentParser(
        description="Smoke-inspect the Milestone 2 Citrus prepared Dataset/DataLoader."
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
        "--splits",
        nargs="+",
        default=["train", "val"],
        choices=["train", "val", "test"],
        help="Prepared splits to inspect.",
    )
    parser.add_argument(
        "--samples_per_split",
        type=int,
        default=2,
        help="Number of leading samples to inspect from each split.",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=2,
        help="DataLoader batch size for the smoke inspection.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=192,
        help="RGB tensor height when not using --native_rgb.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="RGB tensor width when not using --native_rgb.",
    )
    parser.add_argument(
        "--native_rgb",
        action="store_true",
        help="Keep RGB tensors at native 1280x720 instead of resizing to model size.",
    )
    parser.add_argument(
        "--temporal",
        action="store_true",
        help="Load same-split temporal RGB triplets instead of target-only RGB samples.",
    )
    parser.add_argument(
        "--frame_ids",
        nargs="+",
        type=int,
        default=[0, -1, 1],
        help="Temporal frame ids to load when --temporal is set.",
    )
    parser.add_argument(
        "--num_scales",
        type=int,
        default=4,
        help="Number of RGB pyramid scales to return.",
    )
    parser.add_argument(
        "--max_neighbor_delta_ms",
        type=float,
        default=200.0,
        help="Maximum target-to-neighbor timestamp gap when --temporal is set.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("Citrus prepared Dataset/DataLoader smoke inspection")
    print(f"  Dataset workspace: {args.dataset_workspace.resolve()}")
    print(f"  Prepared dataset:  {args.prepared_name}")
    print(f"  Splits:            {', '.join(args.splits)}")
    if args.native_rgb:
        print("  RGB tensor size:   native")
    else:
        print(f"  RGB tensor size:   width={args.width}, height={args.height}")
    print(f"  Batch size:        {args.batch_size}")
    if args.temporal:
        print(f"  Temporal mode:     enabled, frame_ids={args.frame_ids}")
        print(f"  Neighbor cap:      {args.max_neighbor_delta_ms:.3f} ms")
    else:
        print("  Temporal mode:     disabled")

    for split in args.splits:
        inspect_split(args, split)


if __name__ == "__main__":
    main()
