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

Environment variables must be set for Meshroom to find those files:
```
ALICEVISION_SENSOR_DB=/path/to/database
ALICEVISION_VOCTREE=/path/to/voctree
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
* PySide >= 5.12.2
Warning: On Windows, the plugin AssimpSceneParser is missing from pre-built binaries, so you need to add it manually (from an older version for instance).
See https://bugreports.qt.io/browse/QTBUG-74535

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

#### [QtAliceVision](https://github.com/alicevision/QtAliceVision)
Use AliceVision to load and visualize intermediate reconstruction files.
```
QML2_IMPORT_PATH=/path/to/qtAliceVision/install/qml
```


