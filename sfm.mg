{
    "CameraInit": {
        "nodeType": "CameraInit",
        "attributes": {
            "imageDirectory": "/PATH/TO/SOURCE/IMAGES",
            "sensorWidthDatabase": "/PATH/TO/sensor_width_camera_database.txt"
        }
    },
    "FeatureExtraction": {
        "nodeType": "FeatureExtraction",
        "attributes": {
            "input_file": "{CameraInit.outputSfm}"
        }
    },
    "FeatureMatching": {
        "nodeType": "FeatureMatching",
        "attributes": {
            "input_file": "{CameraInit.outputSfm}",
            "featuresDir": "{FeatureExtraction.outdir}"
        }
    },
    "StructureFromMotion": {
        "nodeType": "StructureFromMotion",
        "attributes": {
            "input_file": "{CameraInit.outputSfm}",
            "featuresDir": "{FeatureExtraction.outdir}",
            "matchdir": "{FeatureMatching.out_dir}"
        }
    }
}