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
  - **`url`** (required): the url to download the asset from.
  - **`path`** (required): the file path of the asset, relative to the plugin root folder.
  - **`sha256`** (optional, recommended): the SHA-256 checksum of the asset.

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

## Plugin Menus

A plugin can declare custom menus for the Meshroom UI with a `menu.py` file at the root of its `meshroom` folder. The file is executed when the plugin is loaded, and registers its menus with `MeshroomMenuManager`:

```python
from meshroom.ui.menu import Menu, MenuCallback, MeshroomMenuManager


class OpenSettings(MenuCallback):
    def __call__(self, menu, app, **kwargs):
        ...


menu = Menu("My Plugin")
menu.addButton("Open Settings", callback=OpenSettings())
MeshroomMenuManager.registerMenu(menu)
```

A `menu.py` file can register several menus. Within a menu, entries are identified by their name: two entries (or two items of a radio button) cannot share a name or a label. The optional `index` argument inserts an entry, or a top-level menu, at a given position instead of appending it. Callbacks must be callables (a function or a `MenuCallback` instance), called with the menu, the `MeshroomApp` and context-dependent keyword arguments (`enabled` for checkboxes, `selected` for radio buttons).

Sub-menus (radio buttons included) can be nested up to 2 levels below a menu of the menu bar: deeper ones are displayed disabled, without their content, and a warning is logged. Characters of a label that no installed font can display (e.g. emojis without an emoji font) are removed from it.

Only the `menu.py` file at the root of the `meshroom` folder is reserved: a `menu.py` in a subfolder is loaded like any other module.

Menus are only loaded when Meshroom runs with its graphical interface: the file is ignored by the command-line tools (`meshroom_batch`, `meshroom_compute`).

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
