from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, Tuple

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from citrus_prepared_dataset import CitrusPreparedDataset, repo_root


def ensure_repo_imports(root: Path) -> None:
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def move_tensor_batch_to_device(batch: Dict[object, object], device: torch.device) -> Dict[object, torch.Tensor]:
    moved = {}
    non_tensor = []
    for key, value in batch.items():
        if not hasattr(value, "to"):
            non_tensor.append((key, type(value).__name__))
            continue
        moved[key] = value.to(device)
    if non_tensor:
        raise TypeError(
            "Trainer-facing dry run expects tensor-like batch values only; "
            f"found {non_tensor[:5]}"
        )
    return moved


def tensor_summary(tensor: torch.Tensor) -> str:
    detached = tensor.detach()
    return (
        f"shape={tuple(detached.shape)}, dtype={detached.dtype}, "
        f"device={detached.device}, "
        f"range={float(detached.min()):.6f}..{float(detached.max()):.6f}"
    )


def build_models(args: argparse.Namespace, device: torch.device):
    import networks

    encoder = networks.LiteMono(
        model=args.model,
        drop_path_rate=args.drop_path,
        width=args.width,
        height=args.height,
    ).to(device)
    depth_decoder = networks.DepthDecoder(encoder.num_ch_enc, args.scales).to(device)
    pose_encoder = networks.ResnetEncoder(
        args.num_layers,
        pretrained=False,
        num_input_images=2,
    ).to(device)
    pose_decoder = networks.PoseDecoder(
        pose_encoder.num_ch_enc,
        num_input_features=1,
        num_frames_to_predict_for=2,
    ).to(device)

    encoder.eval()
    depth_decoder.eval()
    pose_encoder.eval()
    pose_decoder.eval()
    return encoder, depth_decoder, pose_encoder, pose_decoder


def predict_poses_like_trainer(
    inputs: Dict[object, torch.Tensor],
    pose_encoder,
    pose_decoder,
    frame_ids: Iterable[int],
) -> Dict[object, torch.Tensor]:
    from layers import transformation_from_parameters

    outputs = {}
    pose_feats = {frame_id: inputs[("color_aug", frame_id, 0)] for frame_id in frame_ids}
    for frame_id in frame_ids:
        if frame_id == 0:
            continue
        if frame_id < 0:
            pose_inputs = [pose_feats[frame_id], pose_feats[0]]
        else:
            pose_inputs = [pose_feats[0], pose_feats[frame_id]]

        pose_features = [pose_encoder(torch.cat(pose_inputs, 1))]
        axisangle, translation = pose_decoder(pose_features)
        outputs[("axisangle", 0, frame_id)] = axisangle
        outputs[("translation", 0, frame_id)] = translation
        outputs[("cam_T_cam", 0, frame_id)] = transformation_from_parameters(
            axisangle[:, 0],
            translation[:, 0],
            invert=(frame_id < 0),
        )
    return outputs


def synthesize_views_like_trainer(
    args: argparse.Namespace,
    inputs: Dict[object, torch.Tensor],
    outputs: Dict[object, torch.Tensor],
    batch_size: int,
    frame_ids: Tuple[int, ...],
    device: torch.device,
) -> Dict[object, torch.Tensor]:
    from layers import BackprojectDepth, Project3D, disp_to_depth

    backproject_depth = {}
    project_3d = {}
    for scale in args.scales:
        height = args.height // (2 ** scale)
        width = args.width // (2 ** scale)
        backproject_depth[scale] = BackprojectDepth(batch_size, height, width).to(device)
        project_3d[scale] = Project3D(batch_size, height, width).to(device)

    for scale in args.scales:
        disp = outputs[("disp", scale)]
        if args.v1_multiscale:
            source_scale = scale
        else:
            disp = F.interpolate(
                disp,
                [args.height, args.width],
                mode="bilinear",
                align_corners=False,
            )
            source_scale = 0

        _, depth = disp_to_depth(disp, args.min_depth, args.max_depth)
        outputs[("depth", 0, scale)] = depth

        for frame_id in frame_ids:
            if frame_id == 0:
                continue
            cam_points = backproject_depth[source_scale](
                depth,
                inputs[("inv_K", source_scale)],
            )
            pix_coords = project_3d[source_scale](
                cam_points,
                inputs[("K", source_scale)],
                outputs[("cam_T_cam", 0, frame_id)],
            )
            outputs[("sample", frame_id, scale)] = pix_coords
            outputs[("color", frame_id, scale)] = F.grid_sample(
                inputs[("color", frame_id, source_scale)],
                pix_coords,
                padding_mode="border",
                align_corners=True,
            )
    return outputs


def reprojection_smoke_loss(
    args: argparse.Namespace,
    inputs: Dict[object, torch.Tensor],
    outputs: Dict[object, torch.Tensor],
    frame_ids: Tuple[int, ...],
) -> torch.Tensor:
    target = inputs[("color", 0, 0)]
    losses = []
    for scale in args.scales:
        for frame_id in frame_ids:
            if frame_id == 0:
                continue
            losses.append(torch.abs(outputs[("color", frame_id, scale)] - target).mean())
    return torch.stack(losses).mean()


def parse_args() -> argparse.Namespace:
    default_workspace = repo_root() / "citrus_project" / "dataset_workspace"
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run one Citrus temporal DataLoader batch through the Lite-Mono "
            "depth, pose, projection, and reprojection shape path without editing trainer.py."
        )
    )
    parser.add_argument("--dataset_workspace", type=Path, default=default_workspace)
    parser.add_argument("--prepared_name", default="prepared_training_dataset")
    parser.add_argument("--split", choices=["train", "val", "test"], default="train")
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--height", type=int, default=192)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--frame_ids", nargs="+", type=int, default=[0, -1, 1])
    parser.add_argument("--max_neighbor_delta_ms", type=float, default=200.0)
    parser.add_argument("--model", default="lite-mono")
    parser.add_argument("--drop_path", type=float, default=0.0)
    parser.add_argument("--num_layers", type=int, default=18)
    parser.add_argument("--scales", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--num_loader_scales", type=int, default=4)
    parser.add_argument("--min_depth", type=float, default=0.1)
    parser.add_argument("--max_depth", type=float, default=100.0)
    parser.add_argument("--v1_multiscale", action="store_true")
    parser.add_argument("--no_cuda", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = repo_root()
    ensure_repo_imports(root)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    frame_ids = tuple(args.frame_ids)

    dataset = CitrusPreparedDataset(
        dataset_workspace=args.dataset_workspace,
        prepared_name=args.prepared_name,
        split=args.split,
        image_size=(args.width, args.height),
        load_depth=True,
        frame_ids=frame_ids,
        num_scales=args.num_loader_scales,
        max_neighbor_delta_ms=args.max_neighbor_delta_ms,
        include_metadata=False,
    )
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        drop_last=True,
    )
    batch = next(iter(loader))
    inputs = move_tensor_batch_to_device(batch, device)
    batch_size = inputs[("color", 0, 0)].shape[0]

    encoder, depth_decoder, pose_encoder, pose_decoder = build_models(args, device)

    print("Citrus Lite-Mono temporal batch dry run")
    print(f"  Dataset workspace: {args.dataset_workspace.resolve()}")
    print(f"  Prepared dataset:  {args.prepared_name}")
    print(f"  Split:             {args.split}")
    print(f"  Temporal samples:  {len(dataset)}")
    print(f"  Batch size:        {batch_size}")
    print(f"  Device:            {device}")
    print(f"  Frame ids:         {list(frame_ids)}")
    print(f"  Input size:        width={args.width}, height={args.height}")
    print(f"  Batch keys:        {len(inputs)} tensor-like values")

    with torch.no_grad():
        features = encoder(inputs[("color_aug", 0, 0)])
        outputs = depth_decoder(features)
        outputs.update(
            predict_poses_like_trainer(inputs, pose_encoder, pose_decoder, frame_ids)
        )
        outputs = synthesize_views_like_trainer(
            args,
            inputs,
            outputs,
            batch_size,
            frame_ids,
            device,
        )
        smoke_loss = reprojection_smoke_loss(args, inputs, outputs, frame_ids)

    print("  Inputs:")
    for frame_id in frame_ids:
        print(f"    color_aug frame {frame_id:+}: {tensor_summary(inputs[('color_aug', frame_id, 0)])}")
    print(f"    K scale 0:           {tensor_summary(inputs[('K', 0)])}")
    print(f"    inv_K scale 0:       {tensor_summary(inputs[('inv_K', 0)])}")
    if "depth_gt" in inputs:
        print(f"    depth_gt:            {tensor_summary(inputs['depth_gt'])}")
        print(f"    valid_mask mean:     {float(inputs['valid_mask'].mean()):.6f}")

    print("  Depth outputs:")
    for scale in args.scales:
        print(f"    disp scale {scale}:       {tensor_summary(outputs[('disp', scale)])}")
        print(f"    depth scale {scale}:      {tensor_summary(outputs[('depth', 0, scale)])}")

    print("  Pose and warp outputs:")
    for frame_id in frame_ids:
        if frame_id == 0:
            continue
        print(f"    cam_T_cam {frame_id:+}:       {tensor_summary(outputs[('cam_T_cam', 0, frame_id)])}")
        print(f"    warped color {frame_id:+}:    {tensor_summary(outputs[('color', frame_id, 0)])}")

    print(f"  Reprojection smoke loss: {float(smoke_loss):.6f}")
    print("  Result: temporal Citrus batch is compatible with the core Lite-Mono shape path.")


if __name__ == "__main__":
    main()
