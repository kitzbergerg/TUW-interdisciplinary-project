import os
import tempfile
from contextlib import nullcontext

import SimpleITK as sitk
import numpy as np
import trimesh
import nibabel as nib


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


def crop_to_label_bbox(image_to_crop, label_image):
    """
    Crops an image to the bounding box of a label.
    The label image can be float (it will be thresholded) or integer.
    """
    if label_image.GetPixelIDValue() not in [sitk.sitkUInt8, sitk.sitkUInt16, sitk.sitkUInt32, sitk.sitkUInt64]:
        integer_mask = sitk.BinaryThreshold(label_image, lowerThreshold=0.5)
        integer_mask = sitk.Cast(integer_mask, sitk.sitkUInt8)
    else:
        integer_mask = label_image

    # Calculate statistics on the integer mask
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(integer_mask)

    if stats.GetNumberOfLabels() == 0 or 1 not in stats.GetLabels():
        raise ValueError(f"Label value 1 not found in mask after processing.")

    # BBox format: (startX, startY, startZ, sizeX, sizeY, sizeZ)
    bbox = stats.GetBoundingBox(1)
    crop_size = bbox[3:6]
    crop_index = bbox[0:3]

    # Crop the *original* input image using the calculated bounding box
    return sitk.RegionOfInterest(image_to_crop, crop_size, crop_index)


def _read_stl(file_in_path, voxel_size=1.0):
    mesh = trimesh.load_mesh(file_in_path)
    voxelized_mesh = mesh.voxelized(pitch=voxel_size)
    binary_matrix = voxelized_mesh.fill().matrix.astype(np.int8)

    affine_matrix = voxelized_mesh.transform.copy()
    # Convert LPS to RAS
    affine_matrix[0, 0] *= -1
    affine_matrix[1, 1] *= -1
    affine_matrix[0, 3] *= -1
    affine_matrix[1, 3] *= -1

    return nib.Nifti1Image(binary_matrix, affine_matrix)


def stl_to_nifti(file_in_path, file_out_path, voxel_size):
    nib.save(_read_stl(file_in_path, voxel_size), file_out_path)


def _stl_to_nifti(temp_dir, file_path, voxel_size, data_type):
    tmp_path = os.path.join(temp_dir, "tmp.nii.gz")
    stl_to_nifti(file_path, tmp_path, voxel_size=voxel_size)
    return sitk.ReadImage(tmp_path, data_type)


def read_image(file_path, voxel_size=1.5, temp_dir=None, data_type=sitk.sitkFloat32):
    if file_path.endswith('.stl'):
        with tempfile.TemporaryDirectory() if temp_dir is None else nullcontext(temp_dir) as td:
            return _stl_to_nifti(td, file_path, voxel_size, data_type)
    elif file_path.endswith(('.nii', '.nii.gz', '.nrrd')):
        return sitk.ReadImage(file_path, data_type)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
