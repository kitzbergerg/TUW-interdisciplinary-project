import argparse
import SimpleITK as sitk


def convert(file_in_path, file_out_path):
    itk_image = sitk.ReadImage(file_in_path, sitk.sitkFloat32)
    sitk.WriteImage(itk_image, file_out_path)
    print("Conversion complete!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Converts NRRD to NIfTI using SimpleITK.'
    )
    parser.add_argument('file_in_path', type=str, help='Path to the input .nrrd file.')
    parser.add_argument('file_out_path', type=str, help='Path for the output .nii.gz file.')
    args = parser.parse_args()

    convert(args.file_in_path, args.file_out_path)
