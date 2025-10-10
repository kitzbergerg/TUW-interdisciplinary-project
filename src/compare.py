import argparse

import nibabel as nib
import numpy as np
from nilearn.image import resample_to_img

from conversion import convert_stl


def dice_similarity_coefficient(mask1, mask2):
    mask1 = np.asarray(mask1).astype(bool)
    mask2 = np.asarray(mask2).astype(bool)
    if mask1.shape != mask2.shape:
        raise ValueError("Masks must have the same shape.")
    intersection = np.logical_and(mask1, mask2)
    sum_of_masks = mask1.sum() + mask2.sum()
    if sum_of_masks == 0:
        return 1.0
    return 2. * intersection.sum() / sum_of_masks


def compare(ground_truth, comparison, voxel_size):
    if ground_truth.endswith('.stl'):
        ground_truth_nifti = convert_stl(ground_truth, voxel_size)
    elif ground_truth.endswith('.nii.gz'):
        ground_truth_nifti = nib.load(ground_truth)
    else:
        exit(1)

    for file in comparison:
        if file.endswith('.stl'):
            nifti_img_2 = convert_stl(file, voxel_size)
        elif file.endswith('.nii.gz'):
            nifti_img_2 = nib.load(file)
        else:
            print(f"Invalid file: {file}")
            continue

        # Resample the other files to the first image
        resampled_nifti_2 = resample_to_img(
            source_img=nifti_img_2,
            target_img=ground_truth_nifti,
            interpolation='nearest',  # Use 'nearest' for masks to avoid creating new values
            copy_header=True,
            force_resample=True
        )
        # -----------------------------------------------------------

        # Get the image data as numpy arrays
        nifti_data_1 = ground_truth_nifti.get_fdata()
        resampled_data_2 = resampled_nifti_2.get_fdata()

        # Convert to binary masks
        nifti_mask_1 = nifti_data_1.astype(bool)
        nifti_mask_2 = resampled_data_2.astype(bool)

        # Calculate dice scores
        dsc = dice_similarity_coefficient(nifti_mask_1, nifti_mask_2)
        print(f"Dice Similarity Coefficient: {dsc:.4f} for {file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare NIfTI files.')
    parser.add_argument('ground_truth', type=str, help='Path to the first file.')
    parser.add_argument('comparison', nargs='+', default=[], help='Paths to other files to compare against.')
    parser.add_argument('-v', '--voxel_size', type=float, default=0.5, help='Voxel Size for STL to NIfTI conversion.')
    args = parser.parse_args()

    compare(args.ground_truth, args.comparison, args.voxel_size)
