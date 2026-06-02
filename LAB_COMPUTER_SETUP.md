# Lab Computer Setup

This repo is a clean transfer copy for running the Citrus/Lite-Mono work on a lab machine without carrying local datasets, weights, caches, or bulky training outputs.

## 1. Clone Into Large Storage

Use a large drive, not a small home partition.

```bash
mkdir -p /data/$USER/projects
cd /data/$USER/projects
git clone <your-github-repo-url> lite-Mono
cd lite-Mono
```

If the lab does not have `/data`, check available storage first:

```bash
df -h
```

## 2. Use tmux

```bash
tmux new -s citrus
```

Detach while keeping the job alive:

```text
Ctrl+b, then d
```

Reattach:

```bash
tmux attach -t citrus
```

## 3. Environment

If Conda exists:

```bash
conda env create -f environment.yml
conda activate lite-mono
```

If Conda is not installed, install Miniforge in your user folder:

```bash
cd ~
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
source ~/miniforge3/etc/profile.d/conda.sh
```

Then rerun:

```bash
cd /data/$USER/projects/lite-Mono
conda env create -f environment.yml
conda activate lite-mono
```

Check GPU:

```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"
```

## 4. Dataset Download Order

From repo root:

```bash
python citrus_project/dataset_workspace/download_citrusfarm_seq_01_lidar.py | tee lidar_download.log
python citrus_project/dataset_workspace/download_citrusfarm_seq_01_rgb_depth.py | tee rgb_depth_download.log
```

The files will download under:

```text
citrus_project/dataset_workspace/
```

Check the actual drive:

```bash
realpath citrus_project/dataset_workspace
df -h citrus_project/dataset_workspace
```

## 5. Dataset Preparation Order

After downloads finish:

```bash
python citrus_project/dataset_workspace/extract_left_rgbd_from_raw.py
python citrus_project/dataset_workspace/extract_lidar_from_raw.py
python citrus_project/dataset_workspace/audit_projection_alignment.py --max_samples 12 --output_dir projection_alignment_audit/time_spread_visual_12
python citrus_project/dataset_workspace/build_training_dataset.py
```

The prepared training dataset should appear under:

```text
citrus_project/dataset_workspace/prepared_training_dataset/
```

Expected split size from the current project record:

```text
train = 4311
val   = 564
test  = 407
total = 5282
```

## 6. Important Notes

- Read `AGENTS.md` first for current project status and decisions.
- LiDAR is used for training/evaluation labels; inference remains RGB-only.
- Do not commit downloaded bags, extracted data, prepared datasets, weights, or long training outputs.
- For the next experiment, remember to run checkpoint scans before trusting a final epoch.
