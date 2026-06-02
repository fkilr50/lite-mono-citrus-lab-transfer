from __future__ import annotations

from citrus_prepared_dataset import CitrusPreparedDataset, repo_root


def mean_abs_color_aug_delta(sample: dict, frame_id: int = 0) -> float:
    return float((sample[("color_aug", frame_id, 0)] - sample[("color", frame_id, 0)]).abs().mean())


def main() -> None:
    dataset_workspace = repo_root() / "citrus_project" / "dataset_workspace"

    train_dataset = CitrusPreparedDataset(
        dataset_workspace=dataset_workspace,
        split="train",
        image_size=(640, 192),
        frame_ids=[0, -1, 1],
        include_metadata=False,
        is_train=True,
        color_augmentation_probability=1.0,
    )
    val_dataset = CitrusPreparedDataset(
        dataset_workspace=dataset_workspace,
        split="val",
        image_size=(640, 192),
        frame_ids=[0, -1, 1],
        include_metadata=False,
        is_train=False,
        color_augmentation_probability=1.0,
    )

    train_sample = train_dataset[0]
    val_sample = val_dataset[0]

    train_delta = mean_abs_color_aug_delta(train_sample)
    val_delta = mean_abs_color_aug_delta(val_sample)

    if train_delta <= 0:
        raise AssertionError(
            "Expected train color_aug to differ from color when augmentation probability is 1"
        )
    if val_delta != 0:
        raise AssertionError("Expected validation color_aug to match color exactly")

    for frame_id in (-1, 0, 1):
        shape = tuple(train_sample[("color", frame_id, 0)].shape)
        aug_shape = tuple(train_sample[("color_aug", frame_id, 0)].shape)
        if shape != aug_shape:
            raise AssertionError(
                f"color/color_aug shape mismatch for frame {frame_id}: {shape} vs {aug_shape}"
            )

    print("Citrus color augmentation smoke passed.")
    print(f"  train samples:       {len(train_dataset)}")
    print(f"  val samples:         {len(val_dataset)}")
    print(f"  train mean abs diff: {train_delta:.6f}")
    print(f"  val mean abs diff:   {val_delta:.6f}")


if __name__ == "__main__":
    main()
