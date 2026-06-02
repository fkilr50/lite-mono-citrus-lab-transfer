from __future__ import annotations

import csv
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms
from torchvision.transforms import functional as transform_functional


CITRUS_ZED_LEFT_INTRINSICS = (
    527.5591059906969,
    528.5624579927512,
    647.1975009993375,
    357.2476935284654,
)
CITRUS_ZED_LEFT_SIZE = (1280, 720)  # width, height


@dataclass(frozen=True)
class CitrusPreparedRecord:
    rgb_rel: str
    dense_rel: str
    valid_mask_rel: str
    session: str
    timestamp_ns: int
    split_index: int
    manifest_row: Dict[str, str]


@dataclass(frozen=True)
class CitrusTemporalSample:
    target: CitrusPreparedRecord
    frames: Dict[int, CitrusPreparedRecord]
    neighbor_delta_ms: Dict[int, float]


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


def extract_timestamp(filename: str) -> int:
    base = os.path.basename(filename)
    return int(base.split("_")[-1].split(".")[0])


def extract_session_token(filename: str) -> Optional[str]:
    base = os.path.basename(filename)
    parts = base.split("_")
    if len(parts) >= 5 and parts[3] == "bag":
        return parts[2]
    return None


def citrus_normalized_K() -> np.ndarray:
    fx, fy, cx, cy = CITRUS_ZED_LEFT_INTRINSICS
    native_width, native_height = CITRUS_ZED_LEFT_SIZE
    return np.array(
        [
            [fx / native_width, 0.0, cx / native_width, 0.0],
            [0.0, fy / native_height, cy / native_height, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )


def citrus_pixel_K(image_size: Tuple[int, int]) -> np.ndarray:
    """Return a 4x4 pixel-space K matrix for a resized Citrus RGB tensor."""
    width, height = image_size
    K = citrus_normalized_K().copy()
    K[0, :] *= width
    K[1, :] *= height
    return K


def image_to_tensor(image: Image.Image) -> torch.Tensor:
    array = np.asarray(image, dtype=np.float32) / 255.0
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError(f"Expected RGB image array, got shape {array.shape}")
    return torch.from_numpy(array).permute(2, 0, 1).contiguous()


def resize_image(image: Image.Image, size: Optional[Tuple[int, int]]) -> Image.Image:
    if size is None:
        return image
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
    return image.resize(size, resample)


def scaled_size(image_size: Tuple[int, int], scale: int) -> Tuple[int, int]:
    width, height = image_size
    divisor = 2 ** scale
    return (width // divisor, height // divisor)


def ms_delta(left: CitrusPreparedRecord, right: CitrusPreparedRecord) -> float:
    return abs(left.timestamp_ns - right.timestamp_ns) / 1e6


class CitrusPreparedDataset(Dataset):
    """Loads the prepared Citrus RGB, dense LiDAR depth, and valid-mask artifacts.

    By default this returns target-only samples with metadata for inspection.
    Passing temporal frame_ids such as (0, -1, 1) returns same-split,
    same-session frame bundles for the next training-integration slice.
    """

    def __init__(
        self,
        dataset_workspace: Optional[Path] = None,
        prepared_name: str = "prepared_training_dataset",
        split: str = "train",
        image_size: Optional[Tuple[int, int]] = None,
        load_depth: bool = True,
        frame_ids: Optional[Sequence[int]] = None,
        num_scales: int = 4,
        max_neighbor_delta_ms: float = 200.0,
        require_full_sequence: bool = True,
        include_metadata: bool = True,
        is_train: bool = False,
        color_augmentation_probability: float = 0.5,
    ) -> None:
        if split not in {"train", "val", "test"}:
            raise ValueError(f"Unknown split {split!r}; expected train, val, or test")
        if not 0.0 <= color_augmentation_probability <= 1.0:
            raise ValueError(
                "color_augmentation_probability must be between 0 and 1, "
                f"got {color_augmentation_probability}"
            )

        if dataset_workspace is None:
            dataset_workspace = repo_root() / "citrus_project" / "dataset_workspace"
        self.dataset_workspace = Path(dataset_workspace).resolve()
        self.prepared_dir = self.dataset_workspace / prepared_name
        self.split = split
        self.image_size = image_size
        self.load_depth = load_depth
        self.frame_ids = tuple(frame_ids if frame_ids is not None else (0,))
        self.num_scales = num_scales
        self.max_neighbor_delta_ms = max_neighbor_delta_ms
        self.require_full_sequence = require_full_sequence
        self.include_metadata = include_metadata
        self.is_train = is_train
        self.color_augmentation_probability = color_augmentation_probability
        try:
            self.brightness = (0.8, 1.2)
            self.contrast = (0.8, 1.2)
            self.saturation = (0.8, 1.2)
            self.hue = (-0.1, 0.1)
            transforms.ColorJitter.get_params(
                self.brightness, self.contrast, self.saturation, self.hue
            )
        except TypeError:
            self.brightness = 0.2
            self.contrast = 0.2
            self.saturation = 0.2
            self.hue = 0.1
        if 0 not in self.frame_ids:
            raise ValueError("frame_ids must include 0 for the target frame")
        if self.num_scales < 1:
            raise ValueError("num_scales must be at least 1")

        split_path = self.prepared_dir / "splits" / f"{split}_pairs.txt"
        manifest_path = self.prepared_dir / "metrics" / "all_samples.csv"
        if not split_path.is_file():
            raise FileNotFoundError(f"Missing split file: {split_path}")
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Missing manifest file: {manifest_path}")

        manifest = load_manifest(manifest_path)
        self.records = self._build_records(load_split_pairs(split_path), manifest)
        self.temporal_samples = self._build_temporal_samples(self.records)

    @staticmethod
    def _build_records(
        pairs: Sequence[Tuple[str, str]],
        manifest: Dict[str, Dict[str, str]],
    ) -> List[CitrusPreparedRecord]:
        records = []
        for index, (rgb_rel, dense_rel) in enumerate(pairs):
            if rgb_rel not in manifest:
                raise KeyError(f"{rgb_rel} appears in split file but not all_samples.csv")
            row = manifest[rgb_rel]
            manifest_dense_rel = row["dense_rel"]
            if manifest_dense_rel != dense_rel:
                raise ValueError(
                    "Split dense path does not match manifest dense path:\n"
                    f"  split:    {dense_rel}\n"
                    f"  manifest: {manifest_dense_rel}"
                )
            records.append(
                CitrusPreparedRecord(
                    rgb_rel=rgb_rel,
                    dense_rel=dense_rel,
                    valid_mask_rel=row["valid_mask_rel"],
                    session=str(row.get("session") or extract_session_token(rgb_rel) or ""),
                    timestamp_ns=extract_timestamp(rgb_rel),
                    split_index=index,
                    manifest_row=row,
                )
            )
        return records

    def _build_temporal_samples(
        self,
        records: Sequence[CitrusPreparedRecord],
    ) -> List[CitrusTemporalSample]:
        if self.frame_ids == (0,):
            return [
                CitrusTemporalSample(
                    target=record,
                    frames={0: record},
                    neighbor_delta_ms={0: 0.0},
                )
                for record in records
            ]

        by_session: Dict[str, List[CitrusPreparedRecord]] = {}
        for record in records:
            by_session.setdefault(record.session, []).append(record)
        for session_records in by_session.values():
            session_records.sort(key=lambda item: (item.timestamp_ns, item.rgb_rel))

        samples = []
        for session_records in by_session.values():
            for index, target in enumerate(session_records):
                frames = {0: target}
                deltas = {0: 0.0}
                valid = True
                for frame_id in self.frame_ids:
                    if frame_id == 0:
                        continue
                    neighbor_index = index + frame_id
                    if neighbor_index < 0 or neighbor_index >= len(session_records):
                        valid = False
                        break
                    neighbor = session_records[neighbor_index]
                    delta_ms = ms_delta(target, neighbor)
                    if delta_ms > self.max_neighbor_delta_ms:
                        valid = False
                        break
                    frames[frame_id] = neighbor
                    deltas[frame_id] = delta_ms

                if valid or not self.require_full_sequence:
                    samples.append(
                        CitrusTemporalSample(
                            target=target,
                            frames=frames,
                            neighbor_delta_ms=deltas,
                        )
                    )
        samples.sort(key=lambda sample: sample.target.split_index)
        return samples

    def __len__(self) -> int:
        return len(self.temporal_samples)

    def _workspace_path(self, relative_path: str) -> Path:
        return self.dataset_workspace / relative_path

    def _make_color_aug(self) -> Callable[[Image.Image], Image.Image]:
        if (
            not self.is_train
            or self.color_augmentation_probability <= 0
            or random.random() >= self.color_augmentation_probability
        ):
            return lambda image: image
        params = transforms.ColorJitter.get_params(
            self.brightness, self.contrast, self.saturation, self.hue
        )
        if callable(params):
            return params

        transform_order, brightness, contrast, saturation, hue = params

        def apply_color_jitter(image: Image.Image) -> Image.Image:
            for transform_id in transform_order:
                transform_id = int(transform_id)
                if transform_id == 0 and brightness is not None:
                    image = transform_functional.adjust_brightness(image, brightness)
                elif transform_id == 1 and contrast is not None:
                    image = transform_functional.adjust_contrast(image, contrast)
                elif transform_id == 2 and saturation is not None:
                    image = transform_functional.adjust_saturation(image, saturation)
                elif transform_id == 3 and hue is not None:
                    image = transform_functional.adjust_hue(image, hue)
            return image

        return apply_color_jitter

    def _load_color_pyramid(
        self,
        record: CitrusPreparedRecord,
        color_aug: Callable[[Image.Image], Image.Image],
    ) -> Tuple[
        Dict[int, torch.Tensor],
        Dict[int, torch.Tensor],
        Tuple[int, int],
        Tuple[int, int],
    ]:
        rgb_path = self._workspace_path(record.rgb_rel)
        with Image.open(rgb_path) as image:
            rgb = image.convert("RGB")
            native_size = rgb.size
            base_size = self.image_size or native_size
            pyramid = {}
            aug_pyramid = {}
            for scale in range(self.num_scales):
                resized = resize_image(rgb, scaled_size(base_size, scale))
                pyramid[scale] = image_to_tensor(resized)
                aug_pyramid[scale] = image_to_tensor(color_aug(resized))
        return pyramid, aug_pyramid, native_size, base_size

    def __getitem__(self, index: int) -> Dict[str, object]:
        temporal_sample = self.temporal_samples[index]
        record = temporal_sample.target
        color_pyramids = {}
        color_aug_pyramids = {}
        native_size = None
        base_size = None
        color_aug = self._make_color_aug()
        for frame_id in self.frame_ids:
            if frame_id not in temporal_sample.frames:
                continue
            pyramid, aug_pyramid, frame_native_size, frame_base_size = self._load_color_pyramid(
                temporal_sample.frames[frame_id],
                color_aug,
            )
            color_pyramids[frame_id] = pyramid
            color_aug_pyramids[frame_id] = aug_pyramid
            if frame_id == 0:
                native_size = frame_native_size
                base_size = frame_base_size

        if native_size is None or base_size is None:
            raise RuntimeError(f"Target frame missing from temporal sample at index {index}")

        K0 = citrus_pixel_K(base_size)
        inv_K0 = np.linalg.pinv(K0)

        sample: Dict[str, object] = {
            "color": color_pyramids[0][0],
            "K": torch.from_numpy(K0),
            "inv_K": torch.from_numpy(inv_K0.astype(np.float32)),
            "K_normalized": torch.from_numpy(citrus_normalized_K()),
            "index": torch.tensor(index, dtype=torch.int64),
            "split_index": torch.tensor(record.split_index, dtype=torch.int64),
            "timestamp_ns": torch.tensor(record.timestamp_ns, dtype=torch.int64),
            "native_size_hw": torch.tensor(
                [native_size[1], native_size[0]], dtype=torch.int64
            ),
            "image_size_hw": torch.tensor(
                [base_size[1], base_size[0]], dtype=torch.int64
            ),
            "frame_ids": torch.tensor(self.frame_ids, dtype=torch.int64),
        }

        if self.include_metadata:
            sample.update(
                {
                    "rgb_rel": record.rgb_rel,
                    "dense_rel": record.dense_rel,
                    "valid_mask_rel": record.valid_mask_rel,
                    "session": record.session,
                    "metadata": {
                        key: str(value) for key, value in record.manifest_row.items()
                    },
                    "frame_rgb_rel": {
                        str(frame_id): temporal_sample.frames[frame_id].rgb_rel
                        for frame_id in temporal_sample.frames
                    },
                    "neighbor_delta_ms": {
                        str(frame_id): torch.tensor(delta_ms, dtype=torch.float32)
                        for frame_id, delta_ms in temporal_sample.neighbor_delta_ms.items()
                    },
                }
            )

        for scale in range(self.num_scales):
            K = citrus_pixel_K(scaled_size(base_size, scale))
            inv_K = np.linalg.pinv(K)
            sample[("K", scale)] = torch.from_numpy(K)
            sample[("inv_K", scale)] = torch.from_numpy(inv_K.astype(np.float32))

        for frame_id, pyramid in color_pyramids.items():
            for scale, color in pyramid.items():
                sample[("color", frame_id, scale)] = color
                sample[("color_aug", frame_id, scale)] = color_aug_pyramids[frame_id][scale]

        if self.load_depth:
            dense = load_npz_array(self._workspace_path(record.dense_rel)).astype(np.float32)
            valid_mask = load_npz_array(self._workspace_path(record.valid_mask_rel))
            valid_mask = (valid_mask > 0).astype(np.float32)
            label_mask = (
                (valid_mask > 0)
                & np.isfinite(dense)
                & (dense > 0)
            ).astype(np.float32)

            sample["depth_gt"] = torch.from_numpy(dense[None, ...])
            sample["valid_mask"] = torch.from_numpy(valid_mask[None, ...])
            sample["label_mask"] = torch.from_numpy(label_mask[None, ...])

        return sample
