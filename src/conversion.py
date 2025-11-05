import argparse
import SimpleITK as sitk

from utils.image_processing import stl_to_nifti, read_image

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
        stl_to_nifti(args.file_in_path, args.file_out_path, args.voxel_size)
    elif args.file_in_path.endswith('.nrrd'):
        sitk.WriteImage(read_image(args.file_in_path), args.file_out_path)
    else:
        parser.print_help()

    print("Conversion complete!")
