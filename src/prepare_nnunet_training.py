import io
import json
import math
import random
import argparse
import SimpleITK as sitk
import os
import tempfile

from utils.image_processing import read_image


def voxel_to_str(voxel_size):
    """Converts a float voxel size (e.g., 1.5, 0.75) to a string (e.g., '15', '075')."""
    return str(voxel_size).replace('.', '')


def convert_data_tuple(
        sample_name: str,
        subject_name: str,
        images_dir: str,
        labels_dir: str,
        subjects_dir: str,
        temp_dir: str,
        voxel_size_original: float,
        upscale_factor: float,
):
    """Helper function to convert and process one subject."""
    subject_path = os.path.join(subjects_dir, subject_name)
    ct_nrrd_path = os.path.join(subject_path, f"{subject_name}.nrrd")
    stl_path = os.path.join(subject_path, f"{subject_name}.stl")

    nnunet_ct_out = os.path.join(images_dir, f"{sample_name}_0000.nii.gz")
    nnunet_low_res_out = os.path.join(images_dir, f"{sample_name}_0001.nii.gz")
    nnunet_label_out = os.path.join(labels_dir, f"{sample_name}.nii.gz")

    # --- 1. Load files ---
    ct_image = read_image(ct_nrrd_path)
    low_res_image = read_image(
        stl_path,
        voxel_size=voxel_size_original,
        temp_dir=temp_dir,
        data_type=sitk.sitkFloat32  # Use float so we can use linear for resampling
    )
    ground_truth_label = read_image(
        stl_path,
        voxel_size=voxel_size_original / upscale_factor,
        temp_dir=temp_dir,
        data_type=sitk.sitkUInt8,
        padding=math.ceil(1.5 * upscale_factor)
    )

    # --- 2. Resample to High-Res Grid ---
    resampled_ct = sitk.Resample(
        ct_image,
        interpolator=sitk.sitkLinear,
        referenceImage=ground_truth_label,
        defaultPixelValue=-1000  # Use air Hounsfield Unit for outside FOV
    )
    resampled_low_res = sitk.Resample(
        low_res_image,
        interpolator=sitk.sitkLinear,  # Use linear so model knows about unsure areas
        referenceImage=ground_truth_label,
    )

    # --- 3. Save final files to nnU-Net directory ---
    sitk.WriteImage(resampled_ct, nnunet_ct_out)
    sitk.WriteImage(resampled_low_res, nnunet_low_res_out)
    sitk.WriteImage(ground_truth_label, nnunet_label_out)


def prepare_and_convert_data(
        subjects_dir,
        train_output_path,
        valid_output_path,
        dataset_id,
        dataset_name,
        random_seed,
        voxel_size_original,
        upscale_factor,
        skip_val,
        data_percentage
):
    """
    Converts, resamples, and crops data from the original subjects
    directory directly into the nnU-Net task directory.
    """
    dataset_folder_name = f"Dataset{dataset_id:03d}_{dataset_name}"
    dataset_train_dir = os.path.join(train_output_path, dataset_folder_name)
    dataset_valid_dir = os.path.join(valid_output_path, dataset_folder_name)

    # Find all subject directories (e.g., "Pat001", "Pat002")
    subject_names = sorted(
        [d for d in os.listdir(subjects_dir)
         if os.path.isdir(os.path.join(subjects_dir, d)) and d.startswith('Pat')]
    )

    if not subject_names:
        print(f"Error: No subject directories found in {subjects_dir}")
        return

    print(f"Found {len(subject_names)} total subjects.")

    # --- 1. Create full train/valid split based on seed ---
    random.seed(random_seed)
    all_indices = list(range(len(subject_names)))
    random.shuffle(all_indices)  # Shuffle once for the split

    split_idx = int(0.9 * len(all_indices))
    train_indices_full = all_indices[:split_idx]
    valid_indices_full = all_indices[split_idx:]

    # --- 2. Calculate subset to process based on percentage ---
    num_train_to_process = int(len(train_indices_full) * data_percentage)
    random.seed(random_seed * num_train_to_process)
    train_indices_to_process = random.sample(train_indices_full, num_train_to_process)
    valid_indices_to_process = valid_indices_full
    print(f"Processing {len(train_indices_to_process)} training samples ({data_percentage * 100}%)")
    if not skip_val:
        print(f"Processing {len(valid_indices_to_process)} validation samples (100%)")

    with tempfile.TemporaryDirectory() as temp_dir:
        # --- 3. Process Training Data ---
        imagesTr_dir = os.path.join(dataset_train_dir, "imagesTr")
        labelsTr_dir = os.path.join(dataset_train_dir, "labelsTr")
        os.makedirs(imagesTr_dir, exist_ok=True)
        os.makedirs(labelsTr_dir, exist_ok=True)

        for i in train_indices_to_process:
            try:
                sample_name = f"femur_{i + 1:03d}_{voxel_to_str(voxel_size_original)}_{voxel_to_str(upscale_factor)}"
                subject_name = subject_names[i]
                print(f"--- Processing Train {subject_name} -> {sample_name} ---")
                convert_data_tuple(
                    sample_name, subject_name, imagesTr_dir, labelsTr_dir,
                    subjects_dir, temp_dir, voxel_size_original, upscale_factor
                )
            except Exception as e:
                print(f"  Error processing {subject_name}: {e}. Skipping.")
                continue

        # --- 4. Process Validation Data ---
        if not skip_val:
            imagesTr_dir = os.path.join(dataset_valid_dir, "imagesTr")
            labelsTr_dir = os.path.join(dataset_valid_dir, "labelsTr")
            os.makedirs(imagesTr_dir, exist_ok=True)
            os.makedirs(labelsTr_dir, exist_ok=True)
            for i in valid_indices_full:
                try:
                    sample_name = f"femur_{i + 1:03d}_{voxel_to_str(voxel_size_original)}_{voxel_to_str(upscale_factor)}"
                    subject_name = subject_names[i]
                    print(f"--- Processing Valid {subject_name} -> {sample_name} ---")
                    convert_data_tuple(
                        sample_name, subject_name, imagesTr_dir, labelsTr_dir,
                        subjects_dir, temp_dir, voxel_size_original, upscale_factor
                    )
                except Exception as e:
                    print(f"  Error processing {subject_name}: {e}. Skipping.")
                    continue

        # --- 5. Create or Update dataset.json file ---
        json_path = os.path.join(dataset_train_dir, "dataset.json")

        all_training_labels = os.listdir(os.path.join(dataset_train_dir, "labelsTr"))
        total_training_samples = len([f for f in all_training_labels if f.endswith(".nii.gz")])

        with io.open(json_path, "w") as f:
            json.dump({
                "dataset_name": dataset_name,
                "channel_names": {
                    "0": "CT",
                    "1": "low_res_segmentation"
                },
                "labels": {
                    "background": 0,
                    "femur": 1
                },
                "numTraining": total_training_samples,  # Update with the total count
                "file_ending": ".nii.gz",
                "overwrite_image_reader_writer": "SimpleITKIO"
            }, f, indent=4)

        print(
            f"Data preparation complete with {total_training_samples} training samples and {len(valid_indices_full)} validation samples.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert and prepare training data for nnU-Net.'
    )
    parser.add_argument('subjects_dir', type=str,
                        help='Path to original subjects data (e.g., "data/raw/HFValid_Collection_v3/Subjects/")')
    parser.add_argument('train_output_path', type=str,
                        help='Path to nnU-Net raw data directory (e.g., "data/nnUNet/raw/")')
    parser.add_argument('valid_output_path', type=str,
                        help='Path to nnU-Net test/validation directory (e.g., "data/nnUNet/test/")')
    parser.add_argument('--dataset-id', type=int, required=True,
                        help='nnU-Net Dataset ID (e.g., 103)')
    parser.add_argument('--dataset-name', type=str, default="FemurRefine",
                        help='nnU-Net Dataset Name (e.g., "FemurRefine")')
    parser.add_argument('--seed', type=int, default=123,
                        help='Random seed for train/valid split')
    parser.add_argument('--voxel-size-original', type=float, default=1.5,
                        help='Voxel size for the low-res mask (Input 1)')
    parser.add_argument('--upscale-factor', type=float, default=2,
                        help='Voxel size for the high-res mask (Ground Truth)')
    parser.add_argument('--skip-val', action=argparse.BooleanOptionalAction, default=False,
                        help='Pass to disable validation set generation')
    parser.add_argument('--data-percentage', type=float, default=1.0,
                        help='Percentage of data to process (e.g., 0.2 for 20%)')

    args = parser.parse_args()

    if not 0.0 < args.data_percentage <= 1.0:
        raise ValueError("Data percentage must be between 0.0 and 1.0")

    prepare_and_convert_data(
        args.subjects_dir,
        args.train_output_path,
        args.valid_output_path,
        args.dataset_id,
        args.dataset_name,
        args.seed,
        args.voxel_size_original,
        args.upscale_factor,
        args.skip_val,
        args.data_percentage,
    )
