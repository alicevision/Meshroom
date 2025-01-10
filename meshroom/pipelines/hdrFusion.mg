{
    "header": {
        "nodesVersions": {
            "CameraInit": "12.0",
            "LdrToHdrCalibration": "3.1",
            "LdrToHdrMerge": "4.1",
            "LdrToHdrSampling": "4.0",
            "Publish": "1.3"
        },
        "releaseVersion": "2025.1.0-develop",
        "fileVersion": "2.0",
        "template": true
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
        "LdrToHdrCalibration_1": {
            "nodeType": "LdrToHdrCalibration",
            "position": [
                400,
                0
            ],
            "inputs": {
                "input": "{LdrToHdrSampling_1.input}",
                "samples": "{LdrToHdrSampling_1.output}",
                "userNbBrackets": "{LdrToHdrSampling_1.userNbBrackets}",
                "byPass": "{LdrToHdrSampling_1.byPass}",
                "calibrationMethod": "{LdrToHdrSampling_1.calibrationMethod}",
                "channelQuantizationPower": "{LdrToHdrSampling_1.channelQuantizationPower}",
                "workingColorSpace": "{LdrToHdrSampling_1.workingColorSpace}"
            }
        },
        "LdrToHdrMerge_1": {
            "nodeType": "LdrToHdrMerge",
            "position": [
                600,
                0
            ],
            "inputs": {
                "input": "{LdrToHdrCalibration_1.input}",
                "response": "{LdrToHdrCalibration_1.response}",
                "userNbBrackets": "{LdrToHdrCalibration_1.userNbBrackets}",
                "byPass": "{LdrToHdrCalibration_1.byPass}",
                "channelQuantizationPower": "{LdrToHdrCalibration_1.channelQuantizationPower}",
                "workingColorSpace": "{LdrToHdrCalibration_1.workingColorSpace}"
            }
        },
        "LdrToHdrSampling_1": {
            "nodeType": "LdrToHdrSampling",
            "position": [
                200,
                0
            ],
            "inputs": {
                "input": "{CameraInit_1.output}"
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
                    "{LdrToHdrMerge_1.outputFolder}"
                ]
            }
        }
    }
}