# ![Meshroom - 3D Reconstruction Software](/docs/logo/banner-meshroom.png)

[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/2997/badge)](https://bestpractices.coreinfrastructure.org/projects/2997)

Meshroom is a free, open-source 3D Reconstruction Software based on the [AliceVision](https://github.com/alicevision/AliceVision) Photogrammetric Computer Vision framework.

Learn more details about the pipeline on [AliceVision website](http://alicevision.github.io).

See [results of the pipeline on sketchfab](http://sketchfab.com/AliceVision).

Continuous integration:
* Windows: [![Build status](https://ci.appveyor.com/api/projects/status/25sd7lfr3v0rnvni/branch/develop?svg=true)](https://ci.appveyor.com/project/AliceVision/meshroom/branch/develop)
* Linux: [![Build Status](https://travis-ci.org/alicevision/meshroom.svg?branch=develop)](https://travis-ci.org/alicevision/meshroom)


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

* [Meshroom Tutorial on Sketchfab](https://sketchfab.com/blogs/community/tutorial-meshroom-for-beginners) by [Mikros Image](http://www.mikrosimage.com)

Detailed tutorial with a focus on the features of the 2019.1 release.

* [Photogrammetry 2 – 3D scanning with just PHONE/CAMERA simpler, better than ever!](https://www.youtube.com/watch?v=1D0EhSi-vvc) by [Prusa 3D Printer](https://blog.prusaprinters.org)

Overall presentation of the protogrammetry practice with Meshroom.

* [How to 3D Photoscan Easy and Free! by ](https://www.youtube.com/watch?v=k4NTf0hMjtY) by [CG Geek](https://www.youtube.com/channel/UCG8AxMVa6eutIGxrdnDxWpQ)

Overall presentation of the protogrammetry practice with Meshroom and detailed presentation how to do the retolopogy in Blender.

* [Meshroom Survival Guide](https://www.youtube.com/watch?v=eiEaHLNJJ94) by [Moviola](https://moviola.com)

Presentation of the Meshroom software with a focus on using it for Match Moving.


## License

The project is released under MPLv2, see [**COPYING.md**](COPYING.md).


## Get the project

See [**INSTALL.md**](INSTALL.md) to setup the project and pre-requisites.

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
python bin/meshroom_photogrammetry --input INPUT_IMAGES_FOLDER --output OUTPUT_FOLDER
```


## FAQ

See the [Meshroom wiki](https://github.com/alicevision/meshroom/wiki) for more information.


## Contact

Use the public mailing-list to ask questions or request features. It is also a good place for informal discussions like sharing results, interesting related technologies or publications:
> [alicevision@googlegroups.com](mailto:alicevision@googlegroups.com)
> [http://groups.google.com/group/alicevision](http://groups.google.com/group/alicevision)

You can also contact the core team privately on: [alicevision-team@googlegroups.com](mailto:alicevision-team@googlegroups.com).
