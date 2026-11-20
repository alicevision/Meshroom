# Meshroom Nightly Build

The nightly build is a prebuilt, ready-to-run Meshroom built automatically from the `develop` branch.
Use it to try the latest features and fixes before they reach an official release, or to check whether a bug is already fixed.

> [!WARNING]
> Nightly builds are untested beyond automated smoke tests and may be unstable. Do not rely on them for production work, and keep a copy of your projects: a scene saved with a nightly may not open in an older release.

## Table of Contents

1. [Where to get it](#where-to-get-it)
2. [Which archive to choose](#which-archive-to-choose)
3. [Install and run](#install-and-run)
    1. [Full archive](#full-archive)
    2. [Meshroom-only archive](#meshroom-only-archive)
4. [System requirements](#system-requirements)
5. [Reporting issues](#reporting-issues)
6. [How the nightly is built](#how-the-nightly-is-built)

## Where to get it

The nightly is published as a single pre-release named **Nightly build (develop)**, under the `nightly` tag:

**https://github.com/alicevision/Meshroom/releases/tag/nightly**

There is only ever one nightly: each new build replaces the archives of the previous one, and the `nightly` tag moves to the commit it was built from.
Older nightlies are not kept.

The release notes give:
* the build date and the Meshroom commit it was built from;
* the names of the four archives;
* the exact AliceVision and QtAliceVision nightly archives it was built against.

## Which archive to choose

Each nightly provides two archives per platform, named after the build date and commit (`<label>` = `YYYY.MM.DD-<short sha>`):

| | Meshroom only | Meshroom + AliceVision + QtAliceVision |
|---|---|---|
| **Windows** | `Meshroom-<label>-windows.zip` | `Meshroom-<label>-windows-full.zip` |
| **Linux** | `Meshroom-<label>-linux.tar.gz` | `Meshroom-<label>-linux-full.tar.gz` |

* **Full archive** (`-full`): ready to use. It bundles the AliceVision nightly (photogrammetry binaries, nodes and pipeline templates), the QtAliceVision nightly (image and 3D viewer plugins) and their Python interpreter. **Pick this one unless you have a reason not to.**
* **Meshroom only**: the Meshroom application and command-line tools, without AliceVision. Useful if you provide your own AliceVision/QtAliceVision installation, or only use Meshroom with other plugins.

macOS is not part of the nightly build.

## Install and run

Each archive contains a single `Meshroom-<label>-<os>/` folder. No installer is needed: extract it anywhere and run it from there.

* Windows: right-click the `.zip` file and select "Extract All", or run `tar -xf Meshroom-<label>-windows-full.zip` in a terminal.
* Linux: `tar -xzf Meshroom-<label>-linux-full.tar.gz`

Avoid extracting a new nightly over an older one: extract it into a new folder instead.

### Full archive

Run `Meshroom` (`Meshroom.exe` on Windows) from the extracted folder. Everything is configured automatically at startup from the folder layout:

```
Meshroom-<label>-<os>/
├── Meshroom[.exe]          # GUI
├── meshroom_batch[.exe]    # command-line tools (meshroom_compute, meshroom_submit, ...)
├── lib/                    # frozen Meshroom and its Python dependencies
├── aliceVision/            # AliceVision nightly: bin/, lib/, share/aliceVision/, share/meshroom/ (nodes + templates)
├── qtPlugins/              # QtAliceVision nightly: image format plugins and qml/
└── python/                 # Python interpreter shipped with AliceVision (used to run Python nodes)
```

Meshroom sets `ALICEVISION_ROOT`, `PATH`, `QT_PLUGIN_PATH`, `QML2_IMPORT_PATH`, `MESHROOM_NODES_PATH` and `MESHROOM_PIPELINE_TEMPLATES_PATH` to point at these folders.
Variables already set in your environment take precedence for the AliceVision resource files (`ALICEVISION_ROOT`, `ALICEVISION_SENSOR_DB`, `ALICEVISION_VOCTREE`, ...), so unset them if they point to another AliceVision installation.

The command-line tools work the same way, for instance for a headless run:

```bash
./meshroom_batch -p photogrammetry -i /path/to/images -o /path/to/output
```

On Windows, no Visual C++ Redistributable is needed: the MSVC runtime is shipped in the archive.

### Meshroom-only archive

The Meshroom-only archive does not provide any photogrammetry node. To use it with AliceVision, either:

* set up AliceVision and QtAliceVision through environment variables, as described in [INSTALL.md](INSTALL.md#alicevision) (`ALICEVISION_ROOT`, `MESHROOM_NODES_PATH`, `MESHROOM_PIPELINE_TEMPLATES_PATH`, `QML2_IMPORT_PATH`, `QT_PLUGIN_PATH`);
* or reproduce the layout of the full archive by placing the AliceVision and QtAliceVision installs in `aliceVision/` and `qtPlugins/` next to the `Meshroom` executable.

Use the AliceVision and QtAliceVision nightlies listed in the release notes: the binaries are built against these exact versions, and other versions may be incompatible.
The AliceVision nightlies are published on [AliceVision](https://github.com/alicevision/AliceVision/releases/tag/nightly) and [QtAliceVision](https://github.com/alicevision/QtAliceVision/releases/tag/nightly).

Plugins (see [INSTALL_PLUGINS.md](INSTALL_PLUGINS.md)) are installed in the `plugins/` folder created next to the executable, with either archive.

## System requirements

* **Windows**: 64-bit Windows 10 or later.
* **Linux**: x86_64, built on Ubuntu 22.04: use a distribution at least as recent (glibc 2.35 or later). Qt needs the usual X11/OpenGL system libraries; on Debian/Ubuntu, if Meshroom fails to start with a Qt platform plugin error, install:
  ```bash
  sudo apt-get install libgl1 libegl1 libopengl0 libfontconfig1 libglib2.0-0 libdbus-1-3 \
    libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxkbcommon-x11-0
  ```
* A CUDA-capable NVIDIA GPU is required by some AliceVision nodes (e.g. depth map computation), as in official releases.

## Reporting issues

When reporting a problem found with a nightly, open a [GitHub issue](https://github.com/alicevision/Meshroom/issues) and include:
* the archive name (it contains the build date and commit);
* the AliceVision and QtAliceVision nightly versions listed in the release notes, if the issue involves AliceVision nodes or the viewers;
* your OS and GPU.

Before reporting, check whether the issue is still present in the latest nightly: it is replaced at least once a day when `develop` changes.

## How the nightly is built

This section is for maintainers. The nightly is built by [.github/workflows/nightly.yml](.github/workflows/nightly.yml): it checks every hour whether `develop`, the AliceVision nightly or the QtAliceVision nightly changed, and rebuilds when needed (at most once a day for `develop` changes).

Each build ([.github/workflows/build-binary.yml](.github/workflows/build-binary.yml)) freezes Meshroom with cx_Freeze, using the Python interpreter shipped with the AliceVision nightly, then adds AliceVision and QtAliceVision to create the full archive. The release is only updated when both the Windows and Linux builds succeed.

The workflow can also be run manually from the Actions tab. On a branch other than `develop`, it builds the archives (kept as workflow artifacts for one day) without publishing them, which is how to test changes to the build.
