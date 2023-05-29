{
    "header": {
        "pipelineVersion": "2.2", 
        "releaseVersion": "2023.1.0",
        "fileVersion": "1.1", 
        "template": true, 
        "nodesVersions": {
            "ExportAnimatedCamera": "2.0", 
            "FeatureMatching": "2.0", 
            "DistortionCalibration": "2.0", 
            "CameraInit": "9.0", 
            "ImageMatchingMultiSfM": "1.0", 
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "StructureFromMotion": "3.0",
            "Publish": "1.2"
        }
    }, 
    "graph": {
        "DistortionCalibration_1": {
            "inputs": {
                "input": "{CameraInit_2.output}"
            }, 
            "nodeType": "DistortionCalibration", 
            "position": [
                1024, 
                393
            ]
        }, 
        "ImageMatching_1": {
            "inputs": {
                "input": "{FeatureExtraction_1.input}", 
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ]
            }, 
            "nodeType": "ImageMatching", 
            "position": [
                400, 
                0
            ]
        }, 
        "FeatureExtraction_1": {
            "inputs": {
                "input": "{CameraInit_1.output}"
            }, 
            "nodeType": "FeatureExtraction", 
            "position": [
                200, 
                0
            ]
        }, 
        "StructureFromMotion_1": {
            "inputs": {
                "describerTypes": "{FeatureMatching_1.describerTypes}", 
                "input": "{FeatureMatching_1.input}", 
                "featuresFolders": "{FeatureMatching_1.featuresFolders}", 
                "matchesFolders": [
                    "{FeatureMatching_1.output}"
                ]
            }, 
            "nodeType": "StructureFromMotion", 
            "position": [
                800, 
                0
            ]
        }, 
        "ExportAnimatedCamera_1": {
            "inputs": {
                "sfmDataFilter": "{StructureFromMotion_1.output}", 
                "input": "{StructureFromMotion_2.output}"
            }, 
            "nodeType": "ExportAnimatedCamera", 
            "position": [
                1629, 
                212
            ]
        }, 
        "CameraInit_1": {
            "inputs": {}, 
            "nodeType": "CameraInit", 
            "position": [
                0, 
                0
            ]
        }, 
        "ImageMatchingMultiSfM_1": {
            "inputs": {
                "nbNeighbors": 10, 
                "nbMatches": 5, 
                "input": "{FeatureExtraction_2.input}", 
                "inputB": "{StructureFromMotion_1.output}", 
                "featuresFolders": [
                    "{FeatureExtraction_2.output}"
                ]
            }, 
            "nodeType": "ImageMatchingMultiSfM", 
            "position": [
                1029, 
                212
            ]
        }, 
        "CameraInit_2": {
            "inputs": {}, 
            "nodeType": "CameraInit", 
            "position": [
                -2, 
                223
            ]
        }, 
        "FeatureExtraction_2": {
            "inputs": {
                "input": "{CameraInit_2.output}"
            }, 
            "nodeType": "FeatureExtraction", 
            "position": [
                198, 
                223
            ]
        }, 
        "FeatureMatching_2": {
            "inputs": {
                "describerTypes": "{FeatureExtraction_2.describerTypes}", 
                "imagePairsList": "{ImageMatchingMultiSfM_1.output}", 
                "input": "{DistortionCalibration_1.outSfMData}", 
                "featuresFolders": "{ImageMatchingMultiSfM_1.featuresFolders}"
            }, 
            "nodeType": "FeatureMatching", 
            "position": [
                1229, 
                212
            ]
        }, 
        "FeatureMatching_1": {
            "inputs": {
                "describerTypes": "{FeatureExtraction_1.describerTypes}", 
                "imagePairsList": "{ImageMatching_1.output}", 
                "input": "{ImageMatching_1.input}", 
                "featuresFolders": "{ImageMatching_1.featuresFolders}"
            }, 
            "nodeType": "FeatureMatching", 
            "position": [
                600, 
                0
            ]
        }, 
        "StructureFromMotion_2": {
            "inputs": {
                "minAngleForLandmark": 0.5, 
                "minNumberOfObservationsForTriangulation": 3, 
                "describerTypes": "{FeatureMatching_2.describerTypes}", 
                "input": "{FeatureMatching_2.input}", 
                "featuresFolders": "{FeatureMatching_2.featuresFolders}", 
                "matchesFolders": [
                    "{FeatureMatching_2.output}"
                ], 
                "minInputTrackLength": 5, 
                "minAngleForTriangulation": 1.0
            }, 
            "nodeType": "StructureFromMotion", 
            "position": [
                1429, 
                212
            ]
        },
        "Publish_1": {
            "nodeType": "Publish",
            "position": [
                1829,
                212
            ],
            "inputs": {
                "inputFiles": [
                    "{ExportAnimatedCamera_1.output}"
                ]
            }
        }
    }
}
