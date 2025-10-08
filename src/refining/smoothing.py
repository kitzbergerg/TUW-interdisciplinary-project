import nibabel as nib
import argparse
from scipy.ndimage import gaussian_filter, zoom


def upsample_segmentation(image_data, zoom_factor):
    hr_seg_data = zoom(
        image_data,
        zoom_factor,
        order=0,
        mode='nearest'
    )

    return hr_seg_data


def refine(file_path, output_path, zoom_factor):
    nifti_file = nib.load(file_path)
    image_data = nifti_file.get_fdata()
    upsampled = upsample_segmentation(image_data, zoom_factor)

    blurred = gaussian_filter(upsampled, sigma=zoom_factor * 1.5)
    blurred[blurred < 0.5] = 0
    blurred[blurred >= 0.5] = 1

    hr_affine = nifti_file.affine.copy()
    for i in range(3):
        hr_affine[i, i] /= zoom_factor

    refined_nii = nib.Nifti1Image(blurred, hr_affine, header=nifti_file.header)
    nib.save(refined_nii, output_path)
    print(f"✅ Refined segmentation saved to: {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Refine a 3D segmentation mask using a smoothing.')
    parser.add_argument('mask_path', type=str, help='Path to the upsampled segmentation NIfTI file.')
    parser.add_argument('output_path', type=str, help='Path to save the refined NIfTI mask.')
    parser.add_argument('-z', '--zoom_factor', type=float, default=2, help='Upsampling zoom factor.')

    args = parser.parse_args()
    refine(args.mask_path, args.output_path, args.zoom_factor)
