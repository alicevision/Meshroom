{
    "header": {
        "pipelineVersion": "2.2",
        "releaseVersion": "2023.3.0",
        "fileVersion": "1.1",
        "template": true,
        "nodesVersions": {
            "ExportDistortion": "1.0",
            "CameraInit": "10.0",
            "CheckerboardDetection": "1.0",
            "DistortionCalibration": "4.0",
            "Publish": "1.3"
        }
    },
    "graph": {
        "CheckerboardDetection_1": {
            "nodeType": "CheckerboardDetection",
            "position": [
                200,
                0
            ],
            "inputs": {
                "input": "{CameraInit_1.output}",
                "exportDebugImages": true
            }
        },
        "DistortionCalibration_1": {
            "nodeType": "DistortionCalibration",
            "position": [
                400,
                0
            ],
            "inputs": {
                "input": "{CheckerboardDetection_1.input}",
                "checkerboards": "{CheckerboardDetection_1.output}"
            }
        },
        "ExportDistortion_1": {
            "nodeType": "ExportDistortion",
            "position": [
                600,
                0
            ],
            "inputs": {
                "input": "{DistortionCalibration_1.output}"
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
                    "{ExportDistortion_1.output}"
                ]
            }
        },
        "CameraInit_1": {
            "nodeType": "CameraInit",
            "position": [
                0,
                0
            ],
            "inputs": {}
        }
    }
}