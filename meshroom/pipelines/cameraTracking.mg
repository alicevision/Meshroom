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
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "StructureFromMotion": "2.0"
        }
    }, 
    "graph": {
        "DistortionCalibration_1": {
            "inputs": {
                "verboseLevel": "info", 
                "input": "{CameraInit_1.output}", 
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
                160
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "ImageMatching_1": {
            "inputs": {
                "minNbImages": 200, 
                "nbNeighbors": 10, 
                "tree": "${ALICEVISION_VOCTREE}", 
                "maxDescriptors": 500, 
                "verboseLevel": "info", 
                "weights": "", 
                "nbMatches": 5, 
                "input": "{FeatureExtraction_1.input}", 
                "method": "SequentialAndVocabularyTree", 
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ]
            }, 
            "nodeType": "ImageMatching", 
            "uids": {
                "0": "832b744de5fa804d7d63ea255419b1afaf24f723"
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
        "StructureFromMotion_1": {
            "inputs": {
                "localizerEstimatorMaxIterations": 4096, 
                "minAngleForLandmark": 0.5, 
                "filterTrackForks": false, 
                "minNumberOfObservationsForTriangulation": 3, 
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
                "0": "4d198974784fd71f5a1c189e10c2914e56523585"
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
        "ExportAnimatedCamera_1": {
            "inputs": {
                "exportFullROD": false, 
                "undistortedImageType": "exr", 
                "exportUVMaps": true, 
                "verboseLevel": "info", 
                "sfmDataFilter": "", 
                "exportUndistortedImages": false, 
                "input": "{StructureFromMotion_1.output}", 
                "viewFilter": "", 
                "correctPrincipalPoint": true
            }, 
            "nodeType": "ExportAnimatedCamera", 
            "uids": {
                "0": "31413f19e51b239874733f13f9628286fd185c18"
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
                1000, 
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
                "input": "{DistortionCalibration_1.outSfMData}", 
                "photometricMatchingMethod": "ANN_L2", 
                "knownPosesGeometricErrorMax": 5.0, 
                "featuresFolders": "{ImageMatching_1.featuresFolders}"
            }, 
            "nodeType": "FeatureMatching", 
            "uids": {
                "0": "8386c096445d6988ea7d14f1ae3192978a4dd2e8"
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
        }
    }
}