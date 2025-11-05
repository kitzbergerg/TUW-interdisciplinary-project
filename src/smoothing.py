import SimpleITK as sitk
import argparse

from utils.image_processing import read_image


def refine(input_file, output_file, kernel_size):
    itk_image = read_image(input_file)
    if kernel_size > 0:
        itk_image = sitk.SmoothingRecursiveGaussian(itk_image, kernel_size)
    itk_image = sitk.BinaryThreshold(itk_image, lowerThreshold=0.5)
    sitk.WriteImage(itk_image, output_file)
    print(f"Refined segmentation saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Refine a 3D segmentation mask using a smoothing.')
    parser.add_argument('input_file', type=str, help='Path to the upsampled segmentation NIfTI file.')
    parser.add_argument('output_file', type=str, help='Path to save the refined NIfTI mask.')
    parser.add_argument('-s', '--kernel_size', type=float, default=3, help='Kernel size of the gaussian filter.')

    args = parser.parse_args()
    refine(args.input_file, args.output_file, args.kernel_size)
