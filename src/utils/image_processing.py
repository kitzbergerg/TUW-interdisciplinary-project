import os
import tempfile
from contextlib import nullcontext

import SimpleITK as sitk
import numpy as np
import trimesh
import nibabel as nib


def _read_stl(file_in_path, voxel_size, padding=0):
    mesh = trimesh.load_mesh(file_in_path)
    voxelized_mesh = mesh.voxelized(pitch=voxel_size)
    binary_matrix = voxelized_mesh.fill().matrix.astype(np.int8)

    affine_matrix = voxelized_mesh.transform.copy()

    # --- Apply Padding if requested ---
    if padding > 0:
        # 1. Pad the numpy array (add empty voxels on all sides)
        binary_matrix = np.pad(binary_matrix, pad_width=padding, mode='constant', constant_values=0)

        # 2. Adjust the origin (translation) in the affine matrix
        shift = -1 * padding * voxel_size

        # Apply shift to X, Y, Z translation components
        affine_matrix[0, 3] += shift
        affine_matrix[1, 3] += shift
        affine_matrix[2, 3] += shift

    # Convert LPS to RAS
    affine_matrix[0, 0] *= -1
    affine_matrix[1, 1] *= -1
    affine_matrix[0, 3] *= -1
    affine_matrix[1, 3] *= -1

    return nib.Nifti1Image(binary_matrix, affine_matrix)


def stl_to_nifti(file_in_path, file_out_path, voxel_size, padding):
    nib.save(_read_stl(file_in_path, voxel_size, padding=padding), file_out_path)


def read_image(file_path, voxel_size=1.5, temp_dir=None, data_type=sitk.sitkFloat32, padding=0):
    if file_path.endswith('.stl'):
        with tempfile.TemporaryDirectory() if temp_dir is None else nullcontext(temp_dir) as temp_dir:
            tmp_path = os.path.join(temp_dir, "tmp.nii.gz")
            stl_to_nifti(file_path, tmp_path, voxel_size=voxel_size, padding=padding)
            return sitk.ReadImage(tmp_path, data_type)
    elif file_path.endswith(('.nii', '.nii.gz', '.nrrd')):
        return sitk.ReadImage(file_path, data_type)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
