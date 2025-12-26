import SimpleITK as sitk
import argparse

from utils.image_processing import read_image


def crop_to_bbox(image, padding=0):
    if image.GetPixelIDValue() not in [sitk.sitkUInt8, sitk.sitkUInt16, sitk.sitkUInt32, sitk.sitkUInt64]:
        integer_mask = sitk.BinaryThreshold(image, lowerThreshold=0.5)
        integer_mask = sitk.Cast(integer_mask, sitk.sitkUInt8)
    else:
        integer_mask = image

    # Calculate statistics on the integer mask
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(integer_mask)

    if stats.GetNumberOfLabels() == 0 or 1 not in stats.GetLabels():
        raise ValueError(f"Label value 1 not found in mask after processing.")

    # Get original bounding box: (startX, startY, startZ, sizeX, sizeY, sizeZ)
    bbox = stats.GetBoundingBox(1)
    img_size = image.GetSize()

    new_index = []
    new_size = []

    # Iterate through X, Y, Z dimensions (0, 1, 2)
    for dim in range(3):
        # Calculate new start: subtract padding, clamp to 0
        pad_start = max(0, bbox[dim] - padding)

        # Calculate new end: add original length + padding, clamp to max dimension size
        pad_end = min(img_size[dim], bbox[dim] + bbox[dim + 3] + padding)

        # Determine new size
        dim_size = pad_end - pad_start

        new_index.append(pad_start)
        new_size.append(dim_size)

    return sitk.RegionOfInterest(image, new_size, new_index)


def preprocess_for_inference(ct_path, low_res_path, output_ct_path, output_low_res_path):
    """
    Crops a CT and low-res mask to the bounding box of the low-res mask.
    This prepares them for nnU-Net inference.
    """
    print("Loading images...")
    ct_image = read_image(ct_path)
    low_res_image = crop_to_bbox(read_image(low_res_path), padding=4)

    # Resample the CT to match the low-res mask's grid BEFORE cropping.
    # This ensures both images are aligned.
    print("Resampling CT to match low-res mask grid...")
    resampled_ct = sitk.Resample(
        ct_image,
        interpolator=sitk.sitkLinear,
        referenceImage=low_res_image,
    )

    # Save to specified output paths
    sitk.WriteImage(resampled_ct, output_ct_path)
    sitk.WriteImage(low_res_image, output_low_res_path)
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
