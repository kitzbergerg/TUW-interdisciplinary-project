## Setup

### Dependencies

Using `uv`:

```sh
uv venv
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm6.4
uv sync
```

Activate the venv:

```sh
. ./.venv/bin/activate
```

### Download data

Here is a small dataset to play around with: https://doi.org/10.5281/zenodo.10047263
Put this in `data/`:

```sh
mkdir data
cd data
wget https://zenodo.org/records/10047263/files/Totalsegmentator_dataset_small_v201.zip?download=1
unzip Totalsegmentator_dataset_small_v201.zip
```

### Other

```sh
mkdir segmentations
mkdir out
```

## Run TotalSegmentator

```sh
TotalSegmentator -i data/s1366/ct.nii.gz -o segmentations/s1366 -p
```

## Refine & View data

Refine the data (e.g. using smoothing):

```sh
python src/refining/smoothing.py segmentations/s1366/femur_left.nii.gz out/upscale_2x.nii.gz -z 2
```

Find the center of the segmentation:

```sh
python src/find_center.py out/upscale_2x.nii.gz
```

To view it, slice the resulting 3D image at the center (using the correct axis):

```sh
python src/view_nii.py segmentations/s1366/femur_left.nii.gz out/seg_femur.png --slice 173 --axis 1
```
