import SimpleITK as sitk
import os
import argparse
from preprocessing_utils import crop_to_label_bbox  # Import the new util function


def prepare_training_data(original_data_dir, nnunet_task_dir):
    """
    Prepares training data for nnU-Net by resampling to the high-res
    label's grid and then cropping to the label's bounding box.
    """
    imagesTr_dir = os.path.join(nnunet_task_dir, "imagesTr")
    labelsTr_dir = os.path.join(nnunet_task_dir, "labelsTr")
    os.makedirs(imagesTr_dir, exist_ok=True)
    os.makedirs(labelsTr_dir, exist_ok=True)

    print(f"Starting data preparation for nnU-Net...")

    # Assumes 101 samples, from Pat001 to Pat101
    for i in range(1, 102):
        sample_name = f"femur_{i:03d}"
        print(f"Processing {sample_name}...")

        ct_path = os.path.join(original_data_dir, f"Pat{i:03d}", "ct.nii.gz")
        low_res_label_path = os.path.join(original_data_dir, f"Pat{i:03d}", "label_low_res.nii.gz")
        high_res_label_path = os.path.join(original_data_dir, f"Pat{i:03d}", "label_high_res.nii.gz")

        nnunet_ct_out = os.path.join(imagesTr_dir, f"{sample_name}_0000.nii.gz")
        nnunet_low_res_out = os.path.join(imagesTr_dir, f"{sample_name}_0001.nii.gz")
        nnunet_label_out = os.path.join(labelsTr_dir, f"{sample_name}.nii.gz")

        try:
            ct_image = sitk.ReadImage(ct_path)
            low_res_image = sitk.ReadImage(low_res_label_path)
            ground_truth_label = sitk.ReadImage(high_res_label_path)
        except Exception as e:
            print(f"  Error loading files for {sample_name}: {e}")
            continue

        # --- 1. Resample to High-Res Grid ---
        resampled_ct = sitk.Resample(
            ct_image,
            interpolator=sitk.sitkLinear,
            referenceImage=ground_truth_label,
        )
        resampled_low_res = sitk.Resample(
            low_res_image,
            interpolator=sitk.sitkNearestNeighbor,
            referenceImage=ground_truth_label,
        )

        # --- 2. Crop all resampled images to the label bounding box ---
        cropped_ct = crop_to_label_bbox(resampled_ct, ground_truth_label)
        cropped_low_res = crop_to_label_bbox(resampled_low_res, ground_truth_label)
        cropped_label = crop_to_label_bbox(ground_truth_label, ground_truth_label)

        # --- 3. Save files ---
        sitk.WriteImage(cropped_ct, nnunet_ct_out)
        sitk.WriteImage(cropped_low_res, nnunet_low_res_out)
        sitk.WriteImage(cropped_label, nnunet_label_out)

    print("Data preparation complete.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare nnU-Net training data.')
    parser.add_argument('original_data_dir', type=str, help='Path to original data (e.g., "data/preprocessed/")')
    parser.add_argument('nnunet_task_dir', type=str,
                        help='Path to nnU-Net task dir (e.g., "data/nnUNet/raw/Dataset102_FemurRefineV2/")')
    args = parser.parse_args()

    prepare_training_data(args.original_data_dir, args.nnunet_task_dir)
