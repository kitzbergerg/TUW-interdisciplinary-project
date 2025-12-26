import argparse
import SimpleITK as sitk

from utils.image_processing import read_image


def resample_image(itk_image, upscale_factor, interpolator=sitk.sitkLinear):
    resampler = sitk.ResampleImageFilter()

    new_size = [int(round(s * upscale_factor)) for s in itk_image.GetSize()]
    resampler.SetSize(new_size)

    new_spacing = [s / upscale_factor for s in itk_image.GetSpacing()]
    resampler.SetOutputSpacing(new_spacing)

    resampler.SetInterpolator(interpolator)
    resampler.SetDefaultPixelValue(0)
    resampler.SetOutputOrigin(itk_image.GetOrigin())
    resampler.SetOutputDirection(itk_image.GetDirection())

    # we want probability maps, not intensities
    resampler.SetOutputPixelType(sitk.sitkFloat32)

    return resampler.Execute(itk_image)


def resample(input_file, output_file, upscale_factor, interpolator):
    itk_image = read_image(input_file)
    resampled_itk_image = resample_image(itk_image, upscale_factor, interpolator)
    sitk.WriteImage(resampled_itk_image, output_file)
    print(f"Resampled segmentation saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Resample a nifti image.')
    parser.add_argument('input_file', type=str, help='Path to the segmentation NIfTI file.')
    parser.add_argument('output_file', type=str, help='Path to save the resampled NIfTI file.')
    parser.add_argument('-z', '--upscale_factor', type=float, default=2.0,
                        help='Resampling factor (<1 for downsampling and >1 for upsampling).')
    parser.add_argument('--use-bspline', action=argparse.BooleanOptionalAction, default=True,
                        help='Switch to bspline interpolation instead of linear.')

    args = parser.parse_args()

    interpolator = sitk.sitkBSpline if args.use_bspline else sitk.sitkLinear
    resample(args.input_file, args.output_file, args.upscale_factor, interpolator)
