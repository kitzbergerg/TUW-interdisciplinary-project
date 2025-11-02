import SimpleITK as sitk
import argparse
from preprocessing_utils import crop_to_label_bbox


def preprocess_for_inference(ct_path, low_res_path, output_ct_path, output_low_res_path):
    """
    Crops a CT and low-res mask to the bounding box of the low-res mask.
    This prepares them for nnU-Net inference.
    """
    print("Loading images...")
    ct_image = sitk.ReadImage(ct_path)
    low_res_image = sitk.ReadImage(low_res_path)

    # Resample the CT to match the low-res mask's grid BEFORE cropping.
    # This ensures both images are aligned.
    print("Resampling CT to match low-res mask grid...")
    resampled_ct = sitk.Resample(ct_image, referenceImage=low_res_image)

    print("Cropping images to low-res mask bounding box...")
    cropped_ct = crop_to_label_bbox(resampled_ct, low_res_image)
    cropped_low_res = crop_to_label_bbox(low_res_image, low_res_image)

    # Save to specified output paths
    sitk.WriteImage(cropped_ct, output_ct_path)
    sitk.WriteImage(cropped_low_res, output_low_res_path)
    print(f"Cropped CT saved to: {output_ct_path}")
    print(f"Cropped low-res mask saved to: {output_low_res_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Pre-process (crop) CT and low-res mask for nnU-Net inference.'
    )
    parser.add_argument('input_ct', type=str, help='Path to the full-size CT NIfTI file.')
    parser.add_argument('input_low_res', type=str, help='Path to the full-size low-res segmentation NIfTI file.')
    parser.add_argument('output_ct', type=str, help='Path to save the CROPPED CT file.')
    parser.add_argument('output_low_res', type=str, help='Path to save the CROPPED low-res mask file.')

    args = parser.parse_args()

    preprocess_for_inference(
        args.input_ct,
        args.input_low_res,
        args.output_ct,
        args.output_low_res
    )
