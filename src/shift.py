import argparse
import SimpleITK as sitk
import numpy as np


def shift_image_fractional(input_file, output_file, shift_voxels, interpolator='linear'):
    """
    Shifts a NIfTI image by a fractional number of voxels using a transform.

    Args:
        input_file (str): Path to the input NIfTI file.
        output_file (str): Path to save the shifted NIfTI file.
        shift_voxels (list of float): A list of 3 floats representing the shift
                                      in voxel units for each axis [x, y, z].
        interpolator (str): Interpolator to use. 'linear' for intensity images,
                            'nearest' for label/segmentation maps.
    """
    # Load the image
    itk_image = sitk.ReadImage(input_file)
    spacing = itk_image.GetSpacing()

    # Convert the shift from voxel units to physical units (mm)
    # The transform operates in the physical space
    shift_physical = [float(sv) * float(sp) for sv, sp in zip(shift_voxels, spacing)]

    # SimpleITK uses the opposite convention for translation, so we negate the shift
    shift_physical = [-s for s in shift_physical]

    print(f"Original spacing: {np.array(spacing)}")
    print(f"Shift in voxels: {np.array(shift_voxels)}")
    print(f"Calculated shift in physical units (mm): {np.array(shift_physical)}")

    # Create a translation transform
    translation = sitk.TranslationTransform(3, shift_physical)

    # Choose the interpolator
    if interpolator == 'linear':
        interp_method = sitk.sitkLinear
    elif interpolator == 'nearest':
        interp_method = sitk.sitkNearestNeighbor
    else:
        raise ValueError("Interpolator must be 'linear' or 'nearest'")

    # Resample the image using the transform
    # The key is to use the original image as the reference for the output grid
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(itk_image)  # Use original image's grid
    resampler.SetTransform(translation)
    resampler.SetInterpolator(interp_method)
    resampler.SetDefaultPixelValue(0)  # Value for pixels outside the original image

    shifted_image = resampler.Execute(itk_image)

    # Save the result
    sitk.WriteImage(shifted_image, output_file)
    print(f"Shifted image saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Shift a NIfTI image by a fractional voxel amount.'
    )
    parser.add_argument('input_file', type=str, help='Path to the input NIfTI file.')
    parser.add_argument('output_file', type=str, help='Path to save the shifted NIfTI file.')
    parser.add_argument('--shift', type=float, nargs=3, required=True,
                        metavar=('SHIFT_X', 'SHIFT_Y', 'SHIFT_Z'),
                        help='Shift in fractional voxel units for each axis (e.g., 0.5 0 0).')
    parser.add_argument('--interp', type=str, default='linear', choices=['linear', 'nearest'],
                        help="Interpolator: 'linear' for intensity, 'nearest' for labels.")

    args = parser.parse_args()
    shift_image_fractional(args.input_file, args.output_file, args.shift, args.interp)
