import SimpleITK as sitk
import os
from glob import glob

# --- !! UPDATE THESE PATHS !! ---
# Path to your original 100 samples
original_data_dir = "out/"
# Path to your nnU-Net task directory
nnunet_task_dir = "nnUNet_raw/Dataset101_FemurRefine/"
# --------------------------------

imagesTr_dir = os.path.join(nnunet_task_dir, "imagesTr")
labelsTr_dir = os.path.join(nnunet_task_dir, "labelsTr")

print(f"Starting data preparation for nnU-Net...")

# Loop through your samples
for i in range(1, 102):
    sample_name = f"femur_{i:03d}"  # e.g., "femur_001"
    print(f"Processing {sample_name}...")

    # --- Define file paths ---
    # 1. The Reference Image (High-Res CT)
    ct_path = os.path.join(original_data_dir, f"Pat{i:03d}", "ct.nii.gz")
    # 2. The Moving Image (Low-Res Label)
    low_res_label_path = os.path.join(original_data_dir, f"Pat{i:03d}", "label_low_res.nii.gz")
    # 3. The Ground Truth (High-Res Label)
    high_res_label_path = os.path.join(original_data_dir, f"Pat{i:03d}", "label_high_res.nii.gz")

    # --- Define nnU-Net output paths ---
    nnunet_ct_out = os.path.join(imagesTr_dir, f"{sample_name}_0000.nii.gz")
    nnunet_resampled_out = os.path.join(imagesTr_dir, f"{sample_name}_0001.nii.gz")
    nnunet_label_out = os.path.join(labelsTr_dir, f"{sample_name}.nii.gz")

    # --- Load images ---
    try:
        reference_image = sitk.ReadImage(ct_path)
        moving_image = sitk.ReadImage(low_res_label_path)
        ground_truth_label = sitk.ReadImage(high_res_label_path)
    except Exception as e:
        print(f"  Error loading files for {sample_name}: {e}")
        continue

    # --- 1. Resample the low-res label to match the CT grid ---
    # We use Linear interpolation to get the "blurry" upsampled mask
    resampled_low_res_mask = sitk.Resample(
        moving_image,
        referenceImage=reference_image,
    )

    # --- 2. Check and resample the high-res label (CRITICAL STEP) ---
    # Your high-res label MUST also match the CT grid.
    # We use Nearest Neighbor interpolation because it's a label.
    if ground_truth_label.GetSize() != reference_image.GetSize():
        print(f"  WARNING: Resampling ground truth label for {sample_name} to match CT.")
        ground_truth_label = sitk.Resample(
            ground_truth_label,
        referenceImage=reference_image,
        )

    # --- Save the files in the nnU-Net format ---
    sitk.WriteImage(reference_image, nnunet_ct_out)
    sitk.WriteImage(resampled_low_res_mask, nnunet_resampled_out)
    sitk.WriteImage(ground_truth_label, nnunet_label_out)

print("Data preparation complete.")
