# Meshroom plugins installation

Plugins are collections of nodes and templates with their own dependencies. While plugin maintainers have flexibility in organizing their code, Meshroom requires a specific structure for proper integration.

## Required Structure

- **Meshroom folder**: All plugin nodes and templates must be placed within a `meshroom/` directory
- **Configuration file**: Optional `config.json` file for environment variables, placed in the `meshroom/` folder  
- **Virtual environment**: If using a virtual environment (recommended), it must have the same name as the plugin directory.

## Example Structure

For a plugin named "customPlugin", Meshroom expects this layout:
```
├── customPlugin/                # Plugin root folder
│   ├── meshroom/                # Meshroom nodes and pipelines
│   │   ├── customNodes1/        # Set of nodes
│   │   │   ├── __init__.py      # Required to be a python module
│   │   │   ├── NodeA.py
│   │   │   ├── NodeB.py
│   │   ├── customNodes2/        # Another set of nodes if needed
│   │   │   ├── __init__.py
│   │   │   ├── NodeC.py
│   │   │   ├── NodeD.py
│   │   ├── customTemplate1.mg   # Ready-to-use pipeline templates
│   │   ├── customTemplate2.mg
│   │   ├── config.json          # Optional plugin configuration file
│   ├── customPlugin/            # Optional virtual environment with installed dependencies
│   └── ...                      # Custom code (any structure)
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
