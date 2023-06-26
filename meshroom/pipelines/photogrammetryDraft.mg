{
    "header": {
        "nodesVersions": {
            "Meshing": "7.0",
            "FeatureExtraction": "1.2",
            "CameraInit": "9.0",
            "FeatureMatching": "2.0",
            "MeshFiltering": "3.0",
            "Texturing": "6.0",
            "StructureFromMotion": "3.1",
            "ImageMatching": "2.0",
            "Publish": "1.3"
        },
        "releaseVersion": "2023.2.0",
        "fileVersion": "1.1",
        "template": true
    },
    "graph": {
        "Texturing_1": {
            "nodeType": "Texturing",
            "position": [
                1400,
                0
            ],
            "inputs": {
                "input": "{Meshing_1.output}",
                "inputMesh": "{MeshFiltering_1.outputMesh}"
            }
        },
        "Meshing_1": {
            "nodeType": "Meshing",
            "position": [
                1000,
                0
            ],
            "inputs": {
                "input": "{StructureFromMotion_1.output}"
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
        "CameraInit_1": {
            "nodeType": "CameraInit",
            "position": [
                0,
                0
            ],
            "inputs": {}
        },
        "MeshFiltering_1": {
            "nodeType": "MeshFiltering",
            "position": [
                1200,
                0
            ],
            "inputs": {
                "inputMesh": "{Meshing_1.outputMesh}"
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
                1600,
                0
            ],
            "inputs": {
                "inputFiles": [
                    "{Texturing_1.outputMesh}",
                    "{Texturing_1.outputMaterial}",
                    "{Texturing_1.outputTextures}"
                ]
            }
        }
    }
}