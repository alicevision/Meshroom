{
    "header": {
        "releaseVersion": "2025.1.0-develop",
        "fileVersion": "2.0",
        "template": true,
        "nodesVersions": {
            "CameraInit": "12.0",
            "LightingCalibration": "1.0",
            "PhotometricStereo": "1.0",
            "Publish": "1.3",
            "SphereDetection": "1.0"
        }
    },
    "graph": {
        "CameraInit_1": {
            "nodeType": "CameraInit",
            "position": [
                0,
                0
            ],
            "inputs": {}
        },
        "LightingCalibration_1": {
            "nodeType": "LightingCalibration",
            "position": [
                400,
                0
            ],
            "inputs": {
                "inputPath": "{SphereDetection_1.input}",
                "inputDetection": "{SphereDetection_1.output}"
            }
        },
        "PhotometricStereo_1": {
            "nodeType": "PhotometricStereo",
            "position": [
                600,
                0
            ],
            "inputs": {
                "inputPath": "{LightingCalibration_1.inputPath}",
                "pathToJSONLightFile": "{LightingCalibration_1.outputFile}"
            }
        },
        "Publish_1": {
            "nodeType": "Publish",
            "position": [
                800,
                0
            ],
            "inputs": {
                "inputFiles": [
                    "{PhotometricStereo_1.outputSfmDataNormal}",
                    "{PhotometricStereo_1.normals}",
                    "{PhotometricStereo_1.normalsWorld}",
                    "{PhotometricStereo_1.albedo}",
                    "{PhotometricStereo_1.outputSfmDataAlbedo}",
                    "{PhotometricStereo_1.inputPath}",
                    "{PhotometricStereo_1.outputSfmDataNormalPNG}",
                    "{PhotometricStereo_1.normalsPNG}",
                    "{PhotometricStereo_1.pathToJSONLightFile}"
                ]
            }
        },
        "SphereDetection_1": {
            "nodeType": "SphereDetection",
            "position": [
                200,
                0
            ],
            "inputs": {
                "input": "{CameraInit_1.output}",
                "autoDetect": true
            }
        }
    }
}
