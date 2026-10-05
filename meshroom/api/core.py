# -*- coding: utf-8 -*-

"""
Functions that are designed to provide a simple interface
to Meshroom plugins.
"""

import logging
from typing import Union
import meshroom
from meshroom.core import pluginManager


LOGGER = logging.getLogger("MeshroomApi")


def setLoglevel(level: Union[int, str]):
    if isinstance(level, str):
        level = logging._nameToLevel.get(level.upper(), None)
    if not isinstance(level, int):
        LOGGER.warning(f"Cannot set level {level} : not an integer.")
        return
    logging.getLogger().setLevel(level)
    levelName = logging.getLevelName(int(level))
    LOGGER.info(f"Meshroom log level has been set to {levelName}.")


def initialize(plugins=False, rezPlugins=False, nodes=False, submitters=False, pipelines=False):
    if plugins:
        meshroom.core.initPlugins()
    if rezPlugins:
        meshroom.core.initRezPlugins()
    if nodes:
        meshroom.core.initNodes()
        nodes = pluginManager.getRegisteredNodePlugins()
        LOGGER.info(f"{len(nodes)} Registered NodePlugins")
        for n in nodes.values():
            LOGGER.info(f"Registered NodePlugin {n.nodeDescriptor.__module__}")
    if submitters:
        meshroom.core.initSubmitters()
    if pipelines:
        meshroom.core.initPipelines()


def listPlugins():
    plugins = pluginManager.getPlugins()
    return plugins


def registerPlugin(plugin):
    pluginManager.addPlugin(plugin, registerNodePlugins=True)
    LOGGER.info(f"Register Plugin {plugin.name}")


def unregisterPlugin(name):
    plugin = pluginManager.getPlugin(name)
    if not plugin:
        LOGGER.warning(f"No Plugin named {name}")
        return
    LOGGER.info(f"Unregister Plugin {plugin.name}")
    pluginManager.removePlugin(plugin)


def listNodes():
    nodes = pluginManager.getRegisteredNodePlugins()
    return nodes


def registerNode(nodePlugin):
    pluginManager.registerNode(nodePlugin)
    LOGGER.info(f"Register NodePlugin {nodePlugin.nodeDescriptor.__module__}")


def unregisterNode(name):
    node = pluginManager.getRegisteredNodePlugin(name)
    if not node:
        LOGGER.warning(f"No NodePlugin named {name}")
        return
    LOGGER.info(f"Unregister NodePlugin {node.nodeDescriptor.__module__}")
    pluginManager.unregisterNode(node)
