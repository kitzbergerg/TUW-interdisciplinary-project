import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os


def view_nii_slice(file_path, output_path, slice_index=None, axis=2):
    """
    Displays a 2D slice of a 3D NIfTI file.

    Args:
        file_path (str): The path to the .nii or .nii.gz file.
        slice_index (int, optional): The index of the slice to display.
                                     If None, the middle slice is shown.
        axis (int, optional): The axis from which to take the slice (0, 1, or 2).
                              Defaults to 2 (axial view).
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return

    try:
        # Load the NIfTI file. nibabel handles .nii and .nii.gz automatically.
        nifti_file = nib.load(file_path)

        # Get the image data as a NumPy array
        # get_fdata() returns the data in a floating-point format
        image_data = nifti_file.get_fdata()

        print(f"Image dimensions: {image_data.shape}")

        # Ensure the selected axis is valid
        if axis < 0 or axis >= len(image_data.shape):
            print(f"Error: Invalid axis '{axis}'. Must be 0, 1, or 2.")
            return

        # If no slice index is provided, choose the middle slice along the chosen axis
        if slice_index is None:
            slice_index = image_data.shape[axis] // 2

        # Ensure the selected slice index is valid
        if slice_index < 0 or slice_index >= image_data.shape[axis]:
            print(f"Error: Slice index {slice_index} is out of bounds for axis {axis} (size: {image_data.shape[axis]})")
            print(f"Please choose a slice between 0 and {image_data.shape[axis] - 1}.")
            return

        # Select the slice. We use np.take to select a slice along a dynamic axis.
        selected_slice = np.take(image_data, slice_index, axis=axis)

        # --- Display the Slice ---
        fig, ax = plt.subplots(1, 1, figsize=(8, 8))

        # Rotate the slice by 90 degrees to match the typical medical imaging orientation
        rotated_slice = np.rot90(selected_slice)

        ax.imshow(rotated_slice, cmap='gray')
        ax.axis('off')  # Hide the axes
        ax.set_title(f'File: {os.path.basename(file_path)}\nSlice {slice_index} from Axis {axis}')

        plt.savefig(output_path, bbox_inches='tight')
        plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    # Set up the argument parser to handle command-line inputs
    parser = argparse.ArgumentParser(description='View a slice of a NIfTI file.')
    parser.add_argument('file_path', type=str, help='Path to the .nii or .nii.gz file.')
    parser.add_argument('output_path', type=str, help='Path to save the output.')
    parser.add_argument('-s', '--slice', type=int, help='Slice number to display (optional, defaults to middle).')
    parser.add_argument('-a', '--axis', type=int, default=0, choices=[0, 1, 2],
                        help='Axis to slice along: 0=Sagittal, 1=Coronal, 2=Axial (default: 0).')

    args = parser.parse_args()

    view_nii_slice(args.file_path, args.output_path, args.slice, args.axis)
