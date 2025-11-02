import SimpleITK as sitk


def crop_to_label_bbox(image_to_crop, label_image, label_val=1, threshold=0.5):
    """
    Crops an image to the bounding box of a label.
    The label image can be float (it will be thresholded) or integer.
    """
    if label_image.GetPixelIDValue() not in [sitk.sitkUInt8, sitk.sitkUInt16, sitk.sitkUInt32, sitk.sitkUInt64]:
        # If label is float, threshold it to create an integer mask
        print(f"Thresholding float mask (>{threshold}) to integer for bounding box...")
        integer_mask = sitk.BinaryThreshold(
            label_image,
            lowerThreshold=threshold,
            upperThreshold=1e10,  # A very large number
            insideValue=label_val,
            outsideValue=0
        )
        integer_mask = sitk.Cast(integer_mask, sitk.sitkUInt8)
    else:
        integer_mask = label_image

    # Calculate statistics on the integer mask
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(integer_mask)

    if stats.GetNumberOfLabels() == 0 or label_val not in stats.GetLabels():
        raise ValueError(f"Label value {label_val} not found in mask after processing.")

    # BBox format: (startX, startY, startZ, sizeX, sizeY, sizeZ)
    bbox = stats.GetBoundingBox(label_val)
    crop_size = bbox[3:6]
    crop_index = bbox[0:3]

    # Crop the *original* input image using the calculated bounding box
    return sitk.RegionOfInterest(image_to_crop, crop_size, crop_index)
