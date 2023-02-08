{
    "header": {
        "nodesVersions": {
            "PanoramaSeams": "2.0", 
            "FeatureMatching": "2.0", 
            "ImageProcessing": "3.0", 
            "PanoramaCompositing": "2.0", 
            "LdrToHdrMerge": "4.0", 
            "PanoramaEstimation": "1.0", 
            "LdrToHdrCalibration": "3.0", 
            "LdrToHdrSampling": "4.0", 
            "PanoramaInit": "2.0", 
            "CameraInit": "9.0", 
            "SfMTransform": "3.0", 
            "PanoramaMerging": "1.0", 
            "ImageMatching": "2.0", 
            "FeatureExtraction": "1.1", 
            "PanoramaPrepareImages": "1.1", 
            "PanoramaWarping": "1.0"
        }, 
        "releaseVersion": "2021.1.0", 
        "fileVersion": "1.1", 
        "template": true
    }, 
    "graph": {
        "LdrToHdrMerge_1": {
            "inputs": {
                "channelQuantizationPower": "{LdrToHdrCalibration_1.channelQuantizationPower}", 
                "byPass": "{LdrToHdrCalibration_1.byPass}", 
                "input": "{LdrToHdrCalibration_1.input}", 
                "userNbBrackets": "{LdrToHdrCalibration_1.userNbBrackets}", 
                "response": "{LdrToHdrCalibration_1.response}",
                "workingColorSpace": "{LdrToHdrCalibration_1.workingColorSpace}"
            }, 
            "nodeType": "LdrToHdrMerge", 
            "position": [
                800, 
                0
            ]
        }, 
        "ImageProcessing_1": {
            "inputs": {
                "extension": "exr", 
                "fillHoles": true, 
                "input": "{PanoramaMerging_1.outputPanorama}", 
                "fixNonFinite": true
            }, 
            "nodeType": "ImageProcessing", 
            "position": [
                3000, 
                0
            ]
        }, 
        "PanoramaWarping_1": {
            "inputs": {
                "input": "{SfMTransform_1.output}"
            }, 
            "nodeType": "PanoramaWarping", 
            "position": [
                2200, 
                0
            ]
        }, 
        "LdrToHdrCalibration_1": {
            "inputs": {
                "samples": "{LdrToHdrSampling_1.output}", 
                "channelQuantizationPower": "{LdrToHdrSampling_1.channelQuantizationPower}", 
                "byPass": "{LdrToHdrSampling_1.byPass}", 
                "input": "{LdrToHdrSampling_1.input}", 
                "userNbBrackets": "{LdrToHdrSampling_1.userNbBrackets}",
                "workingColorSpace": "{LdrToHdrSampling_1.workingColorSpace}"
            }, 
            "nodeType": "LdrToHdrCalibration", 
            "position": [
                600, 
                0
            ]
        }, 
        "LdrToHdrSampling_1": {
            "inputs": {
                "input": "{PanoramaPrepareImages_1.output}"
            }, 
            "nodeType": "LdrToHdrSampling", 
            "position": [
                400, 
                0
            ]
        }, 
        "ImageMatching_1": {
            "inputs": {
                "input": "{PanoramaInit_1.outSfMData}", 
                "method": "FrustumOrVocabularyTree", 
                "featuresFolders": [
                    "{FeatureExtraction_1.output}"
                ]
            }, 
            "nodeType": "ImageMatching", 
            "position": [
                1400, 
                0
            ]
        }, 
        "FeatureExtraction_1": {
            "inputs": {
                "describerQuality": "high", 
                "input": "{LdrToHdrMerge_1.outSfMData}"
            }, 
            "nodeType": "FeatureExtraction", 
            "position": [
                1000, 
                0
            ]
        }, 
        "PanoramaSeams_1": {
            "inputs": {
                "input": "{PanoramaWarping_1.input}", 
                "warpingFolder": "{PanoramaWarping_1.output}"
            }, 
            "nodeType": "PanoramaSeams", 
            "position": [
                2400, 
                0
            ]
        }, 
        "PanoramaCompositing_1": {
            "inputs": {
                "warpingFolder": "{PanoramaSeams_1.warpingFolder}", 
                "labels": "{PanoramaSeams_1.output}", 
                "input": "{PanoramaSeams_1.input}"
            }, 
            "nodeType": "PanoramaCompositing", 
            "position": [
                2600, 
                0
            ]
        }, 
        "CameraInit_1": {
            "inputs": {
                "allowedCameraModels": [
                    "pinhole", 
                    "radial1", 
                    "radial3", 
                    "brown", 
                    "fisheye1", 
                    "3deanamorphic4", 
                    "3deradial4", 
                    "3declassicld"
                ]
            }, 
            "nodeType": "CameraInit", 
            "position": [
                0, 
                0
            ]
        }, 
        "PanoramaPrepareImages_1": {
            "inputs": {
                "input": "{CameraInit_1.output}"
            }, 
            "nodeType": "PanoramaPrepareImages", 
            "position": [
                200, 
                0
            ]
        }, 
        "SfMTransform_1": {
            "inputs": {
                "method": "manual", 
                "input": "{PanoramaEstimation_1.output}"
            }, 
            "nodeType": "SfMTransform", 
            "position": [
                2000, 
                0
            ]
        }, 
        "PanoramaMerging_1": {
            "inputs": {
                "compositingFolder": "{PanoramaCompositing_1.output}", 
                "input": "{PanoramaCompositing_1.input}"
            }, 
            "nodeType": "PanoramaMerging", 
            "position": [
                2800, 
                0
            ]
        }, 
        "PanoramaEstimation_1": {
            "inputs": {
                "matchesFolders": [
                    "{FeatureMatching_1.output}"
                ], 
                "input": "{FeatureMatching_1.input}", 
                "describerTypes": "{FeatureMatching_1.describerTypes}", 
                "featuresFolders": "{FeatureMatching_1.featuresFolders}"
            }, 
            "nodeType": "PanoramaEstimation", 
            "position": [
                1800, 
                0
            ]
        }, 
        "PanoramaInit_1": {
            "inputs": {
                "dependency": [
                    "{FeatureExtraction_1.output}"
                ], 
                "input": "{FeatureExtraction_1.input}"
            }, 
            "nodeType": "PanoramaInit", 
            "position": [
                1200, 
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
                1600, 
                0
            ]
        }
    }
}
