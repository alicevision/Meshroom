# Meshroom plugins installation

Plugins are collections of nodes and templates with their own dependencies. Plugin maintainers have flexibility in organizing their code, as Meshroom only requires a few directories to recognize nodes and pipelines.

## Required Structure

- **Meshroom folder**: All plugin nodes and templates must be placed within a `./meshroom/` directory
- **Configuration file (optional)**: `./meshroom/config.json` file allows to define the plugin's name, version and custom environment variables
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
│   │   ├── config.json          # Optional plugin configuration file
│   ├── venv/                    # Optional virtual environment with installed dependencies
│   └── ...                      # Custom code (any structure)
```

## Configuration File

`config.json` can be written in two formats:

- A plain list of environment variable entries:
  ```json
  [
      { "key": "MY_VAR", "type": "string", "value": "myValue" },
      { "key": "MY_PATH", "type": "path", "value": "relativeOrAbsolutePath" }
  ]
  ```
- An object with optional `name`, `version`, and `env` keys, `env` using the same entry format as above:
  ```json
  {
      "name": "customPlugin",
      "version": "1.0.0",
      "env": [
          { "key": "MY_VAR", "type": "string", "value": "myValue" }
      ]
  }
  ```

## Loading the Plugin

The "customPlugin" will be loaded automatically when Meshroom starts by setting the `MESHROOM_PLUGINS_PATH` environment variable:
- On Windows:
  ```
  set MESHROOM_PLUGINS_PATH=/path/to/customPlugin;%MESHROOM_PLUGINS_PATH%
  ```
- On Linux:
  ```
  export MESHROOM_PLUGINS_PATH=/path/to/customPlugin:$MESHROOM_PLUGINS_PATH
  ```
