# Meshroom plugins installation

Plugins are collections of nodes and templates with their own dependencies. The hierarchy of plugins is up to their
maintainers, but Meshroom expects the following:
- All the plugin's nodes and templates should be placed within a `meshroom` folder;
- If a configuration file containing environment variables to set with their values is provided, it should be named `config.json` and placed in the `meshroom` folder;
- If the plugin's dependencies are installed through a virtual environment (highly recommended), the virtual environment name should be identical to the plugin's.

Plugins should be provided to Meshroom through the `MESHROOM_PLUGINS_PATH` environment variable.

For example, for a given plugin "customPlugin", Meshroom would expect the following structure:
```
├── folderA
│   ├── customPlugin
│   │   ├── customPlugin <- virtual environment containing the installed dependencies
│   │   ├── meshroom
│   │   │   ├── customNodes1 <- Python module containing a set of nodes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── NodeA.py
│   │   │   │   ├── NodeB.py
│   │   │   ├── customNodes2 <- Python module containing a set of nodes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── NodeC.py
│   │   │   │   ├── NodeD.py
│   │   │   ├── customTemplate1.mg
│   │   │   ├── customTemplate2.mg
│   │   │   ├── config.json <- configuration file for the plugin
│   │   ├── anyFolder
│   │   ├── anyFile.txt
├── folderB
```

"customPlugin" would be loaded upon Meshroom's launch by specifying:
- On Windows:
  ```
  set MESHROOM_PLUGINS_PATH=/path/to/folderA/customPlugin;%MESHROOM_PLUGINS_PATH%
  ```
- On Linux:
  ```
  export MESHROOM_PLUGINS_PATH=/path/to/folderA/customPlugin:$MESHROOM_PLUGINS_PATH
  ```