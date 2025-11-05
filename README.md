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

# Refine

## Smoothing

```sh
python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl data/preprocessed/label_high_res.nii.gz -v 0.75
python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl data/preprocessed/label_low_res.nii.gz -v 1.5

python src/resample.py data/preprocessed/label_low_res.nii.gz data/preprocessed/upsampled_bspline.nii.gz -z 2 --use-bspline
python src/smoothing.py data/preprocessed/upsampled_bspline.nii.gz data/preprocessed/upsampled_bspline.nii.gz -s 0

python src/resample.py data/preprocessed/label_low_res.nii.gz data/preprocessed/upsampled.nii.gz -z 2
python src/smoothing.py data/preprocessed/upsampled.nii.gz data/preprocessed/smoothed.nii.gz -s 3

python src/compare.py data/raw/HFValid_Collection_v3/Subjects/Pat001/Pat001.stl data/preprocessed/label_low_res.nii.gz data/preprocessed/upsampled_bspline.nii.gz data/preprocessed/smoothed.nii.gz data/preprocessed/label_high_res.nii.gz -v 0.3
```

## nnUNet

### Training

First generate the data:

```sh
python src/prepare_nnunet_training.py data/raw/HFValid_Collection_v3/Subjects/ data/nnUNet/raw/ data/nnUNet/validation/ --dataset-id 101 --dataset-name FemurRefine --seed 644501148679811808
```

Set environment variables:

```sh
export nnUNet_raw="data/nnUNet/raw"
export nnUNet_preprocessed="data/nnUNet/preprocessed"
export nnUNet_results="data/nnUNet/results"
```

Run preprocessing:

```sh
nnUNetv2_plan_and_preprocess -d 101 --verify_dataset_integrity
```

Run training

```sh
nnUNetv2_train 101 3d_fullres 0
```

### Inference

```sh
nnUNetv2_predict -i data/nnUNet/validation/Dataset101_FemurRefine/imagesTr -o data/nnUNet/validation/Dataset101_FemurRefine/outputs -d 101 -c 3d_fullres -f 0 -chk checkpoint_best.pth
```

To use with TotalSegmentator:

```sh
python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat001/Pat001.nrrd data/segmentations/ct.nii.gz
TotalSegmentator -i data/segmentations/ct.nii.gz -o data/segmentations/ -p -rs femur_left -rs femur_right

python src/resample.py data/segmentations/femur_right.nii.gz data/segmentations/femur_right_resampled.nii.gz -z 2
python src/prepare_nnunet_predict.py data/segmentations/ct.nii.gz data/segmentations/femur_right_resampled.nii.gz data/nnUNet/validation/femur_001_0000.nii.gz data/nnUNet/validation/femur_001_0001.nii.gz
nnUNetv2_predict -i data/nnUNet/validation/ -o data/nnUNet/validation/outputs/ -d 101 -c 3d_fullres -f 0 -chk checkpoint_best.pth
```

# Comparison/Evaluation

To compare segmentations you can use the SlicerRT extension for 3D Slicer.  
Using the Segment Comparison model you can compute the Dice Similarity.

In code, you can do the following.

```sh
python src/compare.py data/raw/HFValid_Collection_v3/Subjects/Pat091/Pat091.stl data/nnUNet/validation/inputs/femur_091_0001.nii.gz data/nnUNet/validation/outputs/femur_091.nii.gz data/nnUNet/validation/labels/femur_091.nii.gz -v 0.3
```

Note that the stl->nifti conversion uses voxel spacing 0.5 by default. Use '-v <float>' to set different spacing.

# Scripts

Get average metrics for validation set:

```sh
export DATA_DIR=data/nnUNet/validation/Dataset101_FemurRefine/labelsTr/


ls $DATA_DIR \
  | awk -F '_' '{print $2}' \
  | xargs -I {} bash -c '
      python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat{}/Pat{}.stl data/preprocessed/{}_label_high_res.nii.gz -v 0.75
      python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat{}/Pat{}.stl data/preprocessed/{}_label_low_res.nii.gz -v 1.5
        
      python src/resample.py data/preprocessed/{}_label_low_res.nii.gz data/preprocessed/{}_upsampled_bspline.nii.gz -z 2 --use-bspline
      python src/smoothing.py data/preprocessed/{}_upsampled_bspline.nii.gz data/preprocessed/{}_upsampled_bspline.nii.gz -s 0
        
      python src/resample.py data/preprocessed/{}_label_low_res.nii.gz data/preprocessed/{}_upsampled.nii.gz -z 2
      python src/smoothing.py data/preprocessed/{}_upsampled.nii.gz data/preprocessed/{}_smoothed.nii.gz -s 3
  '

ls $DATA_DIR \
  | awk -F '_' '{print $2}' \
  | xargs -I {} bash -c '
    python src/compare.py data/raw/HFValid_Collection_v3/Subjects/Pat{}/Pat{}.stl data/preprocessed/{}_label_low_res.nii.gz data/preprocessed/{}_upsampled_bspline.nii.gz data/preprocessed/{}_smoothed.nii.gz data/preprocessed/{}_label_high_res.nii.gz -v 0.3
  ' \
  | awk -F ' |/..._' '{count[$NF]++; dice[$NF] += $4; hausdorff[$NF] += $7} END {for (key in dice) {print key; printf "Avg Dice: %.4f, Avg Hausdorff: %.4f\n",(dice[key]/(count[key])),(hausdorff[key]/(count[key]))}}'
```

