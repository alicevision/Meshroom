{
    "header": {
        "releaseVersion": "2025.1.0-develop",
        "fileVersion": "2.0",
        "nodesVersions": {},
        "template": true
    },
    "graph": {
        "AppendFiles_1": {
            "nodeType": "AppendFiles",
            "position": [
                189,
                8
            ],
            "inputs": {
                "input": "{AppendText_1.output}",
                "input2": "{AppendText_2.output}",
                "input3": "{AppendText_1.input}",
                "input4": "{AppendText_2.input}"
            }
        },
        "AppendText_1": {
            "nodeType": "AppendText",
            "position": [
                0,
                0
            ],
            "inputs": {
                "inputText": "Input text from AppendText_1"
            }
        },
        "AppendText_2": {
            "nodeType": "AppendText",
            "position": [
                0,
                160
            ],
            "inputs": {
                "inputText": "Input text from AppendText_2"
            }
        }
    }
}