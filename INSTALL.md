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

### Python 2.7

### Pyside2 (for Qt >= 5.10)
#### Update (02/05/2018)
[Python for Qt](http://blog.qt.io/blog/2018/04/13/qt-for-python-is-coming-to-a-computer-near-you/) is becoming official 
and [beta python wheels](http://download.qt.io/snapshots/ci/pyside/5.11/latest/pyside2/) are now provided.

#### Build Instructions (based on [this guide](https://fredrikaverpil.github.io/2016/08/17/compiling-pyside2/))

Since PySide2 is (not yet) available in Qt installer and no prebuilt binaries are available for Qt 5.10, 
you'll need to build it from source. The build procedure is quite similar on all platforms.

Pre-requisites:
* [Python 2.7](https://www.python.org/)
* [Qt 5.10](http://download.qt.io/official_releases/online_installers/)
* [llvm/libclang](http://download.qt.io/development_releases/prebuilt/libclang/)
* [CMake](https://cmake.org/download/)

##### Procedure
This procedure directly installs PySide as a package of the Python used for calling the setup script.
Make sure to use virtualenv if you want to keep this in a separate Python environment.

To simplify the build process, you can add 'bin' folders of cmake, llvm and qt in your PATH.
Alternatively, paths to binaries can be explicitely set when calling the setup.py script (as shown below).

```
# With {libclang}/bin in PATH
# /!\ branch 5.10 does not exist yet, but branch 5.9 is compatible with Qt-5.10
git clone --recursive --branch 5.9 https://codereview.qt-project.org/pyside/pyside-setup 

cd pyside-setup
python setup.py --ignore-git install --cmake=/path/to/cmake --qmake=/path/to/qmake
```

### Qt Plugins
Additional Qt plugins can be built to extend Meshroom UI features. They can be found on separate repositories,
though they might get better integration in the future.
Note that they are optional but highly recommended.

#### [QmlAlembic](https://github.com/alicevision/qmlAlembic)
Adds support for Alembic file loading in Meshroom's 3D viewport. Allows to visualize sparse reconstruction results 
(point cloud and cameras).

#### [QtOIIO](https://github.com/alicevision/QtOIIO)
Use OpenImageIO as backend to load images in Qt. Allow to visualize RAW/EXR images in Meshroom.
 