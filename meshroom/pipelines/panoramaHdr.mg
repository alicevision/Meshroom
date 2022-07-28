{
    "header": {
        "nodesVersions": {
            "PanoramaSeams": "2.0", 
            "FeatureMatching": "2.0", 
            "ImageProcessing": "3.0", 
            "PanoramaCompositing": "2.0", 
            "LdrToHdrMerge": "4.0", 
            "LdrToHdrSampling": "4.0", 
            "LdrToHdrCalibration": "3.0", 
            "PanoramaEstimation": "1.0", 
            "PanoramaInit": "2.0", 
            "PanoramaMerging": "1.0", 
            "SfMTransform": "3.0", 
            "CameraInit": "7.0", 
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "PanoramaPrepareImages": "1.1", 
            "PanoramaWarping": "1.0"
        }, 
        "releaseVersion": "2021.1.0", 
        "fileVersion": "1.1"
    }, 
    "graph": {
        "LdrToHdrMerge_1": {
            "inputs": {
                "verboseLevel": "info", 
                "fusionWeight": "gaussian", 
                "channelQuantizationPower": "{LdrToHdrCalibration_1.channelQuantizationPower}", 
                "nbBrackets": 0, 
                "enableHighlight": false, 
                "offsetRefBracketIndex": 1, 
                "storageDataType": "float", 
                "highlightTargetLux": 120000.0, 
                "byPass": "{LdrToHdrCalibration_1.byPass}", 
                "highlightCorrectionFactor": 1.0, 
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
                "outputFormat": "rgba", 
                "sharpenFilter": {
                    "threshold": 0.0, 
                    "width": 3, 
                    "sharpenFilterEnabled": false, 
                    "contrast": 1.0
                }, 
                "extension": "exr", 
                "exposureCompensation": false, 
                "storageDataType": "float", 
                "inputFolders": [], 
                "verboseLevel": "info", 
                "metadataFolders": [], 
                "claheFilter": {
                    "claheClipLimit": 4.0, 
                    "claheTileGridSize": 8, 
                    "claheEnabled": false
                }, 
                "medianFilter": 0, 
                "fillHoles": true, 
                "reconstructedViewsOnly": false, 
                "input": "{PanoramaMerging_1.outputPanorama}", 
                "noiseFilter": {
                    "noiseEnabled": false, 
                    "noiseMethod": "uniform", 
                    "noiseB": 1.0, 
                    "noiseMono": true, 
                    "noiseA": 0.0
                }, 
                "scaleFactor": 1.0, 
                "bilateralFilter": {
                    "bilateralFilterDistance": 0, 
                    "bilateralFilterSigmaColor": 0.0, 
                    "bilateralFilterSigmaSpace": 0.0, 
                    "bilateralFilterEnabled": false
                }, 
                "contrast": 1.0, 
                "fixNonFinite": true
            }, 
            "nodeType": "ImageProcessing", 
            "uids": {
                "0": "d7845b276d97c3489223cce16a1e9d581d98a832"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/", 
                "outputImages": "{cache}/{nodeType}/{uid0}/panorama.exr", 
                "outSfMData": ""
            }, 
            "position": [
                3000, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "PanoramaWarping_1": {
            "inputs": {
                "panoramaWidth": 10000, 
                "maxPanoramaWidth": 70000, 
                "verboseLevel": "info", 
                "percentUpscale": 50, 
                "input": "{SfMTransform_1.output}", 
                "storageDataType": "float", 
                "estimateResolution": true
            }, 
            "nodeType": "PanoramaWarping", 
            "uids": {
                "0": "f2971d0c73b15fa99cbccbc9515de346ca141a1e"
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
                "maxTotalPoints": 1000000, 
                "nbBrackets": 0, 
                "calibrationMethod": "debevec", 
                "calibrationWeight": "default", 
                "verboseLevel": "info", 
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
                "blockSize": 256, 
                "nbBrackets": 0, 
                "verboseLevel": "info", 
                "radius": 5, 
                "byPass": false, 
                "channelQuantizationPower": 10, 
                "debug": false, 
                "input": "{PanoramaPrepareImages_1.output}", 
                "maxCountSample": 200, 
                "userNbBrackets": 0
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
                "minNbImages": 200, 
                "nbNeighbors": 5, 
                "tree": "${ALICEVISION_VOCTREE}", 
                "maxDescriptors": 500, 
                "verboseLevel": "info", 
                "weights": "", 
                "nbMatches": 40, 
                "input": "{PanoramaInit_1.outSfMData}", 
                "method": "FrustumOrVocabularyTree", 
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ]
            }, 
            "nodeType": "ImageMatching", 
            "uids": {
                "0": "7efc9cd43585003fc6eec0776a704e358f0a15de"
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
                "verboseLevel": "info", 
                "maxThreads": 0, 
                "describerTypes": [
                    "dspsift"
                ], 
                "maxNbFeatures": 0, 
                "relativePeakThreshold": 0.01, 
                "forceCpuExtraction": true, 
                "masksFolder": "", 
                "contrastFiltering": "GridSort", 
                "describerQuality": "high", 
                "gridFiltering": true, 
                "input": "{LdrToHdrMerge_1.outSfMData}", 
                "describerPreset": "normal"
            }, 
            "nodeType": "FeatureExtraction", 
            "uids": {
                "0": "1863cc0989ab0fd910d4fe293074ff94c4e586a1"
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
        "PanoramaSeams_1": {
            "inputs": {
                "verboseLevel": "info", 
                "input": "{PanoramaWarping_1.input}", 
                "warpingFolder": "{PanoramaWarping_1.output}", 
                "maxWidth": 5000, 
                "useGraphCut": true
            }, 
            "nodeType": "PanoramaSeams", 
            "uids": {
                "0": "0ee6da171bd684358b7c64dcc631f81ba743e1fa"
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
        "PanoramaCompositing_1": {
            "inputs": {
                "warpingFolder": "{PanoramaSeams_1.warpingFolder}", 
                "maxThreads": 4, 
                "labels": "{PanoramaSeams_1.output}", 
                "verboseLevel": "info", 
                "overlayType": "none", 
                "compositerType": "multiband", 
                "input": "{PanoramaSeams_1.input}", 
                "storageDataType": "float"
            }, 
            "nodeType": "PanoramaCompositing", 
            "uids": {
                "0": "8aba78572808d012e0bb376503c2016df943b3f0"
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
                "groupCameraFallback": "folder", 
                "intrinsics": [], 
                "viewIdRegex": ".*?(\\d+)", 
                "defaultFieldOfView": 45.0, 
                "allowedCameraModels": [
                    "pinhole", 
                    "radial1", 
                    "radial3", 
                    "brown", 
                    "fisheye1", 
                    "3deanamorphic4", 
                    "3deradial4", 
                    "3declassicld"
                ], 
                "verboseLevel": "info", 
                "viewIdMethod": "metadata", 
                "viewpoints": [], 
                "useInternalWhiteBalance": true, 
                "sensorDatabase": "${ALICEVISION_SENSOR_DB}"
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
                "verboseLevel": "info", 
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
                "applyScale": true, 
                "scale": 1.0, 
                "applyTranslation": true, 
                "landmarksDescriberTypes": [
                    "sift", 
                    "dspsift", 
                    "akaze"
                ], 
                "markers": [], 
                "method": "manual", 
                "verboseLevel": "info", 
                "input": "{PanoramaEstimation_1.output}", 
                "applyRotation": true, 
                "manualTransform": {
                    "manualTranslation": {
                        "y": 0.0, 
                        "x": 0.0, 
                        "z": 0.0
                    }, 
                    "manualRotation": {
                        "y": 0.0, 
                        "x": 0.0, 
                        "z": 0.0
                    }, 
                    "manualScale": 1.0
                }, 
                "transformation": ""
            }, 
            "nodeType": "SfMTransform", 
            "uids": {
                "0": "c72641a2cca50759bcf5283ae6e0b6f7abc3fe4a"
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
        "PanoramaMerging_1": {
            "inputs": {
                "verboseLevel": "info", 
                "compositingFolder": "{PanoramaCompositing_1.output}", 
                "outputFileType": "exr", 
                "storageDataType": "float", 
                "input": "{PanoramaCompositing_1.input}"
            }, 
            "nodeType": "PanoramaMerging", 
            "uids": {
                "0": "e007a4eb5fc5937b320638eba667cea183c0c642"
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
        "PanoramaEstimation_1": {
            "inputs": {
                "intermediateRefineWithFocalDist": false, 
                "offsetLongitude": 0.0, 
                "matchesFolders": [
                    "{FeatureMatching_1.output}"
                ], 
                "filterMatches": false, 
                "rotationAveragingWeighting": true, 
                "offsetLatitude": 0.0, 
                "verboseLevel": "info", 
                "maxAngularError": 100.0, 
                "lockAllIntrinsics": false, 
                "refine": true, 
                "input": "{FeatureMatching_1.input}", 
                "intermediateRefineWithFocal": false, 
                "describerTypes": "{FeatureMatching_1.describerTypes}", 
                "relativeRotation": "rotation_matrix", 
                "maxAngleToPrior": 20.0, 
                "rotationAveraging": "L2_minimization", 
                "featuresFolders": "{FeatureMatching_1.featuresFolders}"
            }, 
            "nodeType": "PanoramaEstimation", 
            "uids": {
                "0": "de946a7c1080873d15c9eb8a0523b544cf548719"
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
                "useFisheye": false, 
                "fisheyeCenterOffset": {
                    "fisheyeCenterOffset_y": 0.0, 
                    "fisheyeCenterOffset_x": 0.0
                }, 
                "initializeCameras": "No", 
                "nbViewsPerLine": [], 
                "debugFisheyeCircleEstimation": false, 
                "verboseLevel": "info", 
                "dependency": [
                    "{FeatureExtraction_1.output}"
                ], 
                "estimateFisheyeCircle": true, 
                "input": "{FeatureExtraction_1.input}", 
                "yawCW": 1, 
                "config": "", 
                "fisheyeRadius": 96.0, 
                "inputAngle": "None"
            }, 
            "nodeType": "PanoramaInit", 
            "uids": {
                "0": "702d6b973342e9203b50afea1470b4c01eb90174"
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
                "verboseLevel": "info", 
                "describerTypes": "{FeatureExtraction_1.describerTypes}", 
                "exportDebugFiles": false, 
                "crossMatching": false, 
                "geometricError": 0.0, 
                "maxMatches": 0, 
                "matchFromKnownCameraPoses": false, 
                "savePutativeMatches": false, 
                "guidedMatching": false, 
                "imagePairsList": "{ImageMatching_1.output}", 
                "geometricEstimator": "acransac", 
                "geometricFilterType": "fundamental_matrix", 
                "maxIteration": 2048, 
                "distanceRatio": 0.8, 
                "input": "{ImageMatching_1.input}", 
                "photometricMatchingMethod": "ANN_L2", 
                "knownPosesGeometricErrorMax": 5.0, 
                "featuresFolders": "{ImageMatching_1.featuresFolders}"
            }, 
            "nodeType": "FeatureMatching", 
            "uids": {
                "0": "cec6da6e894230ab66683c2e959bc9581ea5430e"
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