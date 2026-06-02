from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from options import LiteMonoOptions  # noqa: E402
import trainer as trainer_module  # noqa: E402


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
Trainer = trainer_module.Trainer


def parse_smoke_options():
    generated_log_dir = Path("tmp_trainer_wiring_smoke")
    sys.argv = [
        "smoke_root_citrus_trainer_wiring.py",
        "--dataset", "citrus",
        "--batch_size", "1",
        "--num_workers", "0",
        "--num_epochs", "1",
        "--no_cuda",
        "--weights_init", "scratch",
        "--log_dir", str(generated_log_dir),
        "--model_name", "root_citrus_trainer_wiring_smoke",
        "--log_frequency", "999999",
    ]
    return LiteMonoOptions().parse()


def assert_bad_citrus_crop_rejected() -> None:
    sys.argv = [
        "smoke_root_citrus_trainer_wiring.py",
        "--dataset", "citrus",
        "--depth_metric_crop", "kitti_eigen",
    ]
    opts = LiteMonoOptions().parse()
    trainer = Trainer.__new__(Trainer)
    trainer.opt = opts
    try:
        trainer.configure_dataset_options()
    except ValueError as exc:
        if "--depth_metric_crop none" not in str(exc):
            raise
    else:
        raise AssertionError("Citrus should reject explicit kitti_eigen depth metric crop")


def close_writers(trainer: Trainer) -> None:
    for writer in getattr(trainer, "writers", {}).values():
        writer.close()


def main() -> None:
    assert_bad_citrus_crop_rejected()
    opts = parse_smoke_options()
    trainer = Trainer(opts)
    try:
        if trainer.opt.dataset != "citrus":
            raise AssertionError(f"Expected citrus dataset, got {trainer.opt.dataset}")
        if trainer.opt.split != "citrus_prepared":
            raise AssertionError(f"Expected citrus_prepared split, got {trainer.opt.split}")
        if trainer.opt.depth_metric_crop != "none":
            raise AssertionError(
                f"Expected Citrus depth_metric_crop none, got {trainer.opt.depth_metric_crop}"
            )

        train_count = len(trainer.train_loader.dataset)
        val_count = len(trainer.val_loader.dataset)
        if train_count <= 0 or val_count <= 0:
            raise AssertionError(
                f"Expected non-empty Citrus train/val datasets, got {train_count}/{val_count}"
            )

        batch = next(iter(trainer.train_loader))
        trainer.set_eval()
        with torch.no_grad():
            outputs, losses = trainer.process_batch(batch)
            trainer.compute_depth_losses(batch, outputs, losses)

        loss = float(losses["loss"])
        abs_rel = float(losses["de/abs_rel"])
        if not np.isfinite(loss) or not np.isfinite(abs_rel):
            raise AssertionError(
                f"Expected finite smoke losses, got loss={loss}, abs_rel={abs_rel}"
            )

        print("Root Citrus trainer wiring smoke passed.")
        print(f"  data_path:          {trainer.opt.data_path}")
        print(f"  split:              {trainer.opt.split}")
        print(f"  depth_metric_crop:  {trainer.opt.depth_metric_crop}")
        print(f"  train samples:      {train_count}")
        print(f"  val samples:        {val_count}")
        print(f"  photometric loss:   {loss:.6f}")
        print(f"  depth abs_rel:      {abs_rel:.6f}")
    finally:
        close_writers(trainer)


if __name__ == "__main__":
    main()
