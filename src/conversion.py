import argparse
import SimpleITK as sitk
import nibabel as nib

from utils.preprocessing_utils import convert_stl, convert_nrrd

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Converts NRRD or STL to NIfTI.'
    )
    parser.add_argument('file_in_path', type=str, help='Path to the input .nrrd or .stl file.')
    parser.add_argument('file_out_path', type=str, help='Path for the output .nii.gz file.')
    parser.add_argument('-v', '--voxel_size', type=float, default=1.0,
                        help='Voxel size in mm when converting STL to NII.')
    args = parser.parse_args()

    if args.file_in_path.endswith('.stl'):
        nifti_image = convert_stl(args.file_in_path, args.voxel_size)
        nib.save(nifti_image, args.file_out_path)
    elif args.file_in_path.endswith('.nrrd'):
        itk_image = convert_nrrd(args.file_in_path)
        sitk.WriteImage(itk_image, args.file_out_path)
    else:
        parser.print_help()
        exit(1)

    print("Conversion complete!")
