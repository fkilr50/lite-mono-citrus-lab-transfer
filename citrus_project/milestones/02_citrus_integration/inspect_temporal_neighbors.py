from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from citrus_prepared_dataset import (
    extract_session_token,
    extract_timestamp,
    load_manifest,
    load_split_pairs,
    repo_root,
)


@dataclass(frozen=True)
class TemporalRecord:
    split: str
    split_index: int
    rgb_rel: str
    dense_rel: str
    session: str
    timestamp_ns: int


@dataclass
class DirectionStats:
    available: int = 0
    within_threshold: int = 0
    too_far: int = 0
    missing: int = 0
    global_cross_split: int = 0
    global_same_split: int = 0
    global_missing: int = 0
    deltas_ms: List[float] = None

    def __post_init__(self) -> None:
        if self.deltas_ms is None:
            self.deltas_ms = []


def load_split_records(
    prepared_dir: Path,
    manifest: Dict[str, Dict[str, str]],
    split: str,
) -> List[TemporalRecord]:
    split_path = prepared_dir / "splits" / f"{split}_pairs.txt"
    pairs = load_split_pairs(split_path)
    records = []
    for index, (rgb_rel, dense_rel) in enumerate(pairs):
        if rgb_rel not in manifest:
            raise KeyError(f"{rgb_rel} appears in {split_path} but not all_samples.csv")
        row = manifest[rgb_rel]
        if row["dense_rel"] != dense_rel:
            raise ValueError(
                "Split dense path does not match manifest dense path:\n"
                f"  split:    {dense_rel}\n"
                f"  manifest: {row['dense_rel']}"
            )
        session = row.get("session") or extract_session_token(rgb_rel) or "unknown"
        records.append(
            TemporalRecord(
                split=split,
                split_index=index,
                rgb_rel=rgb_rel,
                dense_rel=dense_rel,
                session=str(session),
                timestamp_ns=extract_timestamp(rgb_rel),
            )
        )
    return records


def group_by_session(records: Iterable[TemporalRecord]) -> Dict[str, List[TemporalRecord]]:
    grouped: Dict[str, List[TemporalRecord]] = defaultdict(list)
    for record in records:
        grouped[record.session].append(record)
    for session_records in grouped.values():
        session_records.sort(key=lambda item: (item.timestamp_ns, item.rgb_rel))
    return dict(grouped)


def ms_delta(left: TemporalRecord, right: TemporalRecord) -> float:
    return abs(left.timestamp_ns - right.timestamp_ns) / 1e6


def neighbor_at(
    records: Sequence[TemporalRecord],
    index: int,
    direction: str,
) -> Optional[TemporalRecord]:
    if direction == "previous":
        return records[index - 1] if index > 0 else None
    if direction == "next":
        return records[index + 1] if index + 1 < len(records) else None
    raise ValueError(f"Unknown direction: {direction}")


def update_direction_stats(
    stats: DirectionStats,
    target: TemporalRecord,
    split_neighbor: Optional[TemporalRecord],
    global_neighbor: Optional[TemporalRecord],
    max_neighbor_delta_ms: float,
) -> None:
    if split_neighbor is None:
        stats.missing += 1
    else:
        stats.available += 1
        delta_ms = ms_delta(target, split_neighbor)
        stats.deltas_ms.append(delta_ms)
        if delta_ms <= max_neighbor_delta_ms:
            stats.within_threshold += 1
        else:
            stats.too_far += 1

    if global_neighbor is None:
        stats.global_missing += 1
    elif global_neighbor.split == target.split:
        stats.global_same_split += 1
    else:
        stats.global_cross_split += 1


def summarize_deltas(deltas_ms: List[float]) -> str:
    if not deltas_ms:
        return "n/a"
    return (
        f"mean={mean(deltas_ms):.3f} ms, "
        f"median={median(deltas_ms):.3f} ms, "
        f"max={max(deltas_ms):.3f} ms"
    )


def pct(count: int, total: int) -> str:
    if total <= 0:
        return "n/a"
    return f"{count / total:.2%}"


def split_examples(
    target: TemporalRecord,
    direction: str,
    reason: str,
    examples: Dict[str, List[str]],
    limit: int,
) -> None:
    if len(examples[reason]) >= limit:
        return
    examples[reason].append(
        f"{target.split} index={target.split_index} session={target.session} "
        f"direction={direction} rgb={target.rgb_rel}"
    )


def inspect_split(
    split: str,
    records: List[TemporalRecord],
    all_by_session: Dict[str, List[TemporalRecord]],
    max_neighbor_delta_ms: float,
    example_limit: int,
) -> Dict[str, object]:
    by_session = group_by_session(records)
    global_index = {
        record.rgb_rel: idx
        for session_records in all_by_session.values()
        for idx, record in enumerate(session_records)
    }

    previous = DirectionStats()
    next_ = DirectionStats()
    safe_triplets = 0
    examples: Dict[str, List[str]] = defaultdict(list)

    for session, session_records in by_session.items():
        global_session_records = all_by_session[session]
        for index, target in enumerate(session_records):
            global_pos = global_index[target.rgb_rel]
            prev_split = neighbor_at(session_records, index, "previous")
            next_split = neighbor_at(session_records, index, "next")
            prev_global = neighbor_at(global_session_records, global_pos, "previous")
            next_global = neighbor_at(global_session_records, global_pos, "next")

            update_direction_stats(
                previous,
                target,
                prev_split,
                prev_global,
                max_neighbor_delta_ms,
            )
            update_direction_stats(
                next_,
                target,
                next_split,
                next_global,
                max_neighbor_delta_ms,
            )

            prev_ok = (
                prev_split is not None
                and ms_delta(target, prev_split) <= max_neighbor_delta_ms
            )
            next_ok = (
                next_split is not None
                and ms_delta(target, next_split) <= max_neighbor_delta_ms
            )
            if prev_ok and next_ok:
                safe_triplets += 1

            for direction, split_neighbor, global_neighbor in (
                ("previous", prev_split, prev_global),
                ("next", next_split, next_global),
            ):
                if split_neighbor is None:
                    split_examples(target, direction, "missing_same_split", examples, example_limit)
                elif ms_delta(target, split_neighbor) > max_neighbor_delta_ms:
                    split_examples(target, direction, "too_far_same_split", examples, example_limit)

                if global_neighbor is not None and global_neighbor.split != target.split:
                    split_examples(target, direction, "global_cross_split", examples, example_limit)

    return {
        "split": split,
        "total": len(records),
        "sessions": len(by_session),
        "safe_triplets": safe_triplets,
        "previous": previous,
        "next": next_,
        "examples": dict(examples),
    }


def print_direction(name: str, stats: DirectionStats, total: int) -> None:
    print(f"  {name}:")
    print(
        f"    same-split available:       {stats.available}/{total} "
        f"({pct(stats.available, total)})"
    )
    print(
        f"    same-split within threshold:{stats.within_threshold}/{total} "
        f"({pct(stats.within_threshold, total)})"
    )
    print(f"    same-split too far:         {stats.too_far}/{total}")
    print(f"    same-split missing:         {stats.missing}/{total}")
    print(
        f"    global neighbor same split: {stats.global_same_split}/{total} "
        f"({pct(stats.global_same_split, total)})"
    )
    print(f"    global neighbor cross split:{stats.global_cross_split}/{total}")
    print(f"    global neighbor missing:    {stats.global_missing}/{total}")
    print(f"    same-split deltas:          {summarize_deltas(stats.deltas_ms)}")


def print_split_summary(summary: Dict[str, object], example_limit: int) -> None:
    total = int(summary["total"])
    print(f"\nSplit: {summary['split']}")
    print(f"  Targets:       {total}")
    print(f"  Sessions:      {summary['sessions']}")
    print(
        f"  Safe triplets: {summary['safe_triplets']}/{total} "
        f"({pct(int(summary['safe_triplets']), total)})"
    )
    print_direction("previous", summary["previous"], total)
    print_direction("next", summary["next"], total)

    examples = summary["examples"]
    if examples and example_limit > 0:
        print("  Examples:")
        for reason, rows in examples.items():
            print(f"    {reason}:")
            for row in rows:
                print(f"      {row}")


def parse_args() -> argparse.Namespace:
    default_workspace = repo_root() / "citrus_project" / "dataset_workspace"
    parser = argparse.ArgumentParser(
        description=(
            "Inspect whether prepared Citrus split samples have safe temporal "
            "neighbors for self-supervised Lite-Mono training."
        )
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
        default=["train", "val", "test"],
        choices=["train", "val", "test"],
        help="Prepared splits to inspect.",
    )
    parser.add_argument(
        "--max_neighbor_delta_ms",
        type=float,
        default=200.0,
        help="Maximum target-to-neighbor timestamp gap considered safe.",
    )
    parser.add_argument(
        "--example_limit",
        type=int,
        default=3,
        help="Maximum examples to print for each warning type.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workspace_dir = args.dataset_workspace.resolve()
    prepared_dir = workspace_dir / args.prepared_name
    manifest = load_manifest(prepared_dir / "metrics" / "all_samples.csv")
    all_records = []
    split_records = {}
    for split in ("train", "val", "test"):
        records = load_split_records(prepared_dir, manifest, split)
        split_records[split] = records
        all_records.extend(records)

    all_by_session = group_by_session(all_records)

    print("Citrus temporal-neighbor inspection")
    print(f"  Dataset workspace:       {workspace_dir}")
    print(f"  Prepared dataset:        {prepared_dir}")
    print(f"  Splits inspected:        {', '.join(args.splits)}")
    print(f"  Max neighbor delta:      {args.max_neighbor_delta_ms:.3f} ms")
    print(f"  All prepared samples:    {len(all_records)}")
    print(f"  Sessions in all splits:  {len(all_by_session)}")
    print(
        "  Rule checked: same-split, same-session previous/current/next "
        "neighbors for training safety."
    )

    for split in args.splits:
        summary = inspect_split(
            split,
            split_records[split],
            all_by_session,
            args.max_neighbor_delta_ms,
            args.example_limit,
        )
        print_split_summary(summary, args.example_limit)


if __name__ == "__main__":
    main()
