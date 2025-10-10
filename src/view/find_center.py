import nibabel as nib
import numpy as np
import argparse
import os


def find_nii_center(file_path):
    """
    Finds the bounding box of non-zero voxels in a NIfTI file and prints the center of the box.

    Args:
        file_path (str): The path to the .nii or .nii.gz file.
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return

    try:
        # Load the NIfTI file and get its data
        nifti_file = nib.load(file_path)
        image_data = nifti_file.get_fdata()

        # Find the indices of all non-zero voxels
        # np.nonzero() returns a tuple of arrays, one for each dimension
        non_zero_indices = np.nonzero(image_data)

        # Check if there is any non-zero data
        if len(non_zero_indices[0]) == 0:
            print("Error: This file contains no non-zero voxels.")
            return

        # Determine the min and max indices for each dimension to get the bounding box
        min_indices = [np.min(idx) for idx in non_zero_indices]
        max_indices = [np.max(idx) for idx in non_zero_indices]

        x_min, y_min, z_min = min_indices
        x_max, y_max, z_max = max_indices

        print(f"Found non-zero data within bounding box:")
        print(f"  x-range: [{x_min}, {x_max}]")
        print(f"  y-range: [{y_min}, {y_max}]")
        print(f"  z-range: [{z_min}, {z_max}]\n")

        # Calculate the center of the bounding box
        center_coords = (
            (x_min + x_max) // 2,
            (y_min + y_max) // 2,
            (z_min + z_max) // 2
        )

        print(f"Center coordinate: {center_coords}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    # Set up the argument parser to handle the file path from the command line
    parser = argparse.ArgumentParser(
        description='Find the center of non-zero data in a NIfTI file.'
    )
    parser.add_argument('file_path', type=str, help='Path to the .nii or .nii.gz file.')
    args = parser.parse_args()

    find_nii_center(args.file_path)
