{
    "header": {
        "pipelineVersion": "2.2",
        "releaseVersion": "2023.2.0-develop",
        "fileVersion": "1.1",
        "template": true,
        "nodesVersions": {
            "FeatureExtraction": "1.1",
            "CameraInit": "9.0",
            "DepthMap": "3.0",
            "DepthMapFilter": "3.0",
            "DistortionCalibration": "3.0",
            "StructureFromMotion": "3.1",
            "PrepareDenseScene": "3.0",
            "Texturing": "6.0",
            "ExportDistortion": "1.0",
            "KeyframeSelection": "4.0",
            "ScenePreview": "1.0",
            "CheckerboardDetection": "1.0",
            "Meshing": "7.0",
            "ImageMatchingMultiSfM": "1.0",
            "MeshDecimate": "1.0",
            "Publish": "1.2",
            "MeshFiltering": "3.0",
            "ApplyCalibration": "1.0",
            "ExportAnimatedCamera": "2.0",
            "SfMTransfer": "2.1",
            "ConvertSfMFormat": "2.0",
            "FeatureMatching": "2.0",
            "ImageMatching": "2.0",
            "SfMTriangulation": "1.0"
        }
    },
    "graph": {
        "CameraInit_1": {
            "nodeType": "CameraInit",
            "position": [
                -215,
                15
            ],
            "inputs": {}
        },
        "DepthMapFilter_1": {
            "nodeType": "DepthMapFilter",
            "position": [
                2400,
                0
            ],
            "inputs": {
                "input": "{DepthMap_1.input}",
                "depthMapsFolder": "{DepthMap_1.output}"
            }
        },
        "DepthMap_1": {
            "nodeType": "DepthMap",
            "position": [
                2200,
                0
            ],
            "inputs": {
                "input": "{PrepareDenseScene_1.input}",
                "imagesFolder": "{PrepareDenseScene_1.output}"
            }
        },
        "FeatureExtraction_1": {
            "nodeType": "FeatureExtraction",
            "position": [
                197,
                227
            ],
            "inputs": {
                "input": "{ApplyCalibration_1.output}"
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
                "label": "FeatureMatchingKeyframes"
            }
        },
        "ImageMatchingMultiSfM_1": {
            "nodeType": "ImageMatchingMultiSfM",
            "position": [
                996,
                215
            ],
            "inputs": {
                "input": "{KeyframeSelection_1.outputSfMDataFrames}",
                "inputB": "{StructureFromMotion_2.output}",
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ],
                "method": "VocabularyTree",
                "matchingMode": "a/b",
                "nbMatches": 20
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
                "label": "ImageMatchingKeyframes"
            }
        },
        "KeyframeSelection_1": {
            "nodeType": "KeyframeSelection",
            "position": [
                197,
                3
            ],
            "inputs": {
                "inputPaths": [
                    "{ApplyCalibration_1.output}"
                ]
            }
        },
        "MeshDecimate_1": {
            "nodeType": "MeshDecimate",
            "position": [
                3000,
                0
            ],
            "inputs": {
                "input": "{MeshFiltering_1.outputMesh}",
                "simplificationFactor": 0.2
            }
        },
        "MeshFiltering_1": {
            "nodeType": "MeshFiltering",
            "position": [
                2800,
                0
            ],
            "inputs": {
                "inputMesh": "{Meshing_1.outputMesh}",
                "filterLargeTrianglesFactor": 10.0
            }
        },
        "PrepareDenseScene_1": {
            "nodeType": "PrepareDenseScene",
            "position": [
                2000,
                0
            ],
            "inputs": {
                "input": "{SfMTriangulation_1.output}"
            }
        },
        "SfMTransfer_1": {
            "nodeType": "SfMTransfer",
            "position": [
                1600,
                0
            ],
            "inputs": {
                "input": "{KeyframeSelection_1.outputSfMDataKeyframes}",
                "reference": "{StructureFromMotion_1.output}"
            },
            "internalInputs": {
                "comment": "Transfer pose from final camera tracking into the keyframes-only scene."
            }
        },
        "SfMTriangulation_1": {
            "nodeType": "SfMTriangulation",
            "position": [
                1800,
                0
            ],
            "inputs": {
                "input": "{SfMTransfer_1.output}",
                "featuresFolders": "{StructureFromMotion_2.featuresFolders}",
                "matchesFolders": "{StructureFromMotion_2.matchesFolders}"
            }
        },
        "Texturing_1": {
            "nodeType": "Texturing",
            "position": [
                3200,
                0
            ],
            "inputs": {
                "input": "{Meshing_1.output}",
                "imagesFolder": "{PrepareDenseScene_1.output}",
                "inputMesh": "{MeshDecimate_1.output}"
            }
        },
        "Publish_1": {
            "nodeType": "Publish",
            "position": [
                3574,
                166
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
        "ExportAnimatedCamera_1": {
            "nodeType": "ExportAnimatedCamera",
            "position": [
                1625,
                209
            ],
            "inputs": {
                "input": "{StructureFromMotion_1.output}"
            }
        },
        "Meshing_1": {
            "nodeType": "Meshing",
            "position": [
                2600,
                0
            ],
            "inputs": {
                "input": "{DepthMapFilter_1.input}",
                "depthMapsFolder": "{DepthMapFilter_1.output}",
                "estimateSpaceFromSfM": false,
                "minStep": 1,
                "fullWeight": 10.0,
                "saveRawDensePointCloud": true
            }
        },
        "CheckerboardDetection_1": {
            "nodeType": "CheckerboardDetection",
            "position": [
                -431,
                -131
            ],
            "inputs": {
                "input": "{CameraInit_2.output}",
                "useNestedGrids": true,
                "exportDebugImages": true
            }
        },
        "DistortionCalibration_1": {
            "nodeType": "DistortionCalibration",
            "position": [
                -216,
                -133
            ],
            "inputs": {
                "input": "{CheckerboardDetection_1.input}",
                "checkerboards": "{CheckerboardDetection_1.output}"
            }
        },
        "ExportDistortion_1": {
            "nodeType": "ExportDistortion",
            "position": [
                -13,
                -136
            ],
            "inputs": {
                "input": "{DistortionCalibration_1.output}"
            }
        },
        "ApplyCalibration_1": {
            "nodeType": "ApplyCalibration",
            "position": [
                -9,
                11
            ],
            "inputs": {
                "input": "{CameraInit_1.output}",
                "calibration": "{DistortionCalibration_1.output}"
            }
        },
        "ScenePreview_1": {
            "nodeType": "ScenePreview",
            "position": [
                3202,
                232
            ],
            "inputs": {
                "cameras": "{ConvertSfMFormat_1.output}",
                "model": "{MeshDecimate_1.output}",
                "undistortedImages": "{ExportAnimatedCamera_1.outputUndistorted}"
            }
        },
        "ConvertSfMFormat_1": {
            "nodeType": "ConvertSfMFormat",
            "position": [
                3006,
                233
            ],
            "inputs": {
                "input": "{ExportAnimatedCamera_1.input}",
                "fileExt": "json",
                "structure": false,
                "observations": false
            }
        },
        "StructureFromMotion_1": {
            "nodeType": "StructureFromMotion",
            "position": [
                1396,
                215
            ],
            "inputs": {
                "input": "{FeatureMatching_3.input}",
                "featuresFolders": "{FeatureMatching_3.featuresFolders}",
                "matchesFolders": [
                    "{FeatureMatching_3.output}",
                    "{FeatureMatching_2.output}"
                ],
                "describerTypes": "{FeatureMatching_3.describerTypes}",
                "minInputTrackLength": 5,
                "minNumberOfObservationsForTriangulation": 3,
                "minAngleForTriangulation": 1.0,
                "minAngleForLandmark": 0.5
            },
            "internalInputs": {
                "comment": "Estimate cameras parameters for the complete camera tracking sequence."
            }
        },
        "StructureFromMotion_2": {
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
            },
            "internalInputs": {
                "comment": "Solve all keyframes first.",
                "label": "StructureFromMotionKeyframes"
            }
        },
        "FeatureMatching_2": {
            "nodeType": "FeatureMatching",
            "position": [
                1198,
                396
            ],
            "inputs": {
                "input": "{ImageMatching_2.input}",
                "featuresFolders": "{ImageMatching_2.featuresFolders}",
                "imagePairsList": "{ImageMatching_2.output}"
            },
            "internalInputs": {
                "label": "FeatureMatchingAllFrames"
            }
        },
        "ImageMatching_2": {
            "nodeType": "ImageMatching",
            "position": [
                998,
                396
            ],
            "inputs": {
                "input": "{ApplyCalibration_1.output}",
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ],
                "method": "Sequential",
                "nbNeighbors": 20
            }
        },
        "CameraInit_2": {
            "nodeType": "CameraInit",
            "position": [
                -633,
                -130
            ],
            "inputs": {},
            "internalInputs": {
                "label": "CameraInitLensGrid"
            }
        },
        "FeatureMatching_3": {
            "nodeType": "FeatureMatching",
            "position": [
                1196,
                215
            ],
            "inputs": {
                "input": "{ImageMatchingMultiSfM_1.outputCombinedSfM}",
                "featuresFolders": "{ImageMatchingMultiSfM_1.featuresFolders}",
                "imagePairsList": "{ImageMatchingMultiSfM_1.output}",
                "describerTypes": "{FeatureExtraction_1.describerTypes}"
            },
            "internalInputs": {
                "label": "FeatureMatchingFramesToKeyframes"
            }
        }
    }
}