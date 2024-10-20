# ![Meshroom - 3D Reconstruction Software](/docs/logo/banner-meshroom.png)

[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/2997/badge)](https://bestpractices.coreinfrastructure.org/projects/2997)

Meshroom is a free, open-source 3D Reconstruction Software based on the [AliceVision](https://github.com/alicevision/AliceVision) Photogrammetric Computer Vision framework.

Learn more details about the pipeline on [AliceVision website](http://alicevision.github.io).

See [results of the pipeline on sketchfab](http://sketchfab.com/AliceVision).

Continuous integration: [![Build status](https://github.com/alicevision/Meshroom/actions/workflows/continuous-integration.yml/badge.svg?branch=develop)](https://github.com/alicevision/Meshroom/actions/workflows/continuous-integration.yml)


## Photogrammetry

Photogrammetry is the science of making measurements from photographs.
It infers the geometry of a scene from a set of unordered photographs or videos.
Photography is the projection of a 3D scene onto a 2D plane, losing depth information.
The goal of photogrammetry is to reverse this process.

See the [presentation of the pipeline steps](http://alicevision.github.io/#photogrammetry).


## Manual

https://meshroom-manual.readthedocs.io


## Tutorials

* [Meshroom: Open Source 3D Reconstruction Software](https://www.youtube.com/watch?v=v_O6tYKQEBA) by [Mikros Image](http://www.mikrosimage.com)

  Overall presentation of the Meshroom software.

* [Meshroom: Initial Pipeline, CCTags, using a Turntable and Known Camera Positions](https://www.youtube.com/watch?v=XUKu1apUuVE) by [mpr-projects](https://github.com/mpr-projects)

  Overview of the default Meshroom 2023.3 pipeline, including masking, cctags and known camera positions.

* [Meshroom Tutorial on Sketchfab](https://sketchfab.com/blogs/community/tutorial-meshroom-for-beginners) by [Mikros Image](http://www.mikrosimage.com)

  Detailed tutorial with a focus on the features of the 2019.1 release.

* [Photogrammetry 2 – 3D scanning with just PHONE/CAMERA simpler, better than ever!](https://www.youtube.com/watch?v=1D0EhSi-vvc) by [Prusa 3D Printer](https://blog.prusaprinters.org)

  Overall presentation of the photogrammetry practice with Meshroom.

* [How to 3D Photoscan Easy and Free! by ](https://www.youtube.com/watch?v=k4NTf0hMjtY) by [CG Geek](https://www.youtube.com/channel/UCG8AxMVa6eutIGxrdnDxWpQ)

  Overall presentation of the protogrammetry practice with Meshroom and detailed presentation how to do the retolopogy in Blender.

* [Meshroom Survival Guide](https://www.youtube.com/watch?v=eiEaHLNJJ94) by [Moviola](https://moviola.com)

  Presentation of the Meshroom software with a focus on using it for Match Moving.


## Customization

### Custom Pipelines

You can create custom pipelines in the user interface and save it as template: `File > Advanced > Save As Template`.
You can define the `MESHROOM_PIPELINE_TEMPLATES_PATH` environment variable to specific folders to make these pipelines available in Meshroom.
In a standard precompiled version of Meshroom, you can also directly add custom pipelines in `lib/meshroom/pipelines`.

### Custom Nodes

You can create custom nodes in python and make them available in Meshroom using the `MESHROOM_NODES_PATH` environment variable.
[Here is an example](meshroom/nodes/blender/ScenePreview.py) to launch a Blender rendering from Meshroom.
In a standard precompiled version of Meshroom, you can also directly add custom nodes in `lib/meshroom/nodes`.
To be recognized by Meshroom, a custom folder with nodes should be a Python module (an `__init__.py` file is needed).

### Plugins

Meshroom supports installing containerised plugins via Docker (with the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)) or [Anaconda](https://docs.anaconda.com/free/miniconda/index.html).

To do so, make sure docker or anaconda is installed properly and available from the command line.
Then click on `File > Advanced > Install Plugin From URL` or `File > Advanced > Install Plugin From Local Folder` to begin the installation.

To learn more about using or creating plugins, check the explanations [here](meshroom/plugins/README.md).

## License

The project is released under MPLv2, see [**COPYING.md**](COPYING.md).


## Citation

If you use this project for a publication, please cite the [paper](https://hal.archives-ouvertes.fr/hal-03351139):
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

## Get the project

You can [download pre-compiled binaries for the latest release](https://github.com/alicevision/meshroom/releases).  

If you want to build it yourself, see [**INSTALL.md**](INSTALL.md) to setup the project and pre-requisites.

Get the source code and install runtime requirements:
```bash
git clone --recursive git://github.com/alicevision/meshroom
cd meshroom
pip install -r requirements.txt
```


## Start Meshroom

You need to have [AliceVision](https://github.com/alicevision/AliceVision) installation in your PATH (and LD_LIBRARY_PATH on Linux/macOS).

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

## Start Meshroom without building AliceVision

To use Meshroom (ui) without building AliceVision
*   Download a [release](https://github.com/alicevision/meshroom/releases)
*   Checkout corresponding Meshroom (ui) version/tag to avoid versions incompatibilities
*   `LD_LIBRARY_PATH=~/foo/Meshroom-2023.2.0/aliceVision/lib/ PATH=$PATH:~/foo/Meshroom-2023.2.0/aliceVision/bin/ PYTHONPATH=$PWD python3 meshroom/ui`

## Start and Debug Meshroom in an IDE

PyCharm Community is free IDE which can be used. To start and debug a project with that IDE,
right-click on `Meshroom/ui/__main__.py` > `Debug`, then `Edit Configuration`, in `Environment variables` : 
*   If you want to use aliceVision built by yourself add: `PATH=$PATH:/foo/build/Linux-x86_64/`
*   If you want to use aliceVision release add: `LD_LIBRARY_PATH=/foo/Meshroom-2023.2.0/aliceVision/lib/;PATH=$PATH:/foo/Meshroom-2023.2.0/aliceVision/bin/` (Make sure that you are on the branch matching the right version)

![image](https://user-images.githubusercontent.com/937836/127321375-3bf78e73-569d-414a-8649-de0307adf794.png)


## FAQ

See the [Meshroom wiki](https://github.com/alicevision/meshroom/wiki) for more information.


## Contact

Use the public mailing-list to ask questions or request features. It is also a good place for informal discussions like sharing results, interesting related technologies or publications:
> [alicevision@googlegroups.com](mailto:alicevision@googlegroups.com)
> [http://groups.google.com/group/alicevision](http://groups.google.com/group/alicevision)

You can also contact the core team privately on: [alicevision-team@googlegroups.com](mailto:alicevision-team@googlegroups.com).
