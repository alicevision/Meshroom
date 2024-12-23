{
    "header": {
        "releaseVersion": "2024.1.0-develop",
        "fileVersion": "2.0",
        "template": true,
        "nodesVersions": {
            "CameraInit": "11.0",
            "ConvertDistortion": "1.0",
            "ConvertSfMFormat": "2.0",
            "ExportAnimatedCamera": "2.0",
            "ExportDistortion": "2.0",
            "FeatureExtraction": "1.3",
            "FeatureMatching": "2.0",
            "ImageMatching": "2.0",
            "ImageSegmentationPrompt": "0.1",
            "NodalSfM": "2.0",
            "Publish": "1.3",
            "RelativePoseEstimating": "2.0",
            "ScenePreview": "2.0",
            "TracksBuilding": "1.0"
        }
    },
    "graph": {
        "CameraInit_1": {
            "nodeType": "CameraInit",
            "position": [
                -200,
                0
            ],
            "inputs": {},
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "ConvertDistortion_1": {
            "nodeType": "ConvertDistortion",
            "position": [
                1600,
                0
            ],
            "inputs": {
                "input": "{ExportAnimatedCamera_1.input}"
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "ConvertSfMFormat_1": {
            "nodeType": "ConvertSfMFormat",
            "position": [
                1400,
                200
            ],
            "inputs": {
                "input": "{NodalSfM_1.output}",
                "fileExt": "sfm",
                "structure": false,
                "observations": false
            },
            "internalInputs": {
                "color": "#4c594c"
            }
        },
        "ExportAnimatedCamera_1": {
            "nodeType": "ExportAnimatedCamera",
            "position": [
                1400,
                0
            ],
            "inputs": {
                "input": "{NodalSfM_1.output}",
                "exportUndistortedImages": true
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "ExportDistortion_1": {
            "nodeType": "ExportDistortion",
            "position": [
                1800,
                0
            ],
            "inputs": {
                "input": "{ConvertDistortion_1.output}",
                "exportLensGridsUndistorted": false
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "FeatureExtraction_1": {
            "nodeType": "FeatureExtraction",
            "position": [
                200,
                0
            ],
            "inputs": {
                "input": "{ImageSegmentationPrompt_1.input}",
                "masksFolder": "{ImageSegmentationPrompt_1.output}"
            },
            "internalInputs": {
                "color": "#80766f"
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
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
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
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "ImageSegmentationPrompt_1": {
            "nodeType": "ImageSegmentationPrompt",
            "position": [
                0,
                0
            ],
            "inputs": {
                "input": "{CameraInit_1.output}",
                "maskInvert": true,
                "keepFilename": true
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "NodalSfM_1": {
            "nodeType": "NodalSfM",
            "position": [
                1200,
                0
            ],
            "inputs": {
                "input": "{RelativePoseEstimating_1.input}",
                "tracksFilename": "{RelativePoseEstimating_1.tracksFilename}",
                "pairs": "{RelativePoseEstimating_1.output}"
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "Publish_1": {
            "nodeType": "Publish",
            "position": [
                2000,
                0
            ],
            "inputs": {
                "inputFiles": [
                    "{ExportAnimatedCamera_1.output}",
                    "{ScenePreview_1.output}",
                    "{ExportDistortion_1.output}"
                ]
            }
        },
        "RelativePoseEstimating_1": {
            "nodeType": "RelativePoseEstimating",
            "position": [
                1000,
                0
            ],
            "inputs": {
                "input": "{TracksBuilding_1.input}",
                "tracksFilename": "{TracksBuilding_1.output}",
                "enforcePureRotation": true
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "ScenePreview_1": {
            "nodeType": "ScenePreview",
            "position": [
                1600,
                200
            ],
            "inputs": {
                "cameras": "{ConvertSfMFormat_1.output}",
                "model": "{NodalSfM_1.output}",
                "undistortedImages": "{ExportAnimatedCamera_1.outputUndistorted}",
                "masks": "{ImageSegmentationPrompt_1.output}",
                "pointCloudParams": {
                    "particleSize": 0.001,
                    "particleColor": "Red"
                }
            },
            "internalInputs": {
                "color": "#4c594c"
            }
        },
        "TracksBuilding_1": {
            "nodeType": "TracksBuilding",
            "position": [
                800,
                0
            ],
            "inputs": {
                "input": "{FeatureMatching_1.input}",
                "featuresFolders": "{FeatureMatching_1.featuresFolders}",
                "matchesFolders": [
                    "{FeatureMatching_1.output}"
                ]
            },
            "internalInputs": {
                "color": "#80766f"
            }
        }
    }
}