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
- `name`, `version`, `description` and `authors` come from the standard `[project]` table.
- `publisher`, `requirements` and `env` come from the Meshroom-specific `[tool.meshroom]` table.

```toml
[project]
name = "customPlugin"
version = "1.0.0"
description = "What the plugin does."
authors = [ {name = "Jane Doe"} ]
dependencies = ["numpy"]

[tool.meshroom]
publisher = "myPublisher"
requirements = "CUDA >= X.X"
env = [
    { key = "MY_VAR", type = "string", value = "myValue" },
    { key = "MY_PATH", type = "path", value = "relativeOrAbsolutePath" },
]
```

All the fields are optional:
- **`name`**: the name of the plugin.
- **`version`**: the version of the plugin.
- **`publisher`**: the publisher of the plugin.
- **`requirements`**: a human-readable description of what the plugin needs to run (e.g. hardware requirements). It is only displayed.
- **`env`**: environment variables set when computing the plugin's nodes. A relative `path` value is resolved against the plugin root folder.

### Legacy `config.json`

Plugins without a `pyproject.toml` can still use a `./meshroom/config.json` file, in one of two formats:

- A plain list of environment variable entries:
  ```json
  [
      { "key": "MY_VAR", "type": "string", "value": "myValue" },
      { "key": "MY_PATH", "type": "path", "value": "relativeOrAbsolutePath" }
  ]
  ```
- An object with optional `name`, `version`, `publisher`, `authors`, `description`, `requirements` and `env` keys, `env` using the same entry format as above:
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
- **Plugin folder**: add the plugin root folder to the `MESHROOM_PLUGINS_PATH` environment variable (`;`-separated on Windows, `:`-separated on Linux).
  ```
  export MESHROOM_PLUGINS_PATH=/path/to/customPlugin:$MESHROOM_PLUGINS_PATH
  ```
- **Rez package**: add a `<package>-<version>=<packageRootPath>` entry to the `MESHROOM_REZ_PLUGINS` environment variable.
  ```
  export MESHROOM_REZ_PLUGINS=customPlugin-1.0.0=/path/to/customPlugin/1.0.0
  ```
