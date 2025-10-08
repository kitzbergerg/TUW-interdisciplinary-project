## Setup

```sh
uv venv
uv add torch torchvision --default-index https://download.pytorch.org/whl/rocm6.4
uv sync
```

## Run

```sh
rm -rf segmentations/
use ./.venv/bin/activate.nu
TotalSegmentator -i data/s0011/ct.nii.gz -o segmentations -p
```