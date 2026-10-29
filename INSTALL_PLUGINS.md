# Meshroom plugins installation

Plugins are collections of nodes and templates with their own dependencies. Plugin maintainers have flexibility in organizing their code, as Meshroom only requires a few directories to recognize nodes and pipelines.

## Required Structure

- **Meshroom folder**: All plugin nodes and templates must be placed within a `./meshroom/` directory.
- **Metadata file (optional)**: A `./pyproject.toml` file defines the plugin's name, version, publisher and custom environment variables (see [Plugin Metadata](#plugin-metadata)).
- **Virtual environment (optional)**: If you have specific dependencies, you can create a virtual environment named "venv" in a folder and this Python will be used when computing the node.

## Example Structure

For a plugin named "customPlugin", Meshroom expects this layout:
```
├── customPlugin/                # Plugin root folder
│   ├── meshroom/                # Meshroom nodes and pipelines
│   │   ├── customNodes1/        # Set of nodes
│   │   │   ├── __init__.py      # Required to be a python module
│   │   │   ├── NodeA.py
│   │   │   ├── NodeB.py
│   │   ├── customNodes2/        # Another set of standalone nodes
│   │   │   ├── NodeC.py
│   │   │   ├── NodeD.py
│   │   ├── customTemplate1.mg   # Ready-to-use pipeline templates
│   │   ├── customTemplate2.mg
│   ├── pyproject.toml           # Optional plugin metadata and dependencies
│   ├── venv/                    # Optional virtual environment with installed dependencies
│   └── ...                      # Custom code (any structure)
```

## Plugin Metadata

The plugin's metadata is read from `pyproject.toml`, at the root of the plugin:
- `name`, `version`, `description`, `authors` and the license come from the standard `[project]` table.
- `publisher`, `requirements`, `env` and `assets` come from the Meshroom-specific `[tool.meshroom]` table.

```toml
[project]
name = "customPlugin"
version = "1.0.0"
description = "What the plugin does."
authors = [ {name = "Jane Doe"} ]
license = "MIT"
dependencies = ["numpy"]

[tool.meshroom]
publisher = "myPublisher"
requirements = "CUDA >= X.X"
env = [
    { key = "MY_VAR", type = "string", value = "myValue" },
    { key = "MY_PATH", type = "path", value = "relativeOrAbsolutePath" },
]

[[tool.meshroom.assets]]
name = "myWeights"
category = "model"
url = "https://example.com/path/to/weights.pt"
path = "models/weights.pt"
sha256 = "eefe175fb7c1c605de5c351ef12271f52663874ea3a01cae75f767201f1fe0c3"

[[tool.meshroom.assets]]
name = "myTool"
category = "binary"
release = "myPublisher/myTool@v1.0.0"
path = "myTool"
```

All the fields are optional:
- **`name`**: the name of the plugin.
- **`version`**: the version of the plugin.
- **`publisher`**: the publisher of the plugin.
- **`requirements`**: a human-readable description of what the plugin needs to run (e.g. hardware requirements). It is only displayed.
- **`license`**: the license of the plugin.
- **`env`**: environment variables set when computing the plugin's nodes. A relative `path` value is resolved against the plugin root folder.
- **`assets`**: external files (models, weights, data...) downloaded into the plugin folder when the plugin is installed or updated as a local plugin. Each asset has:
  - **`name`** (required): the name of the asset, unique within the plugin.
  - **`category`** (required): a free-form label describing the kind of asset (e.g. `model`, `weights`, `data`).
  - **`url`** (required, unless `release` is set): the url to download the asset from. The file is kept as is, it is
    not extracted.
  - **`release`**: instead of `url`, a GitHub release, as `<owner>/<repository>@<tag>`. The file of the release
    to install is chosen for the user's platform, from its name, which should follow the convention
    `<name>-<version>-<os>-<arch>[-<extras>].<ext>`:
    - `<os>`: `linux`, `windows` or `macos` (`win64`, `darwin` and `osx` are also recognized);
    - `<arch>`: `x86_64` or `arm64` (`amd64`, `x64` and `aarch64` are also recognized); a file without it is
      used when no file of the release names the architecture of the user's machine;
    - `<extras>`: free (e.g. `cu128`), ignored to choose the file.

    e.g. `myTool-1.0.0-linux-x86_64-cu128.tar.gz` and `myTool-1.0.0-windows-x86_64-cu128.zip`. The release must
    have a single file per platform: several files matching the user's platform is an error. A release with a
    single file that names no operating system is used on every platform (e.g. model weights).
    The file is checked against the SHA-256 published by GitHub. A `.zip`, `.tar`, `.tar.gz`,
    `.tgz`, `.tar.bz2` or `.tar.xz` archive is extracted in `path`, its single root folder unwrapped, keeping the
    executable permissions of its files; links pointing outside of the archive are skipped.
  - **`path`** (required): the path of the asset, relative to the plugin root folder: the file, or the folder an
    archive from a release is extracted in.
  - **`sha256`** (optional, recommended, only with `url`): the SHA-256 checksum of the asset.
  - **`executable`** (optional, default `false`): make the downloaded file executable (archives keep the
    permissions of their files).

### Legacy `config.json`

Plugins without a `pyproject.toml` can still use a `./meshroom/config.json` file, in one of two formats:

- A plain list of environment variable entries:
  ```json
  [
      { "key": "MY_VAR", "type": "string", "value": "myValue" },
      { "key": "MY_PATH", "type": "path", "value": "relativeOrAbsolutePath" }
  ]
  ```
- An object with optional `name`, `version`, `publisher`, `authors`, `description`, `requirements`, `env` and `assets` keys, `env` using the same entry format as above:
  ```json
  {
      "name": "customPlugin",
      "version": "1.0.0",
      "env": [
          { "key": "MY_VAR", "type": "string", "value": "myValue" }
      ]
  }
  ```

In `config.json`, a relative `path` value is resolved against the `meshroom` folder, not the plugin root folder.

## Installing a Plugin

A plugin can be installed in one of three ways:

- **Local plugin**: install it from a plugin registry with the `meshroom_plugins` command line tool.
  ```
  meshroom_plugins registry add https://example.com/path/to/myRegistry.json
  meshroom_plugins install customPlugin
  ```
  Local plugins and registry files live in the `plugins` folder of the Meshroom installation: the repository root when running from sources, next to the Meshroom executable in a release. Set `MESHROOM_LOCAL_PLUGINS_PATH` to use another folder. Any plugin folder copied there is loaded as a local plugin.
- **Plugin folder**: add the plugin root folder to the `MESHROOM_PLUGINS_PATH` environment variable (`;`-separated on Windows, `:`-separated on Linux).
  ```
  export MESHROOM_PLUGINS_PATH=/path/to/customPlugin:$MESHROOM_PLUGINS_PATH
  ```
- **Rez package**: add a `<package>-<version>=<packageRootPath>` entry to the `MESHROOM_REZ_PLUGINS` environment variable.
  ```
  export MESHROOM_REZ_PLUGINS=customPlugin-1.0.0=/path/to/customPlugin/1.0.0
  ```
