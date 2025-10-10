import SimpleITK as sitk
import argparse
from scipy.ndimage import gaussian_filter


def refine(input_file, output_file, kernel_size):
    # Load the image using SimpleITK
    itk_image = sitk.ReadImage(input_file, sitk.sitkFloat32)
    itk_image_data = sitk.GetArrayFromImage(itk_image)

    # Apply gaussian smoothing
    blurred = gaussian_filter(itk_image_data, sigma=kernel_size)
    blurred[blurred <= 0.5] = 0
    blurred[blurred > 0.5] = 1

    # Convert back to SimpleITK image
    final_itk_image = sitk.GetImageFromArray(blurred)
    final_itk_image.CopyInformation(itk_image)

    # Save the final result
    sitk.WriteImage(final_itk_image, output_file)
    print(f"Refined segmentation saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Refine a 3D segmentation mask using a smoothing.')
    parser.add_argument('input_file', type=str, help='Path to the upsampled segmentation NIfTI file.')
    parser.add_argument('output_file', type=str, help='Path to save the refined NIfTI mask.')
    parser.add_argument('-s', '--kernel_size', type=float, default=3, help='Kernel size of the gaussian filter.')

    args = parser.parse_args()
    refine(args.input_file, args.output_file, args.kernel_size)
