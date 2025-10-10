import argparse
import SimpleITK as sitk
import numpy as np
import trimesh
import nibabel as nib


def convert_nrrd(file_in_path, file_out_path):
    itk_image = sitk.ReadImage(file_in_path, sitk.sitkFloat32)
    sitk.WriteImage(itk_image, file_out_path)


def convert_stl(file_in_path, file_out_path, voxel_size=1.0):
    mesh = trimesh.load_mesh(file_in_path)
    voxelized_mesh = mesh.voxelized(pitch=voxel_size)
    binary_matrix = voxelized_mesh.fill().matrix.astype(np.int8)

    affine_matrix = voxelized_mesh.transform.copy()
    # Convert LPS to RAS
    affine_matrix[0, 0] *= -1
    affine_matrix[1, 1] *= -1
    affine_matrix[0, 3] *= -1
    affine_matrix[1, 3] *= -1
    nifti_image = nib.Nifti1Image(binary_matrix, affine_matrix)

    nib.save(nifti_image, file_out_path)


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
        convert_stl(args.file_in_path, args.file_out_path, args.voxel_size)
    elif args.file_in_path.endswith('.nrrd'):
        convert_nrrd(args.file_in_path, args.file_out_path)
    else:
        parser.print_help()
        exit(1)

    print("Conversion complete!")
