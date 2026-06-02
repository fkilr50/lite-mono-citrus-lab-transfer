# File: download_citrusfarm_seq_01_rgb_depth.py
# Download ZED bags aligned to selected base (LiDAR) bag time window.

import wget
import os
import yaml
import requests
import hashlib
from datetime import datetime, timedelta

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))


def ComputeMD5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def ParseBagStartTime(filename):
    base = os.path.basename(filename)
    parts = base.split("_")
    # Expected pattern: <modality>_YYYY-MM-DD-HH-MM-SS_<index>.bag
    if len(parts) < 3:
        return None
    try:
        return datetime.strptime(parts[1], "%Y-%m-%d-%H-%M-%S")
    except ValueError:
        return None


def SortFilesByBagTime(file_list):
    return sorted(file_list, key=lambda f: (ParseBagStartTime(f) or datetime.max, f))


def LocalPath(relative_path):
    return os.path.join(SCRIPT_ROOT, relative_path.replace("/", os.sep))


def InferReferenceSpanSeconds(reference_files, default_seconds=540):
    times = [ParseBagStartTime(f) for f in reference_files]
    times = [t for t in times if t is not None]

    if len(times) < 2:
        return default_seconds

    times.sort()
    intervals = []
    for i in range(1, len(times)):
        delta_sec = (times[i] - times[i - 1]).total_seconds()
        if delta_sec > 0:
            intervals.append(delta_sec)

    if not intervals:
        return default_seconds

    intervals.sort()
    return int(intervals[len(intervals) // 2])


def SelectAlignedModalityFiles(
    filenames,
    target_prefix,
    reference_prefix,
    max_reference_blocks=3,
    default_reference_span_seconds=540,
    tail_seconds=60,
):
    reference_files = SortFilesByBagTime(
        [f for f in filenames if f.startswith(reference_prefix)]
    )
    selected_reference = reference_files[:max_reference_blocks]

    target_files = SortFilesByBagTime(
        [f for f in filenames if f.startswith(target_prefix)]
    )

    if not selected_reference:
        return target_files, None, None, []

    window_start = ParseBagStartTime(selected_reference[0])
    last_reference_start = ParseBagStartTime(selected_reference[-1])

    if window_start is None or last_reference_start is None:
        return target_files, None, None, selected_reference

    span_seconds = InferReferenceSpanSeconds(
        selected_reference, default_seconds=default_reference_span_seconds
    )
    window_end = last_reference_start + timedelta(seconds=span_seconds + tail_seconds)

    aligned = []
    for f in target_files:
        ts = ParseBagStartTime(f)
        if ts is None:
            continue
        if window_start <= ts <= window_end:
            aligned.append(f)

    if not aligned:
        # Conservative fallback: keep at least one target file if timestamps were unusual.
        aligned = target_files[:1]

    return aligned, window_start, window_end, selected_reference


def DownloadFiles(
    base_url,
    folder_dict,
    folder_list,
    modality_list,
    max_blocks=3,
    reference_modality="base",
    default_reference_span_seconds=540,
    tail_seconds=60,
):
    data_folders = [
        "01_13B_Jackal",
        "02_13B_Jackal",
        "03_13B_Jackal",
        "04_13D_Jackal",
        "05_13D_Jackal",
        "06_14B_Jackal",
        "07_14B_Jackal",
    ]
    files_to_verify = []

    # Download Phase
    for folder in folder_list:
        filenames = folder_dict.get(folder, {})

        # Create folder locally if not exists
        local_folder = LocalPath(folder)
        if not os.path.exists(local_folder):
            os.makedirs(local_folder)

        # Filter target files before downloading
        if folder in data_folders:
            if len(modality_list) == 1 and modality_list[0] == "zed":
                (
                    target_files,
                    window_start,
                    window_end,
                    selected_reference,
                ) = SelectAlignedModalityFiles(
                    filenames.keys(),
                    target_prefix="zed",
                    reference_prefix=reference_modality,
                    max_reference_blocks=max_blocks,
                    default_reference_span_seconds=default_reference_span_seconds,
                    tail_seconds=tail_seconds,
                )

                print(
                    f"\n[{folder}] Reference {reference_modality} files ({len(selected_reference)}):"
                )
                for ref in selected_reference:
                    print(f"  {ref}")

                if window_start and window_end:
                    print(
                        f"[{folder}] Selecting zed files in window: "
                        f"{window_start} -> {window_end}"
                    )
                print(f"[{folder}] Selected zed files: {len(target_files)}")
            else:
                target_files = [
                    f
                    for f in filenames.keys()
                    if any(f.startswith(m) for m in modality_list)
                ]
                target_files = SortFilesByBagTime(target_files)[:max_blocks]
        else:
            # If it's a Calibration or Ground Truth folder, keep everything
            target_files = filenames.keys()

        for filename in target_files:
            local_file_path = os.path.join(local_folder, filename)

            # Skip download if file already exists
            if os.path.exists(local_file_path):
                print(f"File {local_file_path} already exists, skipping download.")
                files_to_verify.append((folder, filename))
                continue

            # Generate the download URL
            download_url = f"{base_url}/{folder}/{filename}"

            # Download the file into the specified folder
            print(f"Downloading {local_file_path}")
            wget.download(download_url, local_file_path)
            print()

            # Add to list of files to verify
            files_to_verify.append((folder, filename))

    # MD5 Verification Phase
    print(f"\nVerifying MD5 for downloaded files.")
    for folder, filename in files_to_verify:
        local_file_path = os.path.join(LocalPath(folder), filename)
        expected_md5 = folder_dict[folder][filename]["md5"]
        computed_md5 = ComputeMD5(local_file_path)

        while expected_md5 != computed_md5:
            print(
                f"MD5 mismatch for {local_file_path}. Removing current file and Redownloading."
            )
            os.remove(local_file_path)
            download_url = f"{base_url}/{folder}/{filename}"
            wget.download(download_url, local_file_path)
            print()
            print(f"Redownloaded {local_file_path}. Verifying again.")
            computed_md5 = ComputeMD5(local_file_path)

        print(f"MD5 verified for {local_file_path}.")
    print(f"MD5 verified for all downloaded files.")


if __name__ == "__main__":
    # Base URL for the S3 bucket and YAML config
    base_url = "https://ucr-robotics.s3.us-west-2.amazonaws.com/citrus-farm-dataset"
    yaml_url = "https://raw.githubusercontent.com/UCR-Robotics/Citrus-Farm-Dataset/main/dataset_file_list.yaml"

    # Download and parse YAML config file
    response = requests.get(yaml_url)
    config_data = yaml.safe_load(response.text)

    folder_dict = config_data.get("citrus-farm-dataset", {})

    # Target only Sequence 01 and its related calibration/ground truth
    folder_list = [
        "01_13B_Jackal",
        "Calibration",
        "Calibration/config",
        "Calibration/data",
        "Calibration/results",
        "Calibration/scripts",
        "ground_truth/01_13B_Jackal",
    ]

    # Target only the ZED camera modality
    modality_list = ["zed"]

    # Number of base files used to define the download time window
    max_blocks = 1

    # Base blocks in Sequence 01 are around 9 minutes apart; use this as default span.
    default_reference_span_seconds = 540

    # Small buffer to avoid clipping the final overlapping zed bag.
    tail_seconds = 60

    DownloadFiles(
        base_url,
        folder_dict,
        folder_list,
        modality_list,
        max_blocks=max_blocks,
        reference_modality="base",
        default_reference_span_seconds=default_reference_span_seconds,
        tail_seconds=tail_seconds,
    )
