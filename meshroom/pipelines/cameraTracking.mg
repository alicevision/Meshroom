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
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "StructureFromMotion": "2.0",
            "Publish": "1.2"
        }
    }, 
    "graph": {
        "DistortionCalibration_1": {
            "inputs": {
                "input": "{CameraInit_1.output}"
            }, 
            "nodeType": "DistortionCalibration", 
            "position": [
                200, 
                160
            ]
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
            "position": [
                800, 
                0
            ]
        }, 
        "ExportAnimatedCamera_1": {
            "inputs": {
                "input": "{StructureFromMotion_1.output}"
            }, 
            "nodeType": "ExportAnimatedCamera", 
            "position": [
                1000, 
                0
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
        "FeatureMatching_1": {
            "inputs": {
                "describerTypes": "{FeatureExtraction_1.describerTypes}", 
                "imagePairsList": "{ImageMatching_1.output}", 
                "input": "{DistortionCalibration_1.outSfMData}", 
                "featuresFolders": "{ImageMatching_1.featuresFolders}"
            }, 
            "nodeType": "FeatureMatching", 
            "position": [
                600, 
                0
            ]
        },
        "Publish_1": {
            "nodeType": "Publish",
            "position": [
                1200,
                0
            ],
            "inputs": {
                "inputFiles": [
                    "{ExportAnimatedCamera_1.output}"
                ]
            }
        }
    }
}
