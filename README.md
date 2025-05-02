# ![Meshroom - 3D Reconstruction Software](/docs/logo/banner-meshroom.png)

Meshroom is an open-source, node-based visual programming framework—a flexible toolbox for creating, managing, and executing complex data processing pipelines.

Meshroom uses a nodal system where each node represents a specific operation, and output attributes can seamlessly feed into subsequent steps. When a node’s attribute is modified, only the affected downstream nodes are invalidated, while cached intermediate results are reused to minimize unnecessary computation.

Meshroom supports both local and distributed execution, enabling efficient parallel processing on render farms.
It also includes interactive widgets for visualizing images and 3D data. Official releases come with built-in plugins for computer vision and machine learning tasks.

[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/2997/badge)](https://bestpractices.coreinfrastructure.org/projects/2997)
[![Build status](https://github.com/alicevision/Meshroom/actions/workflows/continuous-integration.yml/badge.svg?branch=develop)](https://github.com/alicevision/Meshroom/actions/workflows/continuous-integration.yml)

# Get the project

You can [download pre-compiled binaries for the latest release](https://github.com/alicevision/meshroom/releases).  
If you want to build it yourself, see [**INSTALL.md**](INSTALL.md) to setup the project and pre-requisites.


# Concepts

- **Graph, Nodes and Attributes**
Nodes are the fundamental building blocks, each performing a specific task. A graph is a collection of interconnected nodes, defining the sequence of operations.  The nodes are connected through edges that represent the flow of data between them. Each node has a set of attributes or parameters that control its behavior. Adjusting a parameter triggers the invalidation of all connected nodes.
- **Templates**
Each plugin provides a set of pipeline templates. You can customize them and save your own templates.
- **Local / Renderfarm**
You can perform computations either locally or by using a render farm for distributed processing. As the computations proceed, you can monitor their progress and review the logs. It also keeps track of resource consumption to monitor the efficiency and identify the bottlenecks. You can use both local and renderfarm computation at the same time, as Meshroom keeps track of locked nodes while computing externally.
- **Custom Plugins**
You can create your custom plugin, in pure Python or through command lines to execute external software.


# User Interface

The Meshroom UI is divided into several key areas:
 - **Graph Editor**: The central area where nodes are placed and connected to form a processing pipeline.
 - **Node Editor**: It contains multiple tabs with:
   - **Attributes**: Displays the attributes and parameters of the selected node.
   - **Log**: Displays execution logs and error messages.
   - **Statistics**: Displays resources consumption
   - **Status**: Display some technical information on the node (workstation, start/end time, etc.)
   - **Documentation**: The nodes help.
   - **Notes**: Change label or put some notes on the node to know why it’s used in this graph.
 - **2D & 3D Viewer**: Visualizes the output of certain nodes.
 - **Image Gallery**: Visualize the list of input files.


# Manual and Tutorials
 - [Meshroom Manual](https://meshroom-manual.readthedocs.io)
 - [Meshroom FAQ](https://github.com/alicevision/meshroom/wiki)


# Plugins bundled by default

## AliceVision Plugin

[AliceVision Website](http://alicevision.org)

[AliceVision Repository](https://github.com/alicevision/AliceVision)

AliceVision provides state-of-the-art 3D computer vision and machine learning algorithms that can be tested, analyzed and reused. The project is a result of collaboration between academia and industry to provide cutting-edge algorithms with the robustness and the quality required for production usage.
AliceVision plugin provides pipelines for:
 - *3D Reconstruction* from multi-view images, see the [presentation of the pipeline steps](http://alicevision.github.io/#photogrammetry) and [some results on sketchfab](http://sketchfab.com/AliceVision)
 - *Camera Tracking*
 - *HDR fusion* of multi-bracketed photographies
 - *Panorama stitching* supports fisheye optics, but also the generation of high-resolution images using motorized head systems.
 - *Photometric Stereo* for geometric reconstruction from a single view with multiple lightings
 - *Multi-View Photometric Stereo* to combine photogrammetry and photometric stereo


## Segmentation Plugin
[MrSegmentation Repository](https://github.com/meshroomHub/mrSegmentation)
Set of nodes for image segmentation from text prompts.


## DepthEstimation Plugin
[MrDepthEstimation](https://github.com/meshroomHub/mrDepthEstimation)
Set of nodes for depth estimation from an image sequence.


# Other plugins

See the [MeshroomHub](https://github.com/meshroomHub) for more plugins.

## Research Plugin
[Meshroom Research Repository](https://github.com/alicevision/MeshroomResearch)

Meshroom-Research focuses on evaluating and benchmarking Machine Learning nodes for 3D Computer Vision.


## MicMac Plugin
[MeshroomMicMac Repository](https://github.com/alicevision/MeshroomMicMac)

Exploratory plugin providing MicMac pipelines. It does not yet support the full invalidation system of Meshroom but is fully usable to adjust the pipeline and process it.
MicMac is a free open-source photogrammetric software for 3D reconstruction under development at the National Institute of Geographic and Forestry Information (French Mapping Agency, IGN) and the National School of Geographic Sciences (ENSG) within the LASTIG lab.


## Geolocation Plugin
[MrGeolocation Repository](https://github.com/alicevision/mrGeolocation)

The Meshroom Geolocation plugin consists of nodes that utilize the GPS data to download 2D and 3D maps. It could extract the embedded GPS data from photographs to accurately place and contextualize your 3D scans within their global geographical environment.
You can retrieve a variety of maps: a 2D map (worldwide – using Open Street Map), an elevation model in 3D (worldwide – using NASA datasets), and a highly detailed 3D model from Lidar scans when available (France-only – using the open data France’s IGN Lidar datasets).


# License
The project is released under MPLv2, see [**COPYING.md**](COPYING.md).


# Citation
  ```
  @inproceedings{alicevision2021,
    title={{A}liceVision {M}eshroom: An open-source {3D} reconstruction pipeline},
    author={Carsten Griwodz and Simone Gasparini and Lilian Calvet and Pierre Gurdjos and Fabien Castan and Benoit Maujean and Gregoire De Lillo and Yann Lanthony},
    booktitle={Proceedings of the 12th ACM Multimedia Systems Conference - {MMSys '21}},
    doi = {10.1145/3458305.3478443},
    publisher = {ACM Press},
    year = {2021}
  }
  ```


# Contributing
We welcome contributions! Check out our [Contribution Guidelines](CONTRIBUTING.md) to get started. Whether you're a developer, designer, or documentation enthusiast, there's a place for you in the Meshroom community.


# Contact

Use the public mailing-list to ask questions or request features. It is also a good place for informal discussions like sharing results, interesting related technologies or publications: [forum@alicevision.org](https://groups.google.com/g/alicevision)

You can also contact the core team privately on: [team@alicevision.org](mailto:team@alicevision.org).

