{
    "header": {
        "pipelineVersion": "2.2", 
        "releaseVersion": "2021.1.0", 
        "fileVersion": "1.1", 
        "template": true, 
        "nodesVersions": {
            "ExportAnimatedCamera": "2.0", 
            "FeatureMatching": "2.0", 
            "DistortionCalibration": "2.0", 
            "CameraInit": "8.0", 
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "StructureFromMotion": "2.0"
        }
    }, 
    "graph": {
        "DistortionCalibration_1": {
            "inputs": {
                "input": "{CameraInit_1.output}"
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
                "nbNeighbors": 10, 
                "nbMatches": 5, 
                "input": "{FeatureExtraction_1.input}", 
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
                "input": "{CameraInit_1.output}"
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
                "minAngleForLandmark": 0.5, 
                "minNumberOfObservationsForTriangulation": 3, 
                "describerTypes": "{FeatureMatching_1.describerTypes}", 
                "input": "{FeatureMatching_1.input}", 
                "featuresFolders": "{FeatureMatching_1.featuresFolders}", 
                "matchesFolders": [
                    "{FeatureMatching_1.output}"
                ], 
                "minInputTrackLength": 5, 
                "minAngleForTriangulation": 1.0
            }, 
            "nodeType": "StructureFromMotion", 
            "uids": {
                "0": "28715b8d4a51e5a90fbfee17d9eb193262116845"
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
                "input": "{StructureFromMotion_1.output}"
            }, 
            "nodeType": "ExportAnimatedCamera", 
            "uids": {
                "0": "65b4d273f9b9c6a177a8f586b1f9a085f3430133"
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
            "inputs": {}, 
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
                "describerTypes": "{FeatureExtraction_1.describerTypes}", 
                "imagePairsList": "{ImageMatching_1.output}", 
                "input": "{DistortionCalibration_1.outSfMData}", 
                "featuresFolders": "{ImageMatching_1.featuresFolders}"
            }, 
            "nodeType": "FeatureMatching", 
            "uids": {
                "0": "d6266b2126948174744b0ff6c33d96440e7596de"
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