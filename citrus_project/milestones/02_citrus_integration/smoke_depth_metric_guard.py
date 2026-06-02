from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trainer import Trainer  # noqa: E402


DEPTH_METRIC_NAMES = [
    "de/abs_rel",
    "de/sq_rel",
    "de/rms",
    "de/log_rms",
    "da/a1",
    "da/a2",
    "da/a3",
]


def make_trainer(crop_mode: str) -> Trainer:
    trainer = Trainer.__new__(Trainer)
    trainer.opt = SimpleNamespace(depth_metric_crop=crop_mode)
    trainer.depth_metric_names = DEPTH_METRIC_NAMES
    return trainer


def make_outputs(depth_value: float = 2.0) -> dict:
    return {("depth", 0, 0): torch.full((1, 1, 192, 640), depth_value)}


def assert_finite_metric(losses: dict, metric_name: str) -> None:
    value = float(losses[metric_name])
    if not np.isfinite(value):
        raise AssertionError(f"{metric_name} should be finite, got {value}")


def run_kitti_default_crop_smoke() -> None:
    trainer = make_trainer("kitti_eigen")
    inputs = {"depth_gt": torch.full((1, 1, 375, 1242), 2.0)}
    losses = {}

    trainer.compute_depth_losses(inputs, make_outputs(), losses)

    assert_finite_metric(losses, "de/abs_rel")
    if abs(float(losses["da/a1"]) - 1.0) > 1e-6:
        raise AssertionError("KITTI-shaped perfect prediction should have da/a1=1.0")


def run_citrus_shape_guard_smoke() -> None:
    trainer = make_trainer("kitti_eigen")
    inputs = {"depth_gt": torch.full((1, 1, 720, 1280), 2.0)}

    try:
        trainer.compute_depth_losses(inputs, make_outputs(), {})
    except ValueError as exc:
        if "depth_metric_crop='kitti_eigen'" not in str(exc):
            raise
    else:
        raise AssertionError("Citrus-shaped labels should not silently use the KITTI crop")


def run_citrus_no_crop_valid_mask_smoke() -> None:
    trainer = make_trainer("none")
    depth_gt = torch.full((1, 1, 720, 1280), 2.0)
    valid_mask = torch.zeros((1, 1, 720, 1280))
    valid_mask[:, :, 120:240, 300:460] = 1
    losses = {}

    trainer.compute_depth_losses(
        {"depth_gt": depth_gt, "valid_mask": valid_mask},
        make_outputs(),
        losses,
    )

    assert_finite_metric(losses, "de/abs_rel")
    if abs(float(losses["da/a1"]) - 1.0) > 1e-6:
        raise AssertionError("Citrus no-crop perfect prediction should have da/a1=1.0")


def main() -> None:
    run_kitti_default_crop_smoke()
    run_citrus_shape_guard_smoke()
    run_citrus_no_crop_valid_mask_smoke()
    print("Depth metric guard smoke passed.")


if __name__ == "__main__":
    main()
