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
            "CameraInit": "7.0", 
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
            "uids": {
                "0": "9b90e3b468adc487fe2905e0cc78328216966317"
            }, 
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
            "uids": {
                "0": "3b8b39e478a30aa0ef1871576665b2914204a919"
            }, 
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
            "uids": {
                "0": "45cca14aba2a8c4f68c79a15d3fbc48f30ae9d66"
            }, 
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
            "uids": {
                "0": "9225abd943d28be4387a8a8902711d0b7c604a2a"
            }, 
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
            "uids": {
                "0": "af67674ecc8524592fe2b217259c241167e28dcd"
            }, 
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
            "uids": {
                "0": "a076f9e959d62b3a6f63d3f6493527b857eab8d6"
            }, 
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
                "describerTypes": [
                    "sift"
                ], 
                "describerQuality": "high", 
                "input": "{LdrToHdrMerge_1.outSfMData}", 
                "describerPreset": "high"
            }, 
            "nodeType": "FeatureExtraction", 
            "uids": {
                "0": "04f8824c2e2f206b47f05edaf76def15fa91446b"
            }, 
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
            "uids": {
                "0": "70edd7fe8194bf35dcb0b221141cd4abd2354547"
            }, 
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
            "uids": {
                "0": "1f1e629021e2280291046226e009a52dbb7809c1"
            }, 
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
            "uids": {
                "0": "f9436e97e444fa71a05aa5cf7639b206df8ba282"
            }, 
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
            "uids": {
                "0": "6956c52a8d18cb4cdb7ceb0db68f4deb84a37aee"
            }, 
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
            "uids": {
                "0": "b8568fb40b68b42ac80c18df2dcdf600744fe3e1"
            }, 
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
            "uids": {
                "0": "dd02562c5c3b1e18e42561d99590cbf4ff5ba35a"
            }, 
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
            "uids": {
                "0": "47b0976fc98eefcbc0342bbb63e7d27ef3e0d4de"
            }, 
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
                "useFisheye": true, 
                "dependency": [
                    "{FeatureExtraction_1.output}"
                ], 
                "input": "{FeatureExtraction_1.input}"
            }, 
            "nodeType": "PanoramaInit", 
            "uids": {
                "0": "2fd95a957eb42ffc8fb1c24d2666afcd859ba079"
            }, 
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
            "uids": {
                "0": "c0fbe0b12fe47ada6a1ca8f74d266e99c1cc548c"
            }, 
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