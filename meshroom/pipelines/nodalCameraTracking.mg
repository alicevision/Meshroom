{
    "header": {
        "pipelineVersion": "2.2",
        "releaseVersion": "2024.1.0-develop",
        "fileVersion": "1.1",
        "template": true,
        "nodesVersions": {
            "DistortionCalibration": "3.0",
            "FeatureExtraction": "1.3",
            "ScenePreview": "2.0",
            "FeatureMatching": "2.0",
            "RelativePoseEstimating": "1.0",
            "ExportAnimatedCamera": "2.0",
            "ConvertSfMFormat": "2.0",
            "ImageSegmentation": "1.2",
            "NodalSfM": "1.0",
            "ExportDistortion": "1.0",
            "CameraInit": "9.0",
            "CheckerboardDetection": "1.0",
            "ImageMatching": "2.0",
            "TracksBuilding": "1.0",
            "ApplyCalibration": "1.0",
            "Publish": "1.3"
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
                "input": "{ApplyCalibration_1.output}",
                "masksFolder": "{ImageSegmentation_1.output}"
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
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
        },
        "RelativePoseEstimating_1": {
            "nodeType": "RelativePoseEstimating",
            "position": [
                1000,
                0
            ],
            "inputs": {
                "input": "{TracksBuilding_1.input}",
                "featuresFolders": "{TracksBuilding_1.featuresFolders}",
                "tracksFilename": "{TracksBuilding_1.output}",
                "enforcePureRotation": true
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
                "featuresFolders": "{RelativePoseEstimating_1.featuresFolders}",
                "tracksFilename": "{RelativePoseEstimating_1.tracksFilename}",
                "pairs": "{RelativePoseEstimating_1.output}"
            },
            "internalInputs": {
                "color": "#80766f"
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
                "useMasks": false,
                "masks": "{ImageSegmentation_1.output}",
                "pointCloudParams": {
                    "particleSize": 0.001,
                    "particleColor": "Red"
                }
            },
            "internalInputs": {
                "color": "#4c594c"
            }
        },
        "Publish_1": {
            "nodeType": "Publish",
            "position": [
                1800,
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
        "ImageSegmentation_1": {
            "nodeType": "ImageSegmentation",
            "position": [
                0,
                200
            ],
            "inputs": {
                "input": "{CameraInit_1.output}",
                "maskInvert": true
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "CheckerboardDetection_1": {
            "nodeType": "CheckerboardDetection",
            "position": [
                -400,
                -160
            ],
            "inputs": {
                "input": "{CameraInit_2.output}",
                "useNestedGrids": true,
                "exportDebugImages": true
            },
            "internalInputs": {
                "color": "#302e2e"
            }
        },
        "DistortionCalibration_1": {
            "nodeType": "DistortionCalibration",
            "position": [
                -200,
                -160
            ],
            "inputs": {
                "input": "{CheckerboardDetection_1.input}",
                "checkerboards": "{CheckerboardDetection_1.output}"
            },
            "internalInputs": {
                "color": "#302e2e"
            }
        },
        "ExportDistortion_1": {
            "nodeType": "ExportDistortion",
            "position": [
                0,
                -160
            ],
            "inputs": {
                "input": "{DistortionCalibration_1.output}"
            },
            "internalInputs": {
                "color": "#302e2e"
            }
        },
        "ApplyCalibration_1": {
            "nodeType": "ApplyCalibration",
            "position": [
                0,
                0
            ],
            "inputs": {
                "input": "{CameraInit_1.output}",
                "calibration": "{DistortionCalibration_1.output}"
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "CameraInit_2": {
            "nodeType": "CameraInit",
            "position": [
                -600,
                -160
            ],
            "inputs": {},
            "internalInputs": {
                "label": "CameraInitLensGrid",
                "color": "#302e2e"
            }
        }
    }
}