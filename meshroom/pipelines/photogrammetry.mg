{
    "header": {
        "pipelineVersion": "2.2", 
        "releaseVersion": "2023.1.0",
        "fileVersion": "1.1", 
        "template": true, 
        "nodesVersions": {
            "FeatureMatching": "2.0", 
            "MeshFiltering": "3.0", 
            "Texturing": "6.0", 
            "PrepareDenseScene": "3.0", 
            "DepthMap": "3.0", 
            "StructureFromMotion": "3.0",
            "CameraInit": "9.0", 
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "Meshing": "7.0", 
            "DepthMapFilter": "3.0",
            "Publish": "1.3"
        }
    }, 
    "graph": {
        "Publish_1": {
            "inputs": {
                "output": "",
                "inputFiles": [
                    "{Texturing_1.outputMesh}",
                    "{Texturing_1.outputMaterial}",
                    "{Texturing_1.outputTextures}"
                ]
            }, 
            "nodeType": "Publish", 
            "position": [
                2200, 
                0
            ]
        },
        "Texturing_1": {
            "inputs": {
                "imagesFolder": "{DepthMap_1.imagesFolder}", 
                "input": "{Meshing_1.output}", 
                "inputMesh": "{MeshFiltering_1.outputMesh}"
            }, 
            "nodeType": "Texturing", 
            "position": [
                2000, 
                0
            ]
        }, 
        "Meshing_1": {
            "inputs": {
                "depthMapsFolder": "{DepthMapFilter_1.output}", 
                "input": "{DepthMapFilter_1.input}"
            }, 
            "nodeType": "Meshing", 
            "position": [
                1600, 
                0
            ]
        }, 
        "DepthMapFilter_1": {
            "inputs": {
                "depthMapsFolder": "{DepthMap_1.output}", 
                "input": "{DepthMap_1.input}"
            }, 
            "nodeType": "DepthMapFilter", 
            "position": [
                1400, 
                0
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
        "PrepareDenseScene_1": {
            "inputs": {
                "input": "{StructureFromMotion_1.output}"
            }, 
            "nodeType": "PrepareDenseScene", 
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
        "DepthMap_1": {
            "inputs": {
                "imagesFolder": "{PrepareDenseScene_1.output}", 
                "input": "{PrepareDenseScene_1.input}"
            }, 
            "nodeType": "DepthMap", 
            "position": [
                1200, 
                0
            ]
        }, 
        "MeshFiltering_1": {
            "inputs": {
                "inputMesh": "{Meshing_1.outputMesh}"
            }, 
            "nodeType": "MeshFiltering", 
            "position": [
                1800, 
                0
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
        }
    }
}
