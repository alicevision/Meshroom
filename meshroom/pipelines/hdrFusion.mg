{
    "header": {
        "nodesVersions": {
            "CameraInit": "10.0",
            "LdrToHdrMerge": "4.1",
            "LdrToHdrCalibration": "3.1",
            "LdrToHdrSampling": "4.0",
            "Publish": "1.3"
        },
        "releaseVersion": "2024.1.0-develop",
        "fileVersion": "1.1",
        "template": true
    },
    "graph": {
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
        "CameraInit_1": {
            "nodeType": "CameraInit",
            "position": [
                0,
                0
            ],
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
