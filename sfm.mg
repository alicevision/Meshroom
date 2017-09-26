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
    },
    "PrepareDenseScene": {
        "nodeType": "PrepareDenseScene",
        "attributes": {
            "sfmdata": "{StructureFromMotion.out_sfmdata_file}"
        }
    },
    "CamPairs": {
        "nodeType": "CamPairs",
        "attributes": {
            "mvsConfig": "{PrepareDenseScene.mvsConfig}"
        }
    },
    "DepthMap": {
        "nodeType": "DepthMap",
        "attributes": {
            "mvsConfig": "{CamPairs.mvsConfig}"
        }
    },
    "DepthMapFilter": {
        "nodeType": "DepthMapFilter",
        "attributes": {
            "mvsConfig": "{DepthMap.mvsConfig}"
        }
    },
    "Fuse": {
        "nodeType": "Fuse",
        "attributes": {
            "mvsConfig": "{DepthMapFilter.mvsConfig}"
        }
    },
    "Meshing": {
        "nodeType": "Meshing",
        "attributes": {
            "mvsConfig": "{Fuse.mvsConfig}"
        }
    },
    "Texturing": {
        "nodeType": "Texturing",
        "attributes": {
            "mvsConfig": "{Meshing.mvsConfig}"
        }
    }
}