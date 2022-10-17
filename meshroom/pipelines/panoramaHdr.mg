{
    "header": {
        "nodesVersions": {
            "PanoramaSeams": "2.0", 
            "FeatureMatching": "2.0", 
            "ImageProcessing": "3.0", 
            "PanoramaCompositing": "2.0", 
            "LdrToHdrMerge": "4.0", 
            "PanoramaEstimation": "1.0", 
            "LdrToHdrCalibration": "3.0", 
            "LdrToHdrSampling": "4.0", 
            "PanoramaInit": "2.0", 
            "CameraInit": "8.0", 
            "SfMTransform": "3.0", 
            "PanoramaMerging": "1.0", 
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "PanoramaPrepareImages": "1.1", 
            "PanoramaWarping": "1.0"
        }, 
        "releaseVersion": "2021.1.0", 
        "fileVersion": "1.1", 
        "template": true
    }, 
    "graph": {
        "LdrToHdrMerge_1": {
            "inputs": {
                "channelQuantizationPower": "{LdrToHdrCalibration_1.channelQuantizationPower}", 
                "byPass": "{LdrToHdrCalibration_1.byPass}", 
                "input": "{LdrToHdrCalibration_1.input}", 
                "userNbBrackets": "{LdrToHdrCalibration_1.userNbBrackets}", 
                "response": "{LdrToHdrCalibration_1.response}"
            }, 
            "nodeType": "LdrToHdrMerge", 
            "parallelization": {
                "blockSize": 2, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "outSfMData": "{cache}/{nodeType}/{uid0}/sfmData.sfm"
            }, 
            "position": [
                800, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "ImageProcessing_1": {
            "inputs": {
                "extension": "exr", 
                "fillHoles": true, 
                "input": "{PanoramaMerging_1.outputPanorama}", 
                "fixNonFinite": true
            }, 
            "nodeType": "ImageProcessing", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/", 
                "outputImages": "{cache}/{nodeType}/{uid0}/panorama.exr"
            }, 
            "position": [
                3000, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "PanoramaWarping_1": {
            "inputs": {
                "input": "{SfMTransform_1.output}"
            }, 
            "nodeType": "PanoramaWarping", 
            "parallelization": {
                "blockSize": 5, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                2200, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "LdrToHdrCalibration_1": {
            "inputs": {
                "samples": "{LdrToHdrSampling_1.output}", 
                "channelQuantizationPower": "{LdrToHdrSampling_1.channelQuantizationPower}", 
                "byPass": "{LdrToHdrSampling_1.byPass}", 
                "input": "{LdrToHdrSampling_1.input}", 
                "userNbBrackets": "{LdrToHdrSampling_1.userNbBrackets}"
            }, 
            "nodeType": "LdrToHdrCalibration", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "response": "{cache}/{nodeType}/{uid0}/response.csv"
            }, 
            "position": [
                600, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "LdrToHdrSampling_1": {
            "inputs": {
                "input": "{PanoramaPrepareImages_1.output}"
            }, 
            "nodeType": "LdrToHdrSampling", 
            "parallelization": {
                "blockSize": 2, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                400, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "ImageMatching_1": {
            "inputs": {
                "input": "{PanoramaInit_1.outSfMData}", 
                "method": "FrustumOrVocabularyTree", 
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ]
            }, 
            "nodeType": "ImageMatching", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/imageMatches.txt"
            }, 
            "position": [
                1400, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "FeatureExtraction_1": {
            "inputs": {
                "describerQuality": "high", 
                "input": "{LdrToHdrMerge_1.outSfMData}"
            }, 
            "nodeType": "FeatureExtraction", 
            "parallelization": {
                "blockSize": 40, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                1000, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "PanoramaMerging_1": {
            "inputs": {
                "compositingFolder": "{PanoramaCompositing_1.output}", 
                "input": "{PanoramaCompositing_1.input}"
            }, 
            "nodeType": "PanoramaMerging", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "outputPanorama": "{cache}/{nodeType}/{uid0}/panorama.{outputFileTypeValue}"
            }, 
            "position": [
                2800, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "PanoramaCompositing_1": {
            "inputs": {
                "warpingFolder": "{PanoramaSeams_1.warpingFolder}", 
                "labels": "{PanoramaSeams_1.output}", 
                "input": "{PanoramaSeams_1.input}"
            }, 
            "nodeType": "PanoramaCompositing", 
            "parallelization": {
                "blockSize": 5, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                2600, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "CameraInit_1": {
            "inputs": {
                "allowedCameraModels": [
                    "pinhole", 
                    "radial1", 
                    "radial3", 
                    "brown", 
                    "fisheye1", 
                    "3deanamorphic4", 
                    "3deradial4", 
                    "3declassicld"
                ]
            }, 
            "nodeType": "CameraInit", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/cameraInit.sfm"
            }, 
            "position": [
                0, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "PanoramaPrepareImages_1": {
            "inputs": {
                "input": "{CameraInit_1.output}"
            }, 
            "nodeType": "PanoramaPrepareImages", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/cameraInit.sfm"
            }, 
            "position": [
                200, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "SfMTransform_1": {
            "inputs": {
                "method": "manual", 
                "input": "{PanoramaEstimation_1.output}"
            }, 
            "nodeType": "SfMTransform", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/panorama.abc", 
                "outputViewsAndPoses": "{cache}/{nodeType}/{uid0}/cameras.sfm"
            }, 
            "position": [
                2000, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "PanoramaSeams_1": {
            "inputs": {
                "input": "{PanoramaWarping_1.input}", 
                "warpingFolder": "{PanoramaWarping_1.output}"
            }, 
            "nodeType": "PanoramaSeams", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/labels.exr"
            }, 
            "position": [
                2400, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "PanoramaEstimation_1": {
            "inputs": {
                "matchesFolders": [
                    "{FeatureMatching_1.output}"
                ], 
                "input": "{FeatureMatching_1.input}", 
                "describerTypes": "{FeatureMatching_1.describerTypes}", 
                "featuresFolders": "{FeatureMatching_1.featuresFolders}"
            }, 
            "nodeType": "PanoramaEstimation", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/panorama.abc", 
                "outputViewsAndPoses": "{cache}/{nodeType}/{uid0}/cameras.sfm"
            }, 
            "position": [
                1800, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "PanoramaInit_1": {
            "inputs": {
                "dependency": [
                    "{FeatureExtraction_1.output}"
                ], 
                "input": "{FeatureExtraction_1.input}"
            }, 
            "nodeType": "PanoramaInit", 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "outSfMData": "{cache}/{nodeType}/{uid0}/sfmData.sfm"
            }, 
            "position": [
                1200, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "FeatureMatching_1": {
            "inputs": {
                "describerTypes": "{FeatureExtraction_1.describerTypes}", 
                "imagePairsList": "{ImageMatching_1.output}", 
                "input": "{ImageMatching_1.input}", 
                "featuresFolders": "{ImageMatching_1.featuresFolders}"
            }, 
            "nodeType": "FeatureMatching", 
            "parallelization": {
                "blockSize": 20, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                1600, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }
    }
}