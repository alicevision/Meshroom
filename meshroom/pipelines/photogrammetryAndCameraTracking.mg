{
    "header": {
        "pipelineVersion": "2.2",
        "releaseVersion": "2023.2.0-develop",
        "fileVersion": "1.1",
        "template": true,
        "nodesVersions": {
            "Publish": "1.3",
            "StructureFromMotion": "3.0",
            "FeatureExtraction": "1.1",
            "FeatureMatching": "2.0",
            "CameraInit": "9.0",
            "ImageMatchingMultiSfM": "1.0",
            "ImageMatching": "2.0",
            "ExportAnimatedCamera": "2.0"
        }
    },
    "graph": {
        "ImageMatching_1": {
            "nodeType": "ImageMatching",
            "position": [
                400,
                0
            ],
            "inputs": {
                "input": "{FeatureExtraction_1.input}",
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ]
            }
        },
        "FeatureExtraction_1": {
            "nodeType": "FeatureExtraction",
            "position": [
                200,
                0
            ],
            "inputs": {
                "input": "{CameraInit_1.output}"
            }
        },
        "StructureFromMotion_1": {
            "nodeType": "StructureFromMotion",
            "position": [
                800,
                0
            ],
            "inputs": {
                "input": "{FeatureMatching_1.input}",
                "featuresFolders": "{FeatureMatching_1.featuresFolders}",
                "matchesFolders": [
                    "{FeatureMatching_1.output}"
                ],
                "describerTypes": "{FeatureMatching_1.describerTypes}"
            }
        },
        "ExportAnimatedCamera_1": {
            "nodeType": "ExportAnimatedCamera",
            "position": [
                1629,
                212
            ],
            "inputs": {
                "input": "{StructureFromMotion_2.output}",
                "sfmDataFilter": "{StructureFromMotion_1.output}"
            }
        },
        "CameraInit_1": {
            "nodeType": "CameraInit",
            "position": [
                0,
                0
            ],
            "inputs": {}
        },
        "ImageMatchingMultiSfM_1": {
            "nodeType": "ImageMatchingMultiSfM",
            "position": [
                1029,
                212
            ],
            "inputs": {
                "input": "{FeatureExtraction_2.input}",
                "inputB": "{StructureFromMotion_1.output}",
                "featuresFolders": [
                    "{FeatureExtraction_2.output}"
                ],
                "nbMatches": 5,
                "nbNeighbors": 10
            }
        },
        "FeatureMatching_1": {
            "nodeType": "FeatureMatching",
            "position": [
                600,
                0
            ],
            "inputs": {
                "input": "{ImageMatching_1.input}",
                "featuresFolders": "{ImageMatching_1.featuresFolders}",
                "imagePairsList": "{ImageMatching_1.output}",
                "describerTypes": "{FeatureExtraction_1.describerTypes}"
            }
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
        },
        "CameraInit_2": {
            "nodeType": "CameraInit",
            "position": [
                -2,
                223
            ],
            "inputs": {}
        },
        "FeatureExtraction_2": {
            "nodeType": "FeatureExtraction",
            "position": [
                198,
                223
            ],
            "inputs": {
                "input": "{CameraInit_2.output}"
            }
        },
        "FeatureMatching_2": {
            "nodeType": "FeatureMatching",
            "position": [
                1229,
                212
            ],
            "inputs": {
                "featuresFolders": "{ImageMatchingMultiSfM_1.featuresFolders}",
                "imagePairsList": "{ImageMatchingMultiSfM_1.output}",
                "describerTypes": "{FeatureExtraction_2.describerTypes}"
            }
        },
        "StructureFromMotion_2": {
            "nodeType": "StructureFromMotion",
            "position": [
                1429,
                212
            ],
            "inputs": {
                "input": "{FeatureMatching_2.input}",
                "featuresFolders": "{FeatureMatching_2.featuresFolders}",
                "matchesFolders": [
                    "{FeatureMatching_2.output}"
                ],
                "describerTypes": "{FeatureMatching_2.describerTypes}",
                "minInputTrackLength": 5,
                "minNumberOfObservationsForTriangulation": 3,
                "minAngleForTriangulation": 1.0,
                "minAngleForLandmark": 0.5
            }
        }
    }
}
