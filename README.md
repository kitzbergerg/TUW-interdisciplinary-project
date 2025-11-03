# Setup

## Dependencies

Using `uv`:

```sh
uv venv
uv sync
```

Activate the venv:

```sh
source .venv/bin/activate
```

## Create directory structure

```shell
mkdir data
mkdir data/raw
mkdir data/preprocessed
mkdir data/segmentations
mkdir data/nnUNet
mkdir data/nnUNet/raw
mkdir data/nnUNet/preprocessed
mkdir data/nnUNet/results
```

## Download data

Here is a small dataset to play around with: https://doi.org/10.5281/zenodo.10047263
Put this in `data/raw/`:

```sh
cd data/raw/
wget https://zenodo.org/records/10047263/files/Totalsegmentator_dataset_small_v201.zip?download=1
unzip Totalsegmentator_dataset_small_v201.zip
```

You can also use a high-res dataset like: https://amsacta.unibo.it/id/eprint/8431/


```sh
cd data/raw/
wget https://amsacta.unibo.it/id/eprint/8431/31/HFValid_Collection_v3.zip
unzip HFValid_Collection_v3.zip

cd HFValid_Collection_v3
unzip Subjects
```

## View data

You can also use [3D Slicer](https://www.slicer.org/) to view the nii files directly.

`find_center` and `view_nii` are no longer used, but are kept for reference.

# Refine

## Smoothing

```sh
python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl data/preprocessed/label_high_res.nii.gz -v 0.75
python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl data/preprocessed/label_low_res.nii.gz -v 1.5
python src/resample.py data/preprocessed/label_low_res.nii.gz data/preprocessed/upsampled.nii.gz -z 2
python src/refining/smoothing.py data/preprocessed/upsampled.nii.gz data/preprocessed/smoothed.nii.gz -s 3
```

## nnUNet

### Preprocessing

First generate the data:

```sh
python src/nnUNet/prepare_inputs.py data/raw/HFValid_Collection_v3/Subjects/ data/nnUNet/raw/Dataset103_FemurRefine/
```

Set environment variables:

```sh
nnUNet_raw="data/nnUNet/raw"
nnUNet_preprocessed="data/nnUNet/preprocessed"
nnUNet_results="data/nnUNet/results"
```

Run preprocessing:

```sh
nnUNetv2_plan_and_preprocess -d 102 --verify_dataset_integrity
```

### Training

```sh
nnUNet_compile="False" nnUNetv2_train 102 3d_fullres 0
```

### Inference

```sh
nnUNetv2_predict -i nnUNet_test/ -o nnUNet_predict/ -d 102 -c 3d_fullres -f 0 -chk checkpoint_best.pth
```

## Comparison/Evaluation

To compare segmentations you can use the SlicerRT extension for 3D Slicer.  
Using the Segment Comparison model you can compute the Dice Similarity.

In code, you can do the following.  
Note that the stl->nifti conversion uses voxel spacing 0.5 by default.

```sh
python src/compare.py data/raw/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl data/preprocessed/label_high_res.nii.gz data/preprocessed/label_low_res.nii.gz data/preprocessed/upsampled.nii.gz data/preprocessed/smoothed.nii.gz
```

For more detailed comparison, you can use '-v 0.3' to change spacing:

# TotalSegmentator

```sh
python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat001/Pat001.nrrd data/segmentations/ct.nii.gz
TotalSegmentator -i data/segmentations/ct.nii.gz -o data/segmentations/ -p -rs femur_left -rs femur_right

python src/resample.py data/segmentations/femur_right.nii.gz data/segmentations/femur_right_resampled.nii.gz -z 2
python src/nnUNet/preprocess_inference.py data/segmentations/ct.nii.gz data/segmentations/femur_right_resampled.nii.gz data/nnUNet/test/femur_001_0000.nii.gz data/nnUNet/test/femur_001_0001.nii.gz
nnUNetv2_predict -i data/nnUNet/test/ -o data/nnUNet/predictions/ -d 102 -c 3d_fullres -f 0 -chk checkpoint_best.pth
```