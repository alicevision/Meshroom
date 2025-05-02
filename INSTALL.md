# Development
This guide will help you setup a development environment to launch and contribute to Meshroom.


## Installation from source code

Get the source code and install runtime requirements:
```bash
git clone --recursive https://github.com/alicevision/Meshroom.git
cd meshroom
pip install -r requirements.txt
```


## Start Meshroom

 - __Launch the User Interface__

```bash
# Windows
set PYTHONPATH=%CD% && python meshroom/ui
# Linux/macOS
PYTHONPATH=$PWD python meshroom/ui
```

On Ubuntu, you may have conflicts between native drivers and mesa drivers. In that case, you need to force usage of native drivers by adding them to the LD_LIBRARY_PATH:
`LD_LIBRARY_PATH=/usr/lib/nvidia-340 PYTHONPATH=$PWD python meshroom/ui`
You may need to adjust the folder `/usr/lib/nvidia-340` with the correct driver version.

 - __Launch a 3D reconstruction in command line__

```bash
# Windows: set PYTHONPATH=%CD% &&
# Linux/macOS: PYTHONPATH=$PWD
python bin/meshroom_batch --input INPUT_IMAGES_FOLDER --output OUTPUT_FOLDER
```


## Use Prebuilt AliceVision

Download a [Release](https://github.com/alicevision/meshroom/releases) or extract files from a recent AliceVision build on [Dockerhub](https://hub.docker.com/r/alicevision/alicevision).

`LD_LIBRARY_PATH=~/foo/Meshroom-2023.2.0/aliceVision/lib/ PATH=$PATH:~/foo/Meshroom-2023.2.0/aliceVision/bin/ PYTHONPATH=$PWD python3 meshroom/ui`

You may need to checkout the corresponding Meshroom version/tag to avoid versions incompatibilities.


## Install Requirements

### Python Environment

* Windows: Python 3 (>=3.9)
* Linux: Python 3 (>=3.9)

To install all the requirements for runtime, development and packaging, simply run:
```bash
pip install -r requirements.txt -r dev_requirements.txt
```
> Note: `dev_requirements` is only related to testing and packaging. It is not mandatory to run Meshroom.

> Note: It is recommended to use a [virtual python environment](https://docs.python.org/3.9/library/venv.html), like `python -v venv meshroom_venv`.


### Qt/PySide

* PySide >= 6.7
Warning: The plugin AssimpSceneParser is missing from pre-built binaries, so it needs to be added manually (see https://bugreports.qt.io/browse/QTBUG-88821).
It can either be taken from an older version, or directly downloaded from here:
  * Linux: [libassimpsceneimport.so](https://drive.google.com/uc?export=download&id=1cTU7xrOsLI6ICgRSYz_t9E1lsrNF1kBB))
  * Windows: [assimpsceneimport.dll](https://drive.google.com/uc?export=download&id=1X9X9d5W_lCwEHWwF748IdnN1YYipAQT_)

and then copied into PySide's installation folder, in `plugins/sceneparsers`.


### AliceVision

Meshroom relies on the [AliceVision](https://github.com/alicevision/AliceVision) framework for visualization of images and 3D data.
AliceVision's binaries must be in the path while running Meshroom.
To build AliceVision, follow this [guide](https://github.com/alicevision/AliceVision/blob/develop/INSTALL.md) and add the installation in your PATH (and LD_LIBRARY_PATH on Linux/macOS).

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


### Qt AliceVision Plugin
[QtAliceVision](https://github.com/alicevision/QtAliceVision)

An additional Qt plugin can be built to extend Meshroom UI features. Note that it is optional but highly recommended.
This plugin uses AliceVision to load and visualize intermediate reconstruction files and OpenImageIO as backend to read images (including RAW/EXR).
It also adds support for Alembic file loading in Meshroom's 3D viewport, which allows to visualize sparse reconstruction results (point clouds and cameras).

```
QML2_IMPORT_PATH=/path/to/QtAliceVision/install/qml
QT_PLUGIN_PATH=/path/to/QtAliceVision/install
```
