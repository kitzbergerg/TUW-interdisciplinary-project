import argparse

import SimpleITK as sitk

from utils.image_processing import read_image


def compare(ground_truth, comparison, voxel_size):
    ground_truth = read_image(ground_truth, voxel_size=voxel_size, data_type=sitk.sitkUInt8)

    labelstats = sitk.LabelOverlapMeasuresImageFilter()
    hausdorff = sitk.HausdorffDistanceImageFilter()
    for file in comparison:
        other_img = read_image(file, voxel_size=voxel_size)
        resampled = sitk.Resample(other_img, interpolator=sitk.sitkLinear, referenceImage=ground_truth)
        resampled = sitk.BinaryThreshold(resampled, lowerThreshold=0.5)

        labelstats.Execute(resampled, ground_truth)
        hausdorff.Execute(resampled, ground_truth)
        print(f"Dice Similarity Coefficient: {labelstats.GetDiceCoefficient():.4f}, Hausdorff Distance: {hausdorff.GetHausdorffDistance():.4f}, File: {file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare NIfTI files.')
    parser.add_argument('ground_truth', type=str, help='Path to the first file.')
    parser.add_argument('comparison', nargs='+', default=[], help='Paths to other files to compare against.')
    parser.add_argument('-v', '--voxel_size', type=float, default=0.3, help='Voxel Size for STL to NIfTI conversion.')
    args = parser.parse_args()

    compare(args.ground_truth, args.comparison, args.voxel_size)
