{
    "header": {
        "releaseVersion": "2025.1.0-develop",
        "fileVersion": "2.0",
        "nodesVersions": {
            "ApplyCalibration": "1.0",
            "CameraInit": "12.0",
            "ConvertDistortion": "1.0",
            "ConvertSfMFormat": "2.0",
            "DepthMap": "5.0",
            "DepthMapFilter": "4.0",
            "ExportAnimatedCamera": "2.0",
            "ExportDistortion": "2.0",
            "FeatureExtraction": "1.3",
            "FeatureMatching": "2.0",
            "ImageDetectionPrompt": "0.1",
            "ImageMatching": "2.0",
            "ImageMatchingMultiSfM": "1.0",
            "ImageSegmentationBox": "0.1",
            "KeyframeSelection": "5.0",
            "MeshDecimate": "1.0",
            "MeshFiltering": "3.0",
            "Meshing": "7.0",
            "PrepareDenseScene": "3.1",
            "Publish": "1.3",
            "RelativePoseEstimating": "3.0",
            "ScenePreview": "2.0",
            "SfMBootStraping": "3.0",
            "SfMExpanding": "2.0",
            "SfMTransfer": "2.1",
            "SfMTriangulation": "1.0",
            "Texturing": "6.0",
            "TracksBuilding": "1.0"
        },
        "template": true
    },
    "graph": {
        "ApplyCalibration_1": {
            "nodeType": "ApplyCalibration",
            "position": [
                0,
                0
            ],
            "inputs": {
                "input": "{CameraInit_1.output}"
            },
            "internalInputs": {
                "color": "#575963"
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
                "color": "#575963"
            }
        },
        "ConvertDistortion_1": {
            "nodeType": "ConvertDistortion",
            "position": [
                2400,
                360
            ],
            "inputs": {
                "input": "{SfMExpanding_2.output}"
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "ConvertSfMFormat_1": {
            "nodeType": "ConvertSfMFormat",
            "position": [
                3800,
                200
            ],
            "inputs": {
                "input": "{ExportAnimatedCamera_1.input}",
                "fileExt": "json",
                "describerTypes": "{TracksBuilding_2.describerTypes}",
                "structure": false,
                "observations": false
            },
            "internalInputs": {
                "color": "#4c594c"
            }
        },
        "DepthMapFilter_1": {
            "nodeType": "DepthMapFilter",
            "position": [
                3200,
                0
            ],
            "inputs": {
                "input": "{DepthMap_1.input}",
                "depthMapsFolder": "{DepthMap_1.output}"
            },
            "internalInputs": {
                "color": "#3f3138"
            }
        },
        "DepthMap_1": {
            "nodeType": "DepthMap",
            "position": [
                3000,
                0
            ],
            "inputs": {
                "input": "{PrepareDenseScene_1.input}",
                "imagesFolder": "{PrepareDenseScene_1.output}",
                "downscale": 1
            },
            "internalInputs": {
                "color": "#3f3138"
            }
        },
        "ExportAnimatedCamera_1": {
            "nodeType": "ExportAnimatedCamera",
            "position": [
                2600,
                200
            ],
            "inputs": {
                "input": "{SfMExpanding_2.output}",
                "exportUndistortedImages": true
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "ExportDistortion_1": {
            "nodeType": "ExportDistortion",
            "position": [
                2600,
                360
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
                400,
                200
            ],
            "inputs": {
                "input": "{ApplyCalibration_1.output}",
                "masksFolder": "{ImageSegmentationBox_1.output}",
                "maskExtension": "exr"
            },
            "internalInputs": {
                "color": "#575963"
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
                "label": "FeatureMatchingKeyframes",
                "color": "#575963"
            }
        },
        "FeatureMatching_2": {
            "nodeType": "FeatureMatching",
            "position": [
                1800,
                360
            ],
            "inputs": {
                "input": "{ImageMatching_2.input}",
                "featuresFolders": "{ImageMatching_2.featuresFolders}",
                "imagePairsList": "{ImageMatching_2.output}"
            },
            "internalInputs": {
                "label": "FeatureMatchingAllFrames",
                "color": "#80766f"
            }
        },
        "FeatureMatching_3": {
            "nodeType": "FeatureMatching",
            "position": [
                1800,
                200
            ],
            "inputs": {
                "input": "{ImageMatchingMultiSfM_1.outputCombinedSfM}",
                "featuresFolders": "{ImageMatchingMultiSfM_1.featuresFolders}",
                "imagePairsList": "{ImageMatchingMultiSfM_1.output}",
                "describerTypes": "{FeatureExtraction_1.describerTypes}"
            },
            "internalInputs": {
                "label": "FeatureMatchingFramesToKeyframes",
                "color": "#80766f"
            }
        },
        "ImageDetectionPrompt_1": {
            "nodeType": "ImageDetectionPrompt",
            "position": [
                0,
                200
            ],
            "inputs": {
                "input": "{CameraInit_1.output}"
            },
            "internalInputs": {
                "color": "#575963"
            }
        },
        "ImageMatchingMultiSfM_1": {
            "nodeType": "ImageMatchingMultiSfM",
            "position": [
                1600,
                200
            ],
            "inputs": {
                "input": "{KeyframeSelection_1.outputSfMDataFrames}",
                "inputB": "{SfMExpanding_1.output}",
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ],
                "method": "VocabularyTree",
                "matchingMode": "a/b",
                "nbMatches": 20
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
                "input": "{KeyframeSelection_1.outputSfMDataKeyframes}",
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ],
                "method": "Exhaustive"
            },
            "internalInputs": {
                "label": "ImageMatchingKeyframes",
                "color": "#575963"
            }
        },
        "ImageMatching_2": {
            "nodeType": "ImageMatching",
            "position": [
                1600,
                360
            ],
            "inputs": {
                "input": "{ApplyCalibration_1.output}",
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ],
                "method": "Sequential",
                "nbNeighbors": 20
            },
            "internalInputs": {
                "color": "#80766f"
            }
        },
        "ImageSegmentationBox_1": {
            "nodeType": "ImageSegmentationBox",
            "position": [
                200,
                200
            ],
            "inputs": {
                "input": "{ImageDetectionPrompt_1.input}",
                "bboxFolder": "{ImageDetectionPrompt_1.output}",
                "maskInvert": true,
                "keepFilename": true
            },
            "internalInputs": {
                "color": "#575963"
            }
        },
        "KeyframeSelection_1": {
            "nodeType": "KeyframeSelection",
            "position": [
                200,
                0
            ],
            "inputs": {
                "inputPaths": [
                    "{ApplyCalibration_1.output}"
                ]
            },
            "internalInputs": {
                "color": "#575963"
            }
        },
        "MeshDecimate_1": {
            "nodeType": "MeshDecimate",
            "position": [
                3800,
                0
            ],
            "inputs": {
                "input": "{MeshFiltering_1.outputMesh}",
                "simplificationFactor": 0.05
            },
            "internalInputs": {
                "color": "#3f3138"
            }
        },
        "MeshFiltering_1": {
            "nodeType": "MeshFiltering",
            "position": [
                3600,
                0
            ],
            "inputs": {
                "inputMesh": "{Meshing_1.outputMesh}",
                "filterLargeTrianglesFactor": 10.0
            },
            "internalInputs": {
                "color": "#3f3138"
            }
        },
        "Meshing_1": {
            "nodeType": "Meshing",
            "position": [
                3400,
                0
            ],
            "inputs": {
                "input": "{DepthMapFilter_1.input}",
                "depthMapsFolder": "{DepthMapFilter_1.output}",
                "estimateSpaceFromSfM": false,
                "minStep": 1,
                "fullWeight": 10.0,
                "saveRawDensePointCloud": true
            },
            "internalInputs": {
                "color": "#3f3138"
            }
        },
        "PrepareDenseScene_1": {
            "nodeType": "PrepareDenseScene",
            "position": [
                2800,
                0
            ],
            "inputs": {
                "input": "{SfMTriangulation_1.output}",
                "maskExtension": "exr"
            },
            "internalInputs": {
                "color": "#3f3138"
            }
        },
        "Publish_1": {
            "nodeType": "Publish",
            "position": [
                4400,
                100
            ],
            "inputs": {
                "inputFiles": [
                    "{ExportAnimatedCamera_1.output}",
                    "{Texturing_1.output}",
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
                "countIterations": 50000,
                "minInliers": 100
            },
            "internalInputs": {
                "color": "#575963"
            }
        },
        "ScenePreview_1": {
            "nodeType": "ScenePreview",
            "position": [
                4000,
                200
            ],
            "inputs": {
                "cameras": "{ConvertSfMFormat_1.output}",
                "model": "{MeshDecimate_1.output}",
                "undistortedImages": "{ExportAnimatedCamera_1.outputUndistorted}",
                "masks": "{ImageSegmentationBox_1.output}"
            },
            "internalInputs": {
                "color": "#4c594c"
            }
        },
        "SfMBootStraping_1": {
            "nodeType": "SfMBootStraping",
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
                "color": "#575963"
            }
        },
        "SfMExpanding_1": {
            "nodeType": "SfMExpanding",
            "position": [
                1400,
                0
            ],
            "inputs": {
                "input": "{SfMBootStraping_1.output}",
                "tracksFilename": "{SfMBootStraping_1.tracksFilename}",
                "meshFilename": "{SfMBootStraping_1.meshFilename}",
                "minAngleForTriangulation": 1.0,
                "minAngleForLandmark": 0.5
            },
            "internalInputs": {
                "comment": "Estimate cameras parameters for the keyframes.",
                "label": "SfMExpandingKeys",
                "color": "#575963"
            }
        },
        "SfMExpanding_2": {
            "nodeType": "SfMExpanding",
            "position": [
                2200,
                200
            ],
            "inputs": {
                "input": "{TracksBuilding_2.input}",
                "tracksFilename": "{TracksBuilding_2.output}",
                "meshFilename": "{SfMExpanding_1.meshFilename}",
                "nbFirstUnstableCameras": 0,
                "maxImagesPerGroup": 0,
                "bundleAdjustmentMaxOutliers": 5000000,
                "minNumberOfObservationsForTriangulation": 3,
                "minAngleForTriangulation": 1.0,
                "minAngleForLandmark": 0.5
            },
            "internalInputs": {
                "comment": "Estimate cameras parameters for the complete camera tracking sequence.",
                "label": "SfMExpandingAll",
                "color": "#80766f"
            }
        },
        "SfMTransfer_1": {
            "nodeType": "SfMTransfer",
            "position": [
                2400,
                0
            ],
            "inputs": {
                "input": "{KeyframeSelection_1.outputSfMDataKeyframes}",
                "reference": "{SfMExpanding_2.output}",
                "transferLandmarks": false
            },
            "internalInputs": {
                "comment": "Transfer pose from final camera tracking into the keyframes-only scene.",
                "color": "#3f3138"
            }
        },
        "SfMTriangulation_1": {
            "nodeType": "SfMTriangulation",
            "position": [
                2600,
                0
            ],
            "inputs": {
                "input": "{SfMTransfer_1.output}",
                "featuresFolders": "{TracksBuilding_1.featuresFolders}",
                "matchesFolders": "{TracksBuilding_1.matchesFolders}",
                "minAngleForTriangulation": 1.0,
                "minAngleForLandmark": 0.5
            },
            "internalInputs": {
                "color": "#3f3138"
            }
        },
        "Texturing_1": {
            "nodeType": "Texturing",
            "position": [
                4000,
                0
            ],
            "inputs": {
                "input": "{Meshing_1.output}",
                "imagesFolder": "{PrepareDenseScene_1.output}",
                "inputMesh": "{MeshDecimate_1.output}"
            },
            "internalInputs": {
                "color": "#3f3138"
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
                ],
                "describerTypes": "{FeatureMatching_1.describerTypes}",
                "filterTrackForks": true
            },
            "internalInputs": {
                "color": "#575963"
            }
        },
        "TracksBuilding_2": {
            "nodeType": "TracksBuilding",
            "position": [
                2000,
                200
            ],
            "inputs": {
                "input": "{FeatureMatching_3.input}",
                "featuresFolders": "{FeatureMatching_3.featuresFolders}",
                "matchesFolders": [
                    "{FeatureMatching_2.output}",
                    "{FeatureMatching_3.output}"
                ],
                "describerTypes": "{FeatureMatching_3.describerTypes}",
                "minInputTrackLength": 5,
                "filterTrackForks": true
            },
            "internalInputs": {
                "color": "#80766f"
            }
        }
    }
}