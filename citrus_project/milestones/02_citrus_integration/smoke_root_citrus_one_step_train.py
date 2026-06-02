from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one root Trainer optimizer-step smoke on Citrus."
    )
    parser.add_argument(
        "--use_cuda",
        action="store_true",
        help="Run on CUDA instead of forcing CPU. Fails if CUDA is unavailable.",
    )
    return parser.parse_args()


def parse_smoke_options(args: argparse.Namespace):
    option_args = [
        "smoke_root_citrus_one_step_train.py",
        "--dataset", "citrus",
        "--batch_size", "1",
        "--num_workers", "0",
        "--num_epochs", "1",
        "--weights_init", "scratch",
        "--log_dir", "tmp_trainer_wiring_smoke",
        "--model_name", "root_citrus_one_step_train_smoke",
        "--log_frequency", "999999",
    ]
    if args.use_cuda:
        if not torch.cuda.is_available():
            raise RuntimeError("--use_cuda was requested but torch.cuda.is_available() is false")
    else:
        option_args.append("--no_cuda")
    sys.argv = option_args
    return LiteMonoOptions().parse()


def close_writers(trainer: Trainer) -> None:
    for writer in getattr(trainer, "writers", {}).values():
        writer.close()


def first_encoder_param(trainer: Trainer) -> torch.nn.Parameter:
    return next(trainer.models["encoder"].parameters())


def assert_finite_gradients(trainer: Trainer) -> None:
    checked = 0
    for parameters in (trainer.parameters_to_train, trainer.parameters_to_train_pose):
        for parameter in parameters:
            if parameter.grad is None:
                continue
            if not torch.isfinite(parameter.grad).all():
                raise AssertionError("Found non-finite gradient in one-step Citrus smoke")
            checked += 1
    if checked == 0:
        raise AssertionError("No gradients were produced in one-step Citrus smoke")


def main() -> None:
    args = parse_args()
    opts = parse_smoke_options(args)
    trainer = Trainer(opts)
    try:
        trainer.set_train()
        batch = next(iter(trainer.train_loader))

        reference_param = first_encoder_param(trainer)
        before = reference_param.detach().clone()

        outputs, losses = trainer.process_batch(batch)
        loss = losses["loss"]
        if not torch.isfinite(loss):
            raise AssertionError(f"Expected finite training loss, got {float(loss)}")

        trainer.model_optimizer.zero_grad()
        if trainer.use_pose_net:
            trainer.model_pose_optimizer.zero_grad()
        loss.backward()
        assert_finite_gradients(trainer)
        trainer.model_optimizer.step()
        if trainer.use_pose_net:
            trainer.model_pose_optimizer.step()

        after = reference_param.detach()
        max_param_delta = float(torch.max(torch.abs(after - before)))
        if not np.isfinite(max_param_delta) or max_param_delta <= 0:
            raise AssertionError(
                f"Expected encoder parameters to change, max delta={max_param_delta}"
            )

        print("Root Citrus one-step training smoke passed.")
        print(f"  data_path:          {trainer.opt.data_path}")
        print(f"  split:              {trainer.opt.split}")
        print(f"  depth_metric_crop:  {trainer.opt.depth_metric_crop}")
        print(f"  device:             {trainer.device}")
        print(f"  train samples:      {len(trainer.train_loader.dataset)}")
        print(f"  val samples:        {len(trainer.val_loader.dataset)}")
        print(f"  loss before step:   {float(loss):.6f}")
        print(f"  max param delta:    {max_param_delta:.10f}")
    finally:
        close_writers(trainer)


if __name__ == "__main__":
    main()
