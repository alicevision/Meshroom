# Development
This guide will help you setup a development environment to launch and contribute to Meshroom.

## Requirements
### AliceVision
Meshroom relies on the [AliceVision](https://github.com/alicevision/AliceVision) framework. AliceVision's binaries must
be in the path while running Meshroom.
To build AliceVision, follow this [guide](https://github.com/alicevision/AliceVision/blob/develop/INSTALL.md).

Meshroom also relies on specific files provided with AliceVision.
* sensor database: a text database of sensor width per camera model.
Provided in AliceVision source tree: {ALICEVISION_REPOSITORY}/src/aliceVision/sensorDB/cameraSensors.db
* voctree (optional): for larger datasets (>200 images), greatly improves image matching performances.
It can be downloaded [here](https://gitlab.com/alicevision/trainedVocabularyTreeData/raw/master/vlfeat_K80L3.SIFT.tree).
* sphere detection model (optional): for the automated sphere detection in stereo photometry.
It can be downloaded [here](https://gitlab.com/alicevision/SphereDetectionModel/-/raw/main/sphereDetection_Mask-RCNN.onnx).
* semantic segmentation model (optional): for the semantic segmentation of objects.
It can be downloaded [here](https://gitlab.com/alicevision/semanticSegmentationModel/-/raw/main/fcn_resnet50.onnx).

Environment variables must be set for Meshroom to find those files:
```
ALICEVISION_SENSOR_DB=/path/to/database
ALICEVISION_VOCTREE=/path/to/voctree
ALICEVISION_SPHERE_DETECTION_MODEL=/path/to/detection/model
ALICEVISION_SEMANTIC_SEGMENTATION_MODEL=/path/to/segmentation/model
ALICEVISION_ROOT=/path/to/AliceVision/install/directory
```

### Python Environment
* Windows: Python 3 (>=3.5)
* Linux: Python 3 (>=3.5)


To install all the requirements for runtime, development and packaging, simply run:
```bash
pip install -r requirements.txt -r dev_requirements.txt
```
> Note: `dev_requirements` is only related to testing and packaging. It is not mandatory to run Meshroom.

### Qt/PySide
* PySide >= 5.15.2.1
Warning: The plugin AssimpSceneParser is missing from pre-built binaries, so it needs to be added manually (see https://bugreports.qt.io/browse/QTBUG-88821).
It can either be taken from an older version, or directly downloaded from here:
  * Linux: [libassimpsceneimport.so](https://drive.google.com/uc?export=download&id=1cTU7xrOsLI6ICgRSYz_t9E1lsrNF1kBB))
  * Windows: [assimpsceneimport.dll](https://drive.google.com/uc?export=download&id=1X9X9d5W_lCwEHWwF748IdnN1YYipAQT_)

and then copied into PySide's installation folder, in `plugins/sceneparsers`.


### Qt Plugin
An additional Qt plugin can be built to extend Meshroom UI features. It can be found on a separate repository,
though it might get better integration in the future.
Note that it is optional but highly recommended.

#### [QtAliceVision](https://github.com/alicevision/QtAliceVision)
It uses AliceVision to load and visualize intermediate reconstruction files and OpenImageIO as backend to read RAW/EXR images.
It also adds support for Alembic file loading in Meshroom's 3D viewport, which allows to visualize sparse reconstruction results
(point clouds and cameras).

```
QML2_IMPORT_PATH=/path/to/QtAliceVision/install/qml
QT_PLUGIN_PATH=/path/to/QtAliceVision/install
```


