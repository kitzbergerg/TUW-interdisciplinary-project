import argparse
import SimpleITK as sitk
import os
import tempfile
import nibabel as nib

from utils.preprocessing_utils import crop_to_label_bbox, convert_nrrd, convert_stl


def prepare_and_convert_data(subjects_dir, nnunet_task_dir):
    """
    Converts, resamples, and crops data from the original subjects
    directory directly into the nnU-Net task directory.
    """
    imagesTr_dir = os.path.join(nnunet_task_dir, "imagesTr")
    labelsTr_dir = os.path.join(nnunet_task_dir, "labelsTr")
    os.makedirs(imagesTr_dir, exist_ok=True)
    os.makedirs(labelsTr_dir, exist_ok=True)

    # Find all subject directories (e.g., "Pat001", "Pat002")
    subject_names = sorted(
        [d for d in os.listdir(subjects_dir)
         if os.path.isdir(os.path.join(subjects_dir, d)) and d.startswith('Pat')]
    )

    if not subject_names:
        print(f"Error: No subject directories found in {subjects_dir}")
        return

    print(f"Found {len(subject_names)} subjects. Starting preparation...")

    # Use one temporary directory for all intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, subject_name in enumerate(subject_names):
            sample_name = f"femur_{i + 1:03d}"  # e.g., femur_001
            print(f"--- Processing {subject_name} -> {sample_name} ---")

            subject_path = os.path.join(subjects_dir, subject_name)
            ct_nrrd_path = os.path.join(subject_path, f"{subject_name}.nrrd")
            stl_path = os.path.join(subject_path, f"{subject_name}.stl")

            nnunet_ct_out = os.path.join(imagesTr_dir, f"{sample_name}_0000.nii.gz")
            nnunet_low_res_out = os.path.join(imagesTr_dir, f"{sample_name}_0001.nii.gz")
            nnunet_label_out = os.path.join(labelsTr_dir, f"{sample_name}.nii.gz")

            # Define paths for intermediate NIfTI files
            temp_ct_nii = os.path.join(temp_dir, "ct.nii.gz")
            temp_low_res_nii = os.path.join(temp_dir, "label_low_res.nii.gz")
            temp_high_res_nii = os.path.join(temp_dir, "label_high_res.nii.gz")

            try:
                # --- 1. Convert and save to temp files ---
                # Convert NRRD -> NIfTI
                itk_image = convert_nrrd(ct_nrrd_path)
                sitk.WriteImage(itk_image, temp_ct_nii)

                # Convert STL -> NIfTI (Low Res)
                nifti_low_res = convert_stl(stl_path, voxel_size=1.5)
                nib.save(nifti_low_res, temp_low_res_nii)

                # Convert STL -> NIfTI (High Res)
                nifti_high_res = convert_stl(stl_path, voxel_size=0.75)
                nib.save(nifti_high_res, temp_high_res_nii)

                # --- 2. Load temp files with SimpleITK ---
                # This bridges the gap between nibabel and SimpleITK
                ct_image = sitk.ReadImage(temp_ct_nii)
                low_res_image = sitk.ReadImage(temp_low_res_nii)
                ground_truth_label = sitk.ReadImage(temp_high_res_nii)

                # --- 3. Resample to High-Res Grid ---
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

                # --- 4. Crop all images to the label bounding box ---
                cropped_ct = crop_to_label_bbox(resampled_ct, ground_truth_label)
                cropped_low_res = crop_to_label_bbox(resampled_low_res, ground_truth_label)
                cropped_label = crop_to_label_bbox(ground_truth_label, ground_truth_label)

                # --- 5. Save final files to nnU-Net directory ---
                sitk.WriteImage(cropped_ct, nnunet_ct_out)
                sitk.WriteImage(cropped_low_res, nnunet_low_res_out)
                sitk.WriteImage(cropped_label, nnunet_label_out)

            except Exception as e:
                print(f"  Error processing {subject_name}: {e}")
                print("  Skipping this subject.")
                continue

    print("Data preparation complete.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert and prepare training data for nnU-Net.'
    )
    parser.add_argument('subjects_dir', type=str,
                        help='Path to original subjects data (e.g., "data/raw/HFValid_Collection_v3/Subjects/")')
    parser.add_argument('nnunet_task_dir', type=str,
                        help='Path to nnU-Net dataset dir (e.g., "data/nnUNet/raw/Dataset103_FemurRefine/")')
    args = parser.parse_args()

    prepare_and_convert_data(args.subjects_dir, args.nnunet_task_dir)
