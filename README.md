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

You can also use a high-res dataset like: https://amsacta.unibo.it/id/eprint/8431/

### Other

```sh
mkdir segmentations
mkdir out
```

## Run TotalSegmentator

```sh
python src/conversion.py data/HFValid_Collection_v3/Subjects/Pat001/Pat001.nrrd data/HFValid_Collection_v3/Subjects/Pat001/ct.nii.gz
TotalSegmentator -i data/HFValid_Collection_v3/Subjects/Pat001/ct.nii.gz -o segmentations/HFValid/001 -p
```

## Refine & View data

Refine the data (e.g. using smoothing):

```sh
python src/refining/smoothing.py segmentations/HFValid/001/femur_right.nii.gz out/upscale_HFValid_femur_2x.nii.gz -z 2
```

Find the center of the segmentation:

```sh
python src/find_center.py out/upscale_HFValid_femur_2x.nii.gz
```

To view it, slice the resulting 3D image at the center (using the correct axis):

```sh
python src/view_nii.py out/upscale_HFValid_femur_2x.nii.gz out/test.png --slice 347 --axis 1
```

You can also use [3D Slicer](https://www.slicer.org/) to view the nii files directly.
