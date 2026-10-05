{
    "header": {
        "releaseVersion": "2026.1.0+develop",
        "fileVersion": "2.1",
        "nodesVersions": {
            "InputFile": "1.0",
            "InputInt": "1.0",
            "InputString": "1.0"
        },
        "template": true
    },
    "graph": {
        "A_1": {
            "nodeType": "InputString",
            "position": [
                -109,
                39.0
            ],
            "inputs": {
                "string": "string_2"
            }
        },
        "Backdrop_1": {
            "nodeType": "Backdrop",
            "position": [
                -130,
                -131
            ],
            "internalInputs": {
                "nodeWidth": 200,
                "nodeHeight": 311
            }
        },
        "InputString_1": {
            "nodeType": "InputString",
            "position": [
                -109,
                -28
            ],
            "inputs": {
                "string": "string_1"
            }
        },
        "InsideBackdrop_1": {
            "nodeType": "InputFile",
            "position": [
                -109,
                108
            ],
            "inputs": {
                "inputFile": "/path1"
            }
        },
        "Int_1": {
            "nodeType": "InputInt",
            "position": [
                -109,
                -91
            ],
            "inputs": {
                "integer": 3
            }
        },
        "OutsideBackdrop_1": {
            "nodeType": "InputFile",
            "position": [
                -109,
                219.0
            ],
            "inputs": {
                "inputFile": "/path2"
            }
        }
    }
}