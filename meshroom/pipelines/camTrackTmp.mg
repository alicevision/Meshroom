{
    "header": {
        "pipelineVersion": "2.2",
        "releaseVersion": "2023.2.0-develop",
        "fileVersion": "1.1",
        "template": true,
        "nodesVersions": {
            "SfMTriangulation": "1.0",
            "Publish": "1.2",
            "Texturing": "6.0",
            "MeshFiltering": "3.0",
            "SfMTransfer": "2.1",
            "ApplyCalibration": "1.0",
            "ScenePreview": "1.0",
            "CheckerboardDetection": "1.0",
            "ImageMatchingMultiSfM": "1.0",
            "Meshing": "7.0",
            "ExportDistortion": "1.0",
            "StructureFromMotion": "3.1",
            "ExportAnimatedCamera": "2.0",
            "MeshDecimate": "1.0",
            "ConvertSfMFormat": "2.0",
            "FeatureMatching": "2.0",
            "ImageMatching": "2.0",
            "PrepareDenseScene": "3.0",
            "KeyframeSelection": "4.0",
            "FeatureExtraction": "1.1",
            "CameraInit": "9.0",
            "DepthMap": "3.0",
            "DepthMapFilter": "3.0",
            "DistortionCalibration": "3.0"
        }
    },
    "graph": {
        "CameraInit_1": {
            "nodeType": "CameraInit",
            "position": [
                -213,
                -2
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
                200,
                0
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
                1000,
                0
            ],
            "inputs": {
                "input": "{KeyframeSelection_1.outputSfMDataFrames}",
                "inputB": "{StructureFromMotion_1.output}",
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
            }
        },
        "KeyframeSelection_1": {
            "nodeType": "KeyframeSelection",
            "position": [
                200,
                160
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
                "inputMesh": "{Meshing_2.outputMesh}",
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
                "reference": "{StructureFromMotion_2.output}"
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
                "featuresFolders": "{StructureFromMotion_1.featuresFolders}",
                "matchesFolders": "{StructureFromMotion_1.matchesFolders}"
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
        "Texturing_1": {
            "nodeType": "Texturing",
            "position": [
                3200,
                0
            ],
            "inputs": {
                "input": "{Meshing_2.output}",
                "imagesFolder": "{PrepareDenseScene_1.output}",
                "inputMesh": "{MeshDecimate_1.output}"
            }
        },
        "Publish_1": {
            "nodeType": "Publish",
            "position": [
                1800,
                160
            ],
            "inputs": {
                "inputFiles": [
                    "{ExportAnimatedCamera_1.output}"
                ]
            }
        },
        "ExportAnimatedCamera_1": {
            "nodeType": "ExportAnimatedCamera",
            "position": [
                1600,
                160
            ],
            "inputs": {
                "input": "{StructureFromMotion_2.output}"
            }
        },
        "FeatureMatching_2": {
            "nodeType": "FeatureMatching",
            "position": [
                600,
                160
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
                400,
                160
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
        "Meshing_2": {
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
        "StructureFromMotion_2": {
            "nodeType": "StructureFromMotion",
            "position": [
                1400,
                0
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
            }
        },
        "FeatureMatching_3": {
            "nodeType": "FeatureMatching",
            "position": [
                1200,
                0
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
        },
        "CameraInit_2": {
            "nodeType": "CameraInit",
            "position": [
                -633,
                -130
            ],
            "inputs": {}
        },
        "CheckerboardDetection_1": {
            "nodeType": "CheckerboardDetection",
            "position": [
                -431,
                -131
            ],
            "inputs": {
                "input": "{CameraInit_2.output}",
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
                3200,
                274
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
                3001,
                275
            ],
            "inputs": {
                "input": "{ExportAnimatedCamera_1.input}",
                "fileExt": "json",
                "structure": false,
                "observations": false
            }
        }
    }
}