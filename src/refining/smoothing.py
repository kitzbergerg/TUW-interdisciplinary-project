import SimpleITK as sitk
import argparse
from scipy.ndimage import gaussian_filter

def refine(mask_path, output_path, zoom_factor):
    # --- Step 1: Load the image using SimpleITK ---
    itk_image = sitk.ReadImage(mask_path, sitk.sitkFloat32)

    # --- Step 2: Get original properties and calculate new ones ---
    original_spacing = itk_image.GetSpacing()
    original_size = itk_image.GetSize()

    # Calculate the new spacing and size
    new_spacing = [s / zoom_factor for s in original_spacing]
    new_size = [int(round(s * zoom_factor)) for s in original_size]

    # --- Step 3: Resample using SimpleITK ---
    resampler = sitk.ResampleImageFilter()
    resampler.SetOutputSpacing(new_spacing)
    resampler.SetSize(new_size)
    resampler.SetOutputDirection(itk_image.GetDirection())
    resampler.SetOutputOrigin(itk_image.GetOrigin())
    resampler.SetTransform(sitk.Transform())
    resampler.SetDefaultPixelValue(0)
    # Use Nearest Neighbor for segmentation masks to avoid creating new values
    resampler.SetInterpolator(sitk.sitkNearestNeighbor)

    # Execute the resampling
    hr_blocky_itk_image = resampler.Execute(itk_image)

    # --- Step 4: Convert to NumPy for Smoothing ---
    hr_blocky_data = sitk.GetArrayFromImage(hr_blocky_itk_image)

    # --- Step 5: Apply your smoothing logic ---
    blurred = gaussian_filter(hr_blocky_data, sigma=zoom_factor * 1.5)
    blurred[blurred < 0.5] = 0
    blurred[blurred >= 0.5] = 1

    # --- Step 6: Convert back to SimpleITK image to save correctly ---
    final_itk_image = sitk.GetImageFromArray(blurred)
    # Copy all the correct geometric information from the resampled image
    final_itk_image.CopyInformation(hr_blocky_itk_image)

    # Save the final result
    sitk.WriteImage(final_itk_image, output_path)
    print(f"✅ Refined segmentation saved to: {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Refine a 3D segmentation mask using a smoothing.')
    parser.add_argument('mask_path', type=str, help='Path to the upsampled segmentation NIfTI file.')
    parser.add_argument('output_path', type=str, help='Path to save the refined NIfTI mask.')
    parser.add_argument('-z', '--zoom_factor', type=float, default=2, help='Upsampling zoom factor.')

    args = parser.parse_args()
    refine(args.mask_path, args.output_path, args.zoom_factor)
