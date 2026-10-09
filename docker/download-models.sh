#!/usr/bin/env bash

# Download the AliceVision models and data (vocabulary tree, ONNX models, ColorChart model)
# into dl/aliceVision/, from where the Meshroom image copies them into its bundle.
# Files already present are kept.
set -e

# Work from the top level Meshroom directory, wherever the script is called from
cd "$(dirname "${BASH_SOURCE[0]}")/.."

DL_DIR=dl/aliceVision
mkdir -p "${DL_DIR}"

download() {
    # Download to a temporary name so that an interrupted download is not mistaken for a complete one
    test -f "${DL_DIR}/$2" || {
        wget "$1" -O "${DL_DIR}/$2.part"
        mv "${DL_DIR}/$2.part" "${DL_DIR}/$2"
    }
}

download "https://gitlab.com/alicevision/trainedVocabularyTreeData/raw/master/vlfeat_K80L3.SIFT.tree" vlfeat_K80L3.SIFT.tree
download "https://gitlab.com/alicevision/SphereDetectionModel/-/raw/main/sphereDetection_Mask-RCNN.onnx" sphereDetection_Mask-RCNN.onnx
download "https://gitlab.com/alicevision/semanticSegmentationModel/-/raw/main/fcn_resnet50.onnx" fcn_resnet50.onnx

test -d "${DL_DIR}/ColorChartDetectionModel" || {
    rm -rf "${DL_DIR}/ColorChartDetectionModel.part"
    git clone --depth 1 https://gitlab.com/alicevision/ColorchartDetectionModel.git "${DL_DIR}/ColorChartDetectionModel.part"
    rm -rf "${DL_DIR}/ColorChartDetectionModel.part/.git"
    mv "${DL_DIR}/ColorChartDetectionModel.part" "${DL_DIR}/ColorChartDetectionModel"
}
