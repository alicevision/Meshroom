# Intro

A plugin is a set of one or several nodes that are not part of the Meshroom/Alicevision main project.
They are meant to facilitate the creation of custom pipeline, make distribution and installation of extra nodes easy, and allow the use of different level of isolation at the node level.
Each node within a plugin may use the same or differents environnement.

# Making Meshroom Plugins

To make a new plugin, make your node inheriting from `meshroom.core.plugins.PluginNode`
In your new node class, overwrite the variable `envFile` to point to the environment file (e.g. the `yaml` or `dockerfile`) that sets up your installation, end `envType` to specify the type of plugin. The path to this file should be relative to the path of the node, and within the same folder (or subsequent child folder) as the node definition.

The code in `processChunk` in your node definition will be automatically executed within the envirenoment, using `meshroom_compute`.
A new status `FIRST_RUN` denotes the stage in between the environement startup and the execution of the node. 

Make sur your imports are lazy, in `processChunk`.
Several nodes share the same environment as long as they point to the same environment file. 
Changing this file will trigger a rebuild on the environment.

You may install plugin from a git repository or from a local folder. In the later case, you may edit the code directly from your source folder.

By default, Meshroom will look for node definition in `[plugin folder]/meshroomNodes` and new pipelines in `[plugin folder]/meshroomPipelines` and assumes only one environement is needed.

To modify this behavior, you may put a json file named `meshroomPlugin.json` at the root of your folder/repository.
The file must have the following structure:
```
[
	{
	"pluginName":"[YOUR_PLUGIN_NAME]",
        "nodesFolder":"[YOUR_FOLDER_RELATIVE_TO_THE_ROOT_REPO_OR_FOLDER],
        "pipelineFolder":"[YOUR_CUSTOM_PIEPILINE_FOLDER"
	},
	{
	"pluginName":"Dummy Plugin",
        "nodesFolder":"dummy"
	}
]
```

The environment of the nodes are going to be build the first time it is needed (status will be `BUILD`, in purple).

