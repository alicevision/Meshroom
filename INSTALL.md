# Development
This guide will help you setup a development environment to launch and contribute to Meshroom.

## Requirements
### Python 2.7
### Qt 5.10
### Pyside2
#### Build Instructions (based on https://fredrikaverpil.github.io/2016/08/17/compiling-pyside2/)

Since PySide2 is (not yet) available in Qt installer and no prebuilt binaries are available for Qt 5.10, 
you'll need to build it from source. The build procedure is quite similar on all platforms.

Pre-requisites:
* Python 2.7
* Qt 5.10 (http://download.qt.io/official_releases/online_installers/)
* llvm/libclang (http://download.qt.io/development_releases/prebuilt/libclang/)
* CMake (https://cmake.org/download/)

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

 
