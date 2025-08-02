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

To use Meshroom with custom plugins, see [**INSTALL_PLUGINS.md**](INSTALL_PLUGINS.md).


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
   - **Statistics**: Displays resource consumption
   - **Status**: Display some technical information on the node (workstation, start/end time, etc.)
   - **Documentation**: Node Documentation.
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

AliceVision provides state-of-the-art 3D Computer Vision and Machine Learning algorithms that analyze and understand image content to transform collections of regular 2D photographs into detailed 3D models, camera positions, and scene geometry. Born from collaboration between academia and industry, it delivers research-grade algorithms with production-level robustness and quality.
The AliceVision plugin offers comprehensive pipelines for:
- **3D Reconstruction** from multi-view images ([pipeline overview](http://alicevision.github.io/#photogrammetry), [results on Sketchfab](http://sketchfab.com/AliceVision))
- **Camera Tracking** for camera motion estimation
- **HDR Fusion** from multi-bracketed photography
- **Panorama Stitching** including fisheye support and motorized head systems
- **Photometric Stereo** for geometric reconstruction from a single view with multiple lightings
- **Multi-View Photometric Stereo** combining photogrammetry with photometric stereo


## Segmentation Plugin

[MrSegmentation](https://github.com/meshroomHub/mrSegmentation): A set of nodes for AI-powered image segmentation from natural language prompts. The plugin leverages foundation models to automatically identify and isolate specific objects or regions in images based on textual descriptions, enabling intuitive content-aware processing workflows.


# Other plugins

See [MeshroomHub](https://github.com/meshroomHub) for more plugins.

## DepthEstimation Plugin

[MrDepthEstimation](https://github.com/meshroomHub/mrDepthEstimation): A set of nodes for AI-based monocular depth estimation from image sequences. The plugin leverages deep learning models to predict depth information from single images, enabling depth estimation in new scenarios.


## RoMa Plugin

[MrRoma](https://github.com/meshroomHub/mrRoma): A set of nodes for RoMa (robust dense feature matching).
The plugin leverages foundation models to provide pixel-dense correspondence estimation with reliable certainty maps, enabling robust matching even under extreme variations in scale, illumination, viewpoint, and texture.


## GSplat Plugin

[MrGSplat](https://github.com/meshroomHub/mrGSplat): A set of nodes for 3D Gaussian Splatting reconstruction. The plugin integrates seamlessly with AliceVision's photogrammetry pipeline, allowing users to create Gaussian splat representations from multi-view images and to render new viewpoints.


## Research Plugin

[Meshroom Research](https://github.com/meshroomHub/MeshroomResearch)
A research-oriented plugin for evaluating and benchmarking cutting-edge Machine Learning algorithms in 3D Computer Vision. The plugin provides experimental nodes and evaluation frameworks to test new methodologies, compare algorithm performance, and validate research innovations before integration into production pipelines.


## MicMac Plugin

[MeshroomMicMac](https://github.com/alicevision/MeshroomMicMac)

An exploratory plugin providing MicMac pipelines. 
It does not yet support the full invalidation system of Meshroom, but is fully usable to adjust the pipeline and process it.
MicMac is a free open-source photogrammetric software for 3D reconstruction under development at the National Institute of Geographic and Forestry Information (French Mapping Agency, IGN) and the National School of Geographic Sciences (ENSG) within the LASTIG lab.


## Geolocation Plugin

[MrGeolocation](https://github.com/meshroomHub/mrGeolocation)

The Meshroom Geolocation plugin consists of nodes that utilize the GPS data to download 2D and 3D maps. It could extract the embedded GPS data from photographs to accurately place and contextualize your 3D scans within their global geographical environment.
You can retrieve a variety of maps: a 2D map (worldwide – using Open Street Map), an elevation model in 3D (worldwide – using NASA datasets), and a highly detailed 3D model from Lidar scans when available (France-only – using France’s open data IGN Lidar datasets).


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
