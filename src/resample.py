import argparse
import SimpleITK as sitk


def resample_data(itk_image, zoom_factor):
    # Get original properties and calculate new ones
    original_spacing = itk_image.GetSpacing()
    original_size = itk_image.GetSize()

    # Calculate the new spacing and size
    new_spacing = [s / zoom_factor for s in original_spacing]
    new_size = [int(round(s * zoom_factor)) for s in original_size]

    # Resample using SimpleITK
    resampler = sitk.ResampleImageFilter()
    resampler.SetOutputSpacing(new_spacing)
    resampler.SetSize(new_size)
    resampler.SetOutputOrigin(itk_image.GetOrigin())

    resampler.SetInterpolator(sitk.sitkLinear)  # nearest neighbor doesn't work since it shifts pixels
    resampler.SetDefaultPixelValue(0)
    resampler.SetOutputDirection(itk_image.GetDirection())

    # Execute the resampling
    resampled_itk_image = resampler.Execute(itk_image)

    return resampled_itk_image


def resample(input_file, output_file, zoom_factor):
    # Load the image using SimpleITK
    itk_image = sitk.ReadImage(input_file, sitk.sitkFloat32)

    # Resample image
    resampled_itk_image = resample_data(itk_image, zoom_factor)
    resampled_data = sitk.GetArrayFromImage(resampled_itk_image)
    resampled_data[resampled_data <= 0.5] = 0
    resampled_data[resampled_data > 0.5] = 1

    # Convert back to SimpleITK image
    final_itk_image = sitk.GetImageFromArray(resampled_data)
    final_itk_image.CopyInformation(resampled_itk_image)

    # Save the final result
    sitk.WriteImage(final_itk_image, output_file)
    print(f"Resampled segmentation saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Resample a nifti image.')
    parser.add_argument('input_file', type=str, help='Path to the segmentation NIfTI file.')
    parser.add_argument('output_file', type=str, help='Path to save the resampled NIfTI file.')
    parser.add_argument('-z', '--zoom_factor', type=float, default=2.0,
                        help='Resampling zoom factor (<1 for downsampling and >1 for upsampling).')

    args = parser.parse_args()
    resample(args.input_file, args.output_file, args.zoom_factor)
