{
    "header": {
        "pipelineVersion": "2.2",
        "releaseVersion": "2025.1.0-develop",
        "fileVersion": "2.0",
        "template": true,
        "nodesVersions": {
            "CameraInit": "12.0",
            "DepthMap": "5.0",
            "DepthMapFilter": "4.0",
            "FeatureExtraction": "1.3",
            "FeatureMatching": "2.0",
            "ImageMatching": "2.0",
            "LightingCalibration": "1.0",
            "MeshFiltering": "3.0",
            "Meshing": "7.0",
            "PhotometricStereo": "1.0",
            "PrepareDenseScene": "3.1",
            "SfMFilter": "1.0",
            "SfMTransfer": "2.1",
            "SphereDetection": "1.0",
            "StructureFromMotion": "3.3",
            "Texturing": "6.0"
        }
    },
    "graph": {
        "CameraInit_1": {
            "nodeType": "CameraInit",
            "position": [
                -400,
                200
            ],
            "inputs": {
                "rawColorInterpretation": "LibRawWhiteBalancing"
            }
        },
        "DepthMapFilter_1": {
            "nodeType": "DepthMapFilter",
            "position": [
                1200,
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
                1000,
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
                0,
                0
            ],
            "inputs": {
                "input": "{SfMFilter_1.outputSfMData_selected}"
            }
        },
        "FeatureMatching_1": {
            "nodeType": "FeatureMatching",
            "position": [
                400,
                0
            ],
            "inputs": {
                "input": "{ImageMatching_1.input}",
                "featuresFolders": "{ImageMatching_1.featuresFolders}",
                "imagePairsList": "{ImageMatching_1.output}",
                "describerTypes": "{FeatureExtraction_1.describerTypes}",
                "maxIteration": 2048
            }
        },
        "ImageMatching_1": {
            "nodeType": "ImageMatching",
            "position": [
                200,
                0
            ],
            "inputs": {
                "input": "{FeatureExtraction_1.input}",
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ]
            }
        },
        "LightingCalibration_1": {
            "nodeType": "LightingCalibration",
            "position": [
                1200,
                200
            ],
            "inputs": {
                "inputPath": "{SphereDetection_1.input}",
                "inputDetection": "{SphereDetection_1.output}"
            }
        },
        "MeshFiltering_1": {
            "nodeType": "MeshFiltering",
            "position": [
                1600,
                0
            ],
            "inputs": {
                "inputMesh": "{Meshing_1.outputMesh}"
            }
        },
        "Meshing_1": {
            "nodeType": "Meshing",
            "position": [
                1400,
                0
            ],
            "inputs": {
                "input": "{DepthMapFilter_1.input}",
                "depthMapsFolder": "{DepthMapFilter_1.output}"
            }
        },
        "PhotometricStereo_1": {
            "nodeType": "PhotometricStereo",
            "position": [
                1400,
                200
            ],
            "inputs": {
                "inputPath": "{LightingCalibration_1.inputPath}",
                "pathToJSONLightFile": "{LightingCalibration_1.outputFile}"
            }
        },
        "PrepareDenseScene_1": {
            "nodeType": "PrepareDenseScene",
            "position": [
                800,
                0
            ],
            "inputs": {
                "input": "{StructureFromMotion_1.output}"
            }
        },
        "PrepareDenseScene_2": {
            "nodeType": "PrepareDenseScene",
            "position": [
                2200,
                200
            ],
            "inputs": {
                "input": "{PhotometricStereo_1.outputSfmDataAlbedo}"
            }
        },
        "PrepareDenseScene_3": {
            "nodeType": "PrepareDenseScene",
            "position": [
                2200,
                400
            ],
            "inputs": {
                "input": "{PhotometricStereo_1.outputSfmDataNormal}"
            }
        },
        "PrepareDenseScene_4": {
            "nodeType": "PrepareDenseScene",
            "position": [
                2200,
                600
            ],
            "inputs": {
                "input": "{PhotometricStereo_1.outputSfmDataNormalPNG}"
            }
        },
        "SfMFilter_1": {
            "nodeType": "SfMFilter",
            "position": [
                -200,
                200
            ],
            "inputs": {
                "inputFile": "{CameraInit_1.output}",
                "fileMatchingPattern": ".*/.*ambiant.*"
            }
        },
        "SfMTransfer_1": {
            "nodeType": "SfMTransfer",
            "position": [
                800,
                200
            ],
            "inputs": {
                "input": "{SfMFilter_1.outputSfMData_unselected}",
                "reference": "{StructureFromMotion_1.output}",
                "method": "from_poseid"
            }
        },
        "SphereDetection_1": {
            "nodeType": "SphereDetection",
            "position": [
                1000,
                200
            ],
            "inputs": {
                "input": "{SfMTransfer_1.output}"
            }
        },
        "StructureFromMotion_1": {
            "nodeType": "StructureFromMotion",
            "position": [
                600,
                0
            ],
            "inputs": {
                "input": "{FeatureMatching_1.input}",
                "featuresFolders": "{FeatureMatching_1.featuresFolders}",
                "matchesFolders": [
                    "{FeatureMatching_1.output}"
                ],
                "describerTypes": "{FeatureMatching_1.describerTypes}",
                "localizerEstimatorMaxIterations": 4096
            }
        },
        "Texturing_1": {
            "nodeType": "Texturing",
            "position": [
                1800,
                0
            ],
            "inputs": {
                "input": "{Meshing_1.output}",
                "imagesFolder": "{DepthMap_1.imagesFolder}",
                "inputMesh": "{MeshFiltering_1.outputMesh}"
            }
        },
        "Texturing_2": {
            "nodeType": "Texturing",
            "position": [
                2400,
                200
            ],
            "inputs": {
                "input": "{Meshing_1.output}",
                "imagesFolder": "{PrepareDenseScene_2.output}",
                "inputMesh": "{MeshFiltering_1.outputMesh}"
            }
        },
        "Texturing_3": {
            "nodeType": "Texturing",
            "position": [
                2400,
                400
            ],
            "inputs": {
                "input": "{Meshing_1.output}",
                "imagesFolder": "{PrepareDenseScene_3.output}",
                "inputMesh": "{MeshFiltering_1.outputMesh}"
            }
        },
        "Texturing_4": {
            "nodeType": "Texturing",
            "position": [
                2400,
                600
            ],
            "inputs": {
                "input": "{Meshing_1.output}",
                "imagesFolder": "{PrepareDenseScene_4.output}",
                "inputMesh": "{MeshFiltering_1.outputMesh}"
            }
        }
    }
}