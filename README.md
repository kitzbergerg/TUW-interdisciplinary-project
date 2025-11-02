## Setup

### Dependencies

Using `uv`:

```nushell
uv venv
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm6.4
uv sync
```

Activate the venv:

```nushell
use .venv/bin/activate.nu
```

### Download data

Here is a small dataset to play around with: https://doi.org/10.5281/zenodo.10047263
Put this in `data/`:

```nushell
mkdir data
cd data
wget https://zenodo.org/records/10047263/files/Totalsegmentator_dataset_small_v201.zip?download=1
unzip Totalsegmentator_dataset_small_v201.zip
```

You can also use a high-res dataset like: https://amsacta.unibo.it/id/eprint/8431/

### Other

```nushell
mkdir segmentations
mkdir out
```

## Run TotalSegmentator

```nushell
python src/conversion.py data/HFValid_Collection_v3/Subjects/Pat001/Pat001.nrrd data/HFValid_Collection_v3/Subjects/Pat001/ct.nii.gz
TotalSegmentator -i data/HFValid_Collection_v3/Subjects/Pat001/ct.nii.gz -o segmentations/HFValid/001 -p
```

## Refine

Refine the data (e.g. using smoothing):

```nushell
python src/conversion.py data/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl out/label_high_res.nii.gz -v 0.5
python src/conversion.py data/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl out/label_low_res.nii.gz -v 1.0
python src/resample.py out/label_low_res.nii.gz out/upsampled.nii.gz -z 2
python src/refining/smoothing.py out/upsampled.nii.gz out/smoothed.nii.gz -s 3
```

## View data

Find the center of the segmentation:

```nushell
python src/find_center.py out/upscale_HFValid_femur_2x.nii.gz
```

To view it, slice the resulting 3D image at the center (using the correct axis):

```nushell
python src/view_nii.py out/upscale_HFValid_femur_2x.nii.gz out/test.png --slice 347 --axis 1
```

You can also use [3D Slicer](https://www.slicer.org/) to view the nii files directly.

## Comparison

To compare segmentations you can use the SlicerRT extension for 3D Slicer.  
Using the Segment Comparison model you can compute the Dice Similarity.

In code, you can do the following.  
Note that the stl->nifti conversion uses voxel spacing 0.5 by default.

```nushell
python src/compare.py data/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl out/label_high_res.nii.gz out/label_low_res.nii.gz out/upsampled.nii.gz out/smoothed.nii.gz
```

For more detail you can use '-v 0.3' to change spacing:

```nushell
python src/compare.py data/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl out/label_high_res.nii.gz out/label_low_res.nii.gz out/upsampled.nii.gz out/smoothed.nii.gz -v 0.3
```

## nnUNet

### Preprocessing

First generate the data:

```nushell
ls data/HFValid_Collection_v3/Subjects/ | get name | each {path parse} | each {|el| (
    mkdir ("out/" + $el.stem);
    python src/conversion.py ($el.parent + "/" + $el.stem + "/" + $el.stem + ".nrrd") ("out/" + $el.stem + "/ct.nii.gz");
    python src/conversion.py ($el.parent + "/" + $el.stem + "/" + $el.stem + ".stl") ("out/" + $el.stem + "/label_low_res.nii.gz") -v 1.5;
    python src/conversion.py ($el.parent + "/" + $el.stem + "/" + $el.stem + ".stl") ("out/" + $el.stem + "/label_high_res.nii.gz") -v 0.75;
)}

python src/nnUNet/prepare_inputs.py
```

Run preprocessing:

```nushell
$env.nnUNet_raw = "nnUNet_raw"
$env.nnUNet_preprocessed = "nnUNet_preprocessed"
$env.nnUNet_results = "nnUNet_results"

nnUNetv2_plan_and_preprocess -d 101 --verify_dataset_integrity
```

### Training

```nushell
nnUNet_compile="False" nnUNetv2_train 101 3d_fullres 0
```

### Inference

```nushell
nnUNetv2_predict -i nnUNet_test/ -o nnUNet_predict/ -d 101 -c 3d_fullres -f 0 -chk checkpoint_best.pth
```