Get average metrics for validation set:

```sh
export DATA_DIR=data/nnUNet/validation/Dataset103_FemurRefineV2_4x/labelsTr/


ls $DATA_DIR \
    | awk -F '_' '{print $2}' \
    | xargs -I {} bash -c '
        python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat{}/Pat{}.stl data/preprocessed/{}_label_0375.nii.gz -v 0.375
        python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat{}/Pat{}.stl data/preprocessed/{}_label_075.nii.gz -v 0.75
        python src/conversion.py data/raw/HFValid_Collection_v3/Subjects/Pat{}/Pat{}.stl data/preprocessed/{}_label_15.nii.gz -v 1.5
        
        
        python src/resample.py data/preprocessed/{}_label_15.nii.gz data/preprocessed/{}_upsampled_2_bspline.nii.gz -z 2 --use-bspline
        python src/smoothing.py data/preprocessed/{}_upsampled_2_bspline.nii.gz data/preprocessed/{}_bspline_2.nii.gz -s 0
        
        python src/resample.py data/preprocessed/{}_label_15.nii.gz data/preprocessed/{}_upsampled_4_bspline.nii.gz -z 4 --use-bspline
        python src/smoothing.py data/preprocessed/{}_upsampled_4_bspline.nii.gz data/preprocessed/{}_bspline_4.nii.gz -s 0
        
        python src/resample.py data/preprocessed/{}_bspline_2.nii.gz data/preprocessed/{}_upsampled_2x2_bspline.nii.gz -z 2 --use-bspline
        python src/smoothing.py data/preprocessed/{}_upsampled_2x2_bspline.nii.gz data/preprocessed/{}_bspline_2x2.nii.gz -s 0
        
        python src/resample.py data/preprocessed/{}_label_15.nii.gz data/preprocessed/{}_upsampled_2.nii.gz -z 2
        python src/smoothing.py data/preprocessed/{}_upsampled_2.nii.gz data/preprocessed/{}_smoothed_2.nii.gz -s 3
        
        python src/resample.py data/preprocessed/{}_label_15.nii.gz data/preprocessed/{}_upsampled_4.nii.gz -z 4
        python src/smoothing.py data/preprocessed/{}_upsampled_4.nii.gz data/preprocessed/{}_smoothed_4.nii.gz -s 6
        
        python src/resample.py data/preprocessed/{}_smoothed_2.nii.gz data/preprocessed/{}_upsampled_2x2.nii.gz -z 2
        python src/smoothing.py data/preprocessed/{}_upsampled_2x2.nii.gz data/preprocessed/{}_smoothed_2x2.nii.gz -s 3
    '

ls $DATA_DIR \
    | awk -F '_' '{print $2}' \
    | xargs -I {} -P 4 bash -c '
        python src/compare.py data/raw/HFValid_Collection_v3/Subjects/Pat{}/Pat{}.stl \
            data/preprocessed/{}_label_0375.nii.gz \
            data/preprocessed/{}_label_075.nii.gz \
            data/preprocessed/{}_label_15.nii.gz \
            data/preprocessed/{}_bspline_2.nii.gz \
            data/preprocessed/{}_bspline_4.nii.gz \
            data/preprocessed/{}_bspline_2x2.nii.gz \
            data/preprocessed/{}_smoothed_2.nii.gz \
            data/preprocessed/{}_smoothed_4.nii.gz \
            data/preprocessed/{}_smoothed_2x2.nii.gz \
            -v 0.3
        ' \
    | awk -F ' |/..._' '{count[$NF]++; dice[$NF] += $4; hausdorff[$NF] += $7} END {for (key in dice) {print key; printf "Avg Dice: %.4f, Avg Hausdorff: %.4f\n",(dice[key]/(count[key])),(hausdorff[key]/(count[key]))}}'



nnUNetv2_predict -i data/nnUNet/validation/Dataset103_FemurRefineV2_4x/imagesTr/ -o data/nnUNet/validation/Dataset103_FemurRefineV2_4x/outputs/ -d 103 -c 3d_fullres -f 0 -chk checkpoint_best.pth

ls $DATA_DIR \
    | awk -F '_' '{print $2}' \
    | xargs -I {} -P 4 bash -c '
        python src/compare.py data/raw/HFValid_Collection_v3/Subjects/Pat{}/Pat{}.stl \
            data/nnUNet/validation/Dataset103_FemurRefineV2_4x/outputs/femur_{}_15_40.nii.gz \
            -v 0.3
        ' \
    | awk -F ' ' '{count++; dice += $4; hausdorff += $7} END {printf "Avg Dice: %.4f, Avg Hausdorff: %.4f\n",(dice/count),(hausdorff/count)}'
```

Get all non-empty segmentations in directory:

```sh
export PROJECT_DIR=/home/jovyan/InterdisciplinaryProject/
export DATA_DIR=./

ls $DATA_DIR | grep .nii.gz | xargs -I {} python -c "
import SimpleITK as sitk
import numpy as np

img = sitk.ReadImage('$DATA_DIR{}')
input_array = sitk.GetArrayFromImage(img)
if not np.all(input_array == 0):
  print('$DATA_DIR{}')
" | xargs -I {} bash -c "
python $PROJECT_DIR/src/resample.py {} ../resampled/{} -z 4
python $PROJECT_DIR/src/prepare_nnunet_predict.py ../ct_003.nii.gz ../resampled/{} ../in/{}_0000.nii.gz ../in/{}_0001.nii.gz
"

cd $PROJECT_DIR
nnUNetv2_predict -i data/segmentations/in/ -o data/segmentations/out/ -d 103 -c 3d_fullres -f 0 -chk checkpoint_best.pth
```
