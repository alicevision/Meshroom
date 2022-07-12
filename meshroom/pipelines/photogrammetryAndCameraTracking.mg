{
    "header": {
        "pipelineVersion": "2.2", 
        "releaseVersion": "2021.1.0", 
        "fileVersion": "1.1", 
        "nodesVersions": {
            "ExportAnimatedCamera": "2.0", 
            "FeatureMatching": "2.0", 
            "DistortionCalibration": "2.0", 
            "CameraInit": "7.0", 
            "ImageMatchingMultiSfM": "1.0", 
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "StructureFromMotion": "2.0"
        }
    }, 
    "graph": {
        "DistortionCalibration_1": {
            "inputs": {
                "verboseLevel": "info", 
                "input": "{CameraInit_2.output}", 
                "lensGrid": []
            }, 
            "nodeType": "DistortionCalibration", 
            "uids": {
                "0": "8afea9d171904cdb6ba1c0b116cb60de3ccb6fb4"
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
                200, 
                320
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "StructureFromMotion_1": {
            "inputs": {
                "localizerEstimatorMaxIterations": 4096, 
                "minAngleForLandmark": 2.0, 
                "filterTrackForks": false, 
                "minNumberOfObservationsForTriangulation": 2, 
                "maxAngleInitialPair": 40.0, 
                "observationConstraint": "Scale", 
                "maxNumberOfMatches": 0, 
                "localizerEstimator": "acransac", 
                "describerTypes": "{FeatureMatching_1.describerTypes}", 
                "lockScenePreviouslyReconstructed": false, 
                "localBAGraphDistance": 1, 
                "minNbCamerasToRefinePrincipalPoint": 3, 
                "lockAllIntrinsics": false, 
                "input": "{FeatureMatching_1.input}", 
                "featuresFolders": "{FeatureMatching_1.featuresFolders}", 
                "useRigConstraint": true, 
                "rigMinNbCamerasForCalibration": 20, 
                "initialPairA": "", 
                "initialPairB": "", 
                "interFileExtension": ".abc", 
                "useLocalBA": true, 
                "computeStructureColor": true, 
                "matchesFolders": [
                    "{FeatureMatching_1.output}"
                ], 
                "minInputTrackLength": 2, 
                "useOnlyMatchesFromInputFolder": false, 
                "verboseLevel": "info", 
                "minAngleForTriangulation": 3.0, 
                "maxReprojectionError": 4.0, 
                "minAngleInitialPair": 5.0, 
                "minNumberOfMatches": 0, 
                "localizerEstimatorError": 0.0
            }, 
            "nodeType": "StructureFromMotion", 
            "uids": {
                "0": "89c3db0849ba07dfac5e97ca9e27dd690dc476ce"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/sfm.abc", 
                "extraInfoFolder": "{cache}/{nodeType}/{uid0}/", 
                "outputViewsAndPoses": "{cache}/{nodeType}/{uid0}/cameras.sfm"
            }, 
            "position": [
                800, 
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
                "describerQuality": "normal", 
                "gridFiltering": true, 
                "input": "{CameraInit_1.output}", 
                "describerPreset": "normal"
            }, 
            "nodeType": "FeatureExtraction", 
            "uids": {
                "0": "a07fb8d05b63327d05461954c2fd2a00f201275b"
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
                200, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "CameraInit_2": {
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
                    "fisheye4", 
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
                160
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "ExportAnimatedCamera_1": {
            "inputs": {
                "exportFullROD": false, 
                "undistortedImageType": "exr", 
                "exportUVMaps": true, 
                "verboseLevel": "info", 
                "sfmDataFilter": "{StructureFromMotion_1.output}", 
                "exportUndistortedImages": false, 
                "input": "{StructureFromMotion_2.output}", 
                "viewFilter": "", 
                "correctPrincipalPoint": true
            }, 
            "nodeType": "ExportAnimatedCamera", 
            "uids": {
                "0": "6f482ab9e161bd79341c5cd4a43ab9f8e39aec1f"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 1
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/", 
                "outputUndistorted": "{cache}/{nodeType}/{uid0}/undistort", 
                "outputCamera": "{cache}/{nodeType}/{uid0}/camera.abc"
            }, 
            "position": [
                1600, 
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
                    "fisheye4", 
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
        "ImageMatchingMultiSfM_1": {
            "inputs": {
                "minNbImages": 200, 
                "matchingMode": "a/a+a/b", 
                "nbNeighbors": 10, 
                "tree": "${ALICEVISION_VOCTREE}", 
                "nbMatches": 5, 
                "verboseLevel": "info", 
                "weights": "", 
                "maxDescriptors": 500, 
                "input": "{FeatureExtraction_2.input}", 
                "inputB": "{StructureFromMotion_1.output}", 
                "method": "SequentialAndVocabularyTree", 
                "featuresFolders": [
                    "{FeatureExtraction_2.output}"
                ]
            }, 
            "nodeType": "ImageMatchingMultiSfM", 
            "uids": {
                "0": "ef147c1bc069c7689863c7e14cdbbaca86af4006"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/imageMatches.txt", 
                "outputCombinedSfM": "{cache}/{nodeType}/{uid0}/combineSfM.sfm"
            }, 
            "position": [
                1000, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "FeatureExtraction_2": {
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
                "describerQuality": "normal", 
                "gridFiltering": true, 
                "input": "{CameraInit_2.output}", 
                "describerPreset": "normal"
            }, 
            "nodeType": "FeatureExtraction", 
            "uids": {
                "0": "a07fb8d05b63327d05461954c2fd2a00f201275b"
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
                200, 
                160
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
                "input": "{FeatureExtraction_1.input}", 
                "method": "SequentialAndVocabularyTree", 
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ]
            }, 
            "nodeType": "ImageMatching", 
            "uids": {
                "0": "46fb9072ac753d60bec7dda9c8674b0568506ddf"
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
                400, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "FeatureMatching_2": {
            "inputs": {
                "verboseLevel": "info", 
                "describerTypes": "{FeatureExtraction_2.describerTypes}", 
                "exportDebugFiles": false, 
                "crossMatching": false, 
                "geometricError": 0.0, 
                "maxMatches": 0, 
                "matchFromKnownCameraPoses": false, 
                "savePutativeMatches": false, 
                "guidedMatching": false, 
                "imagePairsList": "{ImageMatchingMultiSfM_1.output}", 
                "geometricEstimator": "acransac", 
                "geometricFilterType": "fundamental_matrix", 
                "maxIteration": 2048, 
                "distanceRatio": 0.8, 
                "input": "{DistortionCalibration_1.outSfMData}", 
                "photometricMatchingMethod": "ANN_L2", 
                "knownPosesGeometricErrorMax": 5.0, 
                "featuresFolders": "{ImageMatchingMultiSfM_1.featuresFolders}"
            }, 
            "nodeType": "FeatureMatching", 
            "uids": {
                "0": "7bb42f40b3f607da7e9f5f432409ddf6ef9c5951"
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
                "0": "3b1f2c3fcfe0b94c65627c397a2671ba7594827d"
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
                600, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "StructureFromMotion_2": {
            "inputs": {
                "localizerEstimatorMaxIterations": 4096, 
                "minAngleForLandmark": 0.5, 
                "filterTrackForks": false, 
                "minNumberOfObservationsForTriangulation": 3, 
                "maxAngleInitialPair": 40.0, 
                "observationConstraint": "Scale", 
                "maxNumberOfMatches": 0, 
                "localizerEstimator": "acransac", 
                "describerTypes": "{FeatureMatching_2.describerTypes}", 
                "lockScenePreviouslyReconstructed": false, 
                "localBAGraphDistance": 1, 
                "minNbCamerasToRefinePrincipalPoint": 3, 
                "lockAllIntrinsics": false, 
                "input": "{FeatureMatching_2.input}", 
                "featuresFolders": "{FeatureMatching_2.featuresFolders}", 
                "useRigConstraint": true, 
                "rigMinNbCamerasForCalibration": 20, 
                "initialPairA": "", 
                "initialPairB": "", 
                "interFileExtension": ".abc", 
                "useLocalBA": true, 
                "computeStructureColor": true, 
                "matchesFolders": [
                    "{FeatureMatching_2.output}"
                ], 
                "minInputTrackLength": 5, 
                "useOnlyMatchesFromInputFolder": false, 
                "verboseLevel": "info", 
                "minAngleForTriangulation": 1.0, 
                "maxReprojectionError": 4.0, 
                "minAngleInitialPair": 5.0, 
                "minNumberOfMatches": 0, 
                "localizerEstimatorError": 0.0
            }, 
            "nodeType": "StructureFromMotion", 
            "uids": {
                "0": "4bc466c45bc7b430553752d1eb1640c581c43e36"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/sfm.abc", 
                "extraInfoFolder": "{cache}/{nodeType}/{uid0}/", 
                "outputViewsAndPoses": "{cache}/{nodeType}/{uid0}/cameras.sfm"
            }, 
            "position": [
                1400, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }
    }
}