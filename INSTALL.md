# Development
This guide will help you setup a development environment to launch and contribute to Meshroom.

## Requirements
### AliceVision
Meshroom relies on the [AliceVision](https://github.com/alicevision/AliceVision) framework. AliceVision's binaries must 
be in the path while running Meshroom. 
To build AliceVision, follow this [guide](https://github.com/alicevision/AliceVision/blob/develop/INSTALL.md).

Meshroom also relies on specific files provided with AliceVision.
* sensor database: a text database of sensor width per camera model. 
Provided in AliceVision source tree: {ALICEVISION_ROOT}/src/aliceVision/sensorDB/sensor_width_camera_database.txt
* voctree (optional): for larger datasets (>200 images), greatly improves image matching performances.
It can be downloaded [here](https://gitlab.com/alicevision/trainedVocabularyTreeData/raw/master/vlfeat_K80L3.SIFT.tree).
 
Environment variables must be set for Meshroom to find those files:
```
ALICEVISION_SENSOR_DB=/path/to/database
ALICEVISION_VOCTREE=/path/to/voctree
```

### Python Environment
* Python 2 (>= 2.7) or Python 3 (>=3.5)

To install all the requirements for runtime, development and packaging, simply run:
```bash
pip install -r requirements.txt -r dev_requirements.txt
```
> Node: `dev_requirements` is only related to testing and packaging. It is not mandatory to run Meshroom.

### Qt Plugins
Additional Qt plugins can be built to extend Meshroom UI features. They can be found on separate repositories,
though they might get better integration in the future.
Note that they are optional but highly recommended.

#### [QmlAlembic](https://github.com/alicevision/qmlAlembic)
Adds support for Alembic file loading in Meshroom's 3D viewport. Allows to visualize sparse reconstruction results 
(point cloud and cameras).
```
QML2_IMPORT_PATH=/path/to/qmlAlembic/install/qml
```

#### [QtOIIO](https://github.com/alicevision/QtOIIO)
Use OpenImageIO as backend to load images in Qt. Allow to visualize RAW/EXR images in Meshroom.
This plugin also provides a QML Qt3D Entity to load depthmaps files stored in EXR format.
```
QT_PLUGIN_PATH=/path/to/QtOIIO/install
QML2_IMPORT_PATH=/path/to/QtOIIO/install/qml
```
