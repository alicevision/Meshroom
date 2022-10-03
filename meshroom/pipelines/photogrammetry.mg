{
    "header": {
        "pipelineVersion": "2.2", 
        "releaseVersion": "2021.1.0", 
        "fileVersion": "1.1", 
        "template": true, 
        "nodesVersions": {
            "FeatureMatching": "2.0", 
            "MeshFiltering": "3.0", 
            "Texturing": "6.0", 
            "PrepareDenseScene": "3.0", 
            "DepthMap": "2.0", 
            "StructureFromMotion": "2.0", 
            "CameraInit": "8.0", 
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "Meshing": "7.0", 
            "DepthMapFilter": "3.0"
        }
    }, 
    "graph": {
        "Texturing_1": {
            "inputs": {
                "imagesFolder": "{DepthMap_1.imagesFolder}", 
                "input": "{Meshing_1.output}", 
                "inputMesh": "{MeshFiltering_1.outputMesh}"
            }, 
            "nodeType": "Texturing", 
            "uids": {
                "0": "a7508a27971a36b86401f0476f64287476069faa"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 1
            }, 
            "outputs": {
                "outputTextures": "{cache}/{nodeType}/{uid0}/texture_*.exr", 
                "outputMesh": "{cache}/{nodeType}/{uid0}/texturedMesh.{outputMeshFileTypeValue}", 
                "outputMaterial": "{cache}/{nodeType}/{uid0}/texturedMesh.mtl", 
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                2000, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "Meshing_1": {
            "inputs": {
                "depthMapsFolder": "{DepthMapFilter_1.output}", 
                "input": "{DepthMapFilter_1.input}"
            }, 
            "nodeType": "Meshing", 
            "uids": {
                "0": "a520c188f5e02d00b841b1a376de78a252c79c24"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 1
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/densePointCloud.abc", 
                "outputMesh": "{cache}/{nodeType}/{uid0}/mesh.{outputMeshFileTypeValue}"
            }, 
            "position": [
                1600, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "DepthMapFilter_1": {
            "inputs": {
                "depthMapsFolder": "{DepthMap_1.output}", 
                "input": "{DepthMap_1.input}"
            }, 
            "nodeType": "DepthMapFilter", 
            "uids": {
                "0": "9d7527658e450be51a2fffb3923fd3d24b2b928c"
            }, 
            "parallelization": {
                "blockSize": 10, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                1400, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "ImageMatching_1": {
            "inputs": {
                "input": "{FeatureExtraction_1.input}", 
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ]
            }, 
            "nodeType": "ImageMatching", 
            "uids": {
                "0": "46fb9072ac753d60bec7dda9c8674b0568506ddf"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/imageMatches.txt"
            }, 
            "position": [
                400, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "FeatureExtraction_1": {
            "inputs": {
                "input": "{CameraInit_1.output}"
            }, 
            "nodeType": "FeatureExtraction", 
            "uids": {
                "0": "a07fb8d05b63327d05461954c2fd2a00f201275b"
            }, 
            "parallelization": {
                "blockSize": 40, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                200, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
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
            "uids": {
                "0": "5af4f4052aa22b0450708941b40928d46170f364"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/sfm.abc", 
                "extraInfoFolder": "{cache}/{nodeType}/{uid0}/", 
                "outputViewsAndPoses": "{cache}/{nodeType}/{uid0}/cameras.sfm"
            }, 
            "position": [
                800, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "PrepareDenseScene_1": {
            "inputs": {
                "input": "{StructureFromMotion_1.output}"
            }, 
            "nodeType": "PrepareDenseScene", 
            "uids": {
                "0": "489beb05de9e2d5cdfac149936b8c30c691f4b67"
            }, 
            "parallelization": {
                "blockSize": 40, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/", 
                "outputUndistorted": "{cache}/{nodeType}/{uid0}/*.{outputFileTypeValue}"
            }, 
            "position": [
                1000, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "CameraInit_1": {
            "inputs": {}, 
            "nodeType": "CameraInit", 
            "uids": {
                "0": "f9436e97e444fa71a05aa5cf7639b206df8ba282"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/cameraInit.sfm"
            }, 
            "position": [
                0, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "DepthMap_1": {
            "inputs": {
                "imagesFolder": "{PrepareDenseScene_1.output}", 
                "input": "{PrepareDenseScene_1.input}"
            }, 
            "nodeType": "DepthMap", 
            "uids": {
                "0": "279cdf5aa186d06aa81d952999991df43f3299f8"
            }, 
            "parallelization": {
                "blockSize": 3, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                1200, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "MeshFiltering_1": {
            "inputs": {
                "inputMesh": "{Meshing_1.outputMesh}"
            }, 
            "nodeType": "MeshFiltering", 
            "uids": {
                "0": "590f12b2789757dcbe3bfd3e5b50e28d73a4e060"
            }, 
            "parallelization": {
                "blockSize": 0, 
                "split": 1, 
                "size": 1
            }, 
            "outputs": {
                "outputMesh": "{cache}/{nodeType}/{uid0}/mesh.{outputMeshFileTypeValue}"
            }, 
            "position": [
                1800, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }, 
        "FeatureMatching_1": {
            "inputs": {
                "describerTypes": "{FeatureExtraction_1.describerTypes}", 
                "imagePairsList": "{ImageMatching_1.output}", 
                "input": "{ImageMatching_1.input}", 
                "featuresFolders": "{ImageMatching_1.featuresFolders}"
            }, 
            "nodeType": "FeatureMatching", 
            "uids": {
                "0": "534c5224ba51c770ae3793cc085ae3aaa8c2c415"
            }, 
            "parallelization": {
                "blockSize": 20, 
                "split": 0, 
                "size": 0
            }, 
            "outputs": {
                "output": "{cache}/{nodeType}/{uid0}/"
            }, 
            "position": [
                600, 
                0
            ], 
            "internalFolder": "{cache}/{nodeType}/{uid0}/"
        }
    }
}