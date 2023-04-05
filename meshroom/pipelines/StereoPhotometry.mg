{
    "header": {
        "pipelineVersion": "2.2",
        "releaseVersion": "2021.1.0",
        "fileVersion": "1.1",
        "template": true,
        "nodesVersions": {
            "SphereDetection": "3.0",
            "LightingCalibration": "3.0",
            "CameraInit": "8.0",
            "NormalIntegration": "3.0",
            "PhotometricStereo": "3.0"
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
                406,
                -2
            ],
            "inputs": {
                "inputPath": "{SphereDetection_1.input_sfmdata_path}",
                "inputJSON": "{SphereDetection_1.output_path}"
            }
        },
        "SphereDetection_1": {
            "nodeType": "SphereDetection",
            "position": [
                204,
                4
            ],
            "inputs": {
                "input_sfmdata_path": "{CameraInit_1.output}"
            }
        },
        "PhotometricStereo_1": {
            "nodeType": "PhotometricStereo",
            "position": [
                591,
                -2
            ],
            "inputs": {
                "inputPath": "{LightingCalibration_1.inputPath}",
                "pathToJSONLightFile": "{LightingCalibration_1.outputFile}"
            }
        }
    }
}
