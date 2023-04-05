{
    "header": {
        "pipelineVersion": "2.2",
        "releaseVersion": "2021.1.0",
        "fileVersion": "1.1",
        "template": true,
        "nodesVersions": {
            "CameraInit": "8.0",
            "RTI": "3.0"
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
        "RTI_1": {
            "nodeType": "RTI",
            "position": [
                231,
                -3
            ],
            "inputs": {
                "inputPath": "{CameraInit_1.output}",
                "pathToJSONLightFile": "/home/jean/Documents/Recherche/Reconstructions/RTI_105.json"
            }
        }
    }
}