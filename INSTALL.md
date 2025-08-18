# Meshroom Installation
This guide will help you setup a development environment to launch and contribute to Meshroom.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation from source code](#installation-from-source-code)
3. [Use a prebuilt AliceVision](#use-a-prebuilt-alicevision)
4. [Start Meshroom](#start-meshroom)
5. [Install Requirements](#install-requirements)
    1. [Python environment](#python-environment)
    2. [Qt/PySide](#qtpyside)
    3. [AliceVision](#alicevision)
    4. [mrSegmentation plugin](#mrsegmentation-plugin)
    5. [QtAliceVision plugin](#qtalicevision-plugin)
6. [Adding custom nodes, templates and plugins](#adding-custom-nodes-templates-and-plugins)
    1. [Custom nodes](#custom-nodes)
    2. [Custom templates](#custom-templates)
    3. [Custom plugins](#custom-plugins)


## Quick Start

To quickly run Meshroom without setting up a development environment, follow these simple steps:

1. **Download the prebuilt binaries**:
    * Visit the [Releases](https://github.com/alicevision/meshroom/releases) page.
    * Download the latest release that is suitable for your operating system.
2. **Extract the archive**:
    * On Windows: right-click on the .zip file and select "Extract All", or run `unzip Meshroom-x.y.z.zip` in a terminal.
    * On Linux: in a terminal, run `tar -xzvf Meshroom.x.y.z.tar.gz`.
3. **Run Meshroom**: in the extracted folder, double-click on the "Meshroom" executable to launch it.

## Installation from source code

Get the source code and install runtime requirements:
```bash
git clone --recursive https://github.com/alicevision/Meshroom.git
cd meshroom
pip install -r requirements.txt
```

## Use a prebuilt AliceVision

Meshroom relies on the [AliceVision](https://github.com/alicevision/AliceVision) framework for visualization of images and 3D data.
Download a [Release](https://github.com/alicevision/meshroom/releases) or extract files from a recent AliceVision build on [Dockerhub](https://hub.docker.com/r/alicevision/alicevision).

`LD_LIBRARY_PATH=~/foo/Meshroom-2023.2.0/aliceVision/lib/ PATH=$PATH:~/foo/Meshroom-2023.2.0/aliceVision/bin/ PYTHONPATH=$PWD python3 meshroom/ui`

You may need to checkout the corresponding Meshroom version/tag to avoid versions incompatibilities.

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


## Install Requirements

### Python environment

* Windows: Python 3 (>=3.9)
* Linux: Python 3 (>=3.9)

To install all the requirements for runtime, development and packaging, simply run:
```bash
pip install -r requirements.txt -r dev_requirements.txt
```
> [!NOTE]
> `dev_requirements` is only related to testing and packaging. It is not mandatory to run Meshroom.

> [!NOTE]
> It is recommended to use a [virtual Python environment](https://docs.python.org/3.9/library/venv.html), like `python -m venv meshroom_venv`.


### Qt/PySide

* PySide >= 6.7

> [!WARNING]
> For PySide 6.8.0 and over, the following error may occur when leaving Meshroom's homepage: `Cannot load /path/to/pip/install/PySide6/qml/QtQuick/Scene3D/qtquickscene3dplugin.dll: specified module cannot be found`.
> This is caused by Qt63DQuickScene3D.dll which seems to be missing from the pip distribution, but can be retrieved from a standard Qt installation. 
> On recent Linux systems such as Ubuntu 25, this can be resolved by installing `libqt63dquickscene3d6` using the package manager.
> Alternatively:
> - On Windows, the DLL for MSVC2022_64 can be directly downloaded [here](https://drive.google.com/uc?export=download&id=1vhPDmDQJJfM_hBD7KVqRfh8tiqTCN7Jv). It then needs to be placed in `/path/to/pip/install/PySide6`.
> - On Linux, the .so (here, Rocky9-based) can be directly downloaded [here](https://drive.google.com/uc?export=download&id=1dq7rm_Egc-sQF6j6_E55f60INyxt1ega). It then needs to be placed in `/path/to/pip/install/PySide6/Qt/qml/QtQuick/Scene3D`.


### AliceVision

[AliceVision](https://github.com/alicevision/AliceVision)'s binaries must be in the path while running Meshroom.
To build AliceVision, follow this [guide](https://github.com/alicevision/AliceVision/blob/develop/INSTALL.md) and add the installation in your PATH (and LD_LIBRARY_PATH on Linux/macOS).

The following environment variable must always be set with the location of AliceVision's install directory:
```
ALICEVISION_ROOT=/path/to/AliceVision/install/directory
```

AliceVision provides nodes and templates for Meshroom, which need to be declared to Meshroom with the following environment variables:
```
MESHROOM_NODES_PATH={ALICEVISION_ROOT}/share/meshroom
MESHROOM_PIPELINE_TEMPLATES_PATH={ALICEVISION_ROOT}/share/meshroom
```

Meshroom also relies on [specific files provided with AliceVision](https://github.com/alicevision/AliceVision/blob/doc/updateInstall/INSTALL.md#environment-variables-to-set-for-meshroom), set through environment variables.
If these variables are not set, Meshroom will by default look for them in `{ALICEVISION_ROOT}/share/aliceVision`.

#### mrSegmentation plugin

Some templates provided by AliceVision contain nodes that are not packaged with AliceVision.
These nodes are part of the mrSegmentation plugin, which can be found [here](https://github.com/MeshroomHub/mrSegmentation).

To build and install mrSegmentation, follow this [guide](https://github.com/MeshroomHub/mrSegmentation/blob/main/INSTALL.md).

For mrSegmentation nodes to be correctly detected by Meshroom, the following environment variable should be set:
```
MESHROOM_PLUGINS_PATH=/path/to/mrSegmentation
```

### QtAliceVision plugin

[QtAliceVision](https://github.com/alicevision/QtAliceVision), an additional Qt plugin, can be built to extend Meshroom UI features.

Note that it is optional but highly recommended.

This plugin uses AliceVision to load and visualize intermediate reconstruction files and OpenImageIO as backend to read images (including RAW/EXR).
It also adds support for Alembic file loading in Meshroom's 3D viewport, which allows to visualize sparse reconstruction results (point clouds and cameras).

```
QML2_IMPORT_PATH=/path/to/QtAliceVision/install/qml
QT_PLUGIN_PATH=/path/to/QtAliceVision/install
```

## Adding custom nodes, templates and plugins

In addition to the nodes and templates provided by Meshroom and AliceVision, custom ones can be created, loaded by, and used in Meshroom.

### Custom nodes

Nodes need to be provided to Meshroom as Python modules, using the `MESHROOM_NODES_PATH` environment variable.

For example, to add a set of three custom nodes (`CustomNodeA`, `CustomNodeB` and `CustomNodeC`) to Meshroom, a Python
module containing these nodes must be created:
```
├── folderA
│   ├── customNodes
│   │   ├── __init__.py
│   │   ├── CustomNodeA.py
│   │   ├── CustomNodeB.py
│   │   └── CustomNodeC.py
├── folderB
```

Its containing folder must then be added to `MESHROOM_NODES_PATH`:
- On Windows:
  ```
  set MESHROOM_NODES_PATH=/path/to/folderA;%MESHROOM_NODES_PATH%
  ```
- On Linux:
  ```
  export MESHROOM_NODES_PATH=/path/to/folderA:$MESHROOM_NODES_PATH
  ```

> [!NOTE]
> A valid Meshroom node is a Python file that contains a class inheriting `meshroom.core.desc.BaseNode`.
> Before loading a node, Meshroom checks whether its description (the content of its class) is valid.
> If it is not, the node is rejected with an error log describing which part is invalid.

### Custom templates

The list of pipelines can also be enriched with custom templates, that are declared to Meshroom with the environment
variable `MESHROOM_PIPELINE_TEMPLATES_PATH`.

For example, if a couple of custom templates are saved in a folder "customTemplates", the variable should be set as follows:
- On Windows:
  ```
  set MESHROOM_PIPELINE_TEMPLATES_PATH=/path/to/customTemplate;%MESHROOM_PIPELINE_TEMPLATES_PATH%
  ```
- On Linux:
  ```
  export MESHROOM_PIPELINE_TEMPLATES_PATH=/path/to/customTemplates:$MESHROOM_PIPELINE_TEMPLATES_PATH
  ```

> [!TIP]
> A template can be a Meshroom graph of any type, but it is generally expected to be a graph saved in "minimal mode".
> In "minimal mode", the .mg file only contains, for each node of the graph, the attributes that have non-default values.
> To save a graph in "minimal mode", use the `File > Advanced > Save As Template` menu.

### Custom plugins

To add and use custom plugins with Meshroom, follow [**INSTALL_PLUGINS.md**](INSTALL_PLUGINS.md).
