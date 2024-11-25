#!/usr/bin/env python
# coding:utf-8
""" Test for Meshroom Plugins.
"""
# STD
import os
import shutil
import tempfile

# Internal
from meshroom.core import _plugins
from meshroom.core import desc, registerNodeType, unregisterNodeType
from meshroom.core.graph import Graph
from meshroom.core.node import Node, IncompatiblePluginNode


class SampleNode(desc.Node):
    """ Sample Node for unit testing """

    category = "Sample"

    inputs = [
        desc.File(name='input', label='Input', description='', value='',),
        desc.StringParam(name='paramA', label='ParamA', description='', value='', invalidate=False)  # No impact on UID
    ]
    outputs = [
        desc.File(name='output', label='Output', description='', value=desc.Node.internalFolder)
    ]


def test_plugin_management():
    """ Tests the plugin manager for registering and unregistering node.
    """
    # Sample Node name
    name = SampleNode.__name__

    # Register the node
    registerNodeType(SampleNode)

    # Since the Node Plugin Manager is a singleton instance
    # We should still be able to instantiate and have a look at out registered plugins directly
    pluginManager = _plugins.NodePluginManager()

    # Assert that the plugin we have registered above is indeed registered
    assert pluginManager.registered(name)

    # Assert that the plugin can only be registered once
    assert not pluginManager.registerNode(SampleNode)

    # And once un-registered, it should no longer be present in the pluginManager
    unregisterNodeType(SampleNode)

    # Assert that the plugin we have registered above is indeed registered
    assert not pluginManager.registered(name)
    assert name not in pluginManager.descriptors


def test_descriptor():
    """ Tests the Descriptor and NodeDescriptor instances.
    """
    # Register the node
    registerNodeType(SampleNode)

    # Since the Node Plugin Manager is a singleton instance
    # We should still be able to instantiate and have a look at out registered plugins directly
    pluginManager = _plugins.NodePluginManager()

    # Assert the descriptor is same as the Plugin NodeType
    assert pluginManager.descriptor(SampleNode.__name__).__name__ == SampleNode.__name__

    # Assert that the category of the NodeDescriptor is correct for the registered plugin
    assert pluginManager.descriptors.get(SampleNode.__name__).category == "Sample"

    # Finally unregister the plugin
    unregisterNodeType(SampleNode)


def _setup_temp_package(directory, name):
    """ Sets up a temporary meshroom package structure which can be loaded as plugins.
    """
    package = os.path.join(directory, name)

    # Create the base package in the directory
    os.makedirs(package)

    # The very first file that we need is probably empty __init__.py
    init = os.path.join(package, "__init__.py")

    # The second thing we need is a directory inside
    packageDir = os.path.join(package, "TesingPackage")

    # Third would be another init for the package
    packinit = os.path.join(packageDir, "__init__.py")

    # Then comes the main module which will hold the plugin
    pluginMod = os.path.join(packageDir, "TestInput.py")

    # Now start constructing stuff here
    os.makedirs(packageDir)

    with open(init, "w") as f:
        f.write("__version__ =\"1.0\"")

    with open(packinit, "w") as f:
        f.write("__version__ =\"1.0\"")

    contents = """
from meshroom.core import desc


class SampleTroubledNode(desc.Node):
    \""" Sample Node for unit testing a reload process.
        Defaults to having an invalid input param value. Which gets updated later on.
    \"""

    category = "Sample"

    inputs = [
        # A Float param having the value as a string will cause the plugin to be loaded in an Error state
        desc.FloatParam(name='paramA', label='ParamA', description='', value='4.0')
    ]
    outputs = [
        desc.File(name='output', label='Output', description='', value=desc.Node.internalFolder)
    ]
    """

    with open(pluginMod, "w") as f:
        f.write(contents)

    return package

def _correctify_plugin(pluginPath):
    contents = """
from meshroom.core import desc


class SampleTroubledNode(desc.Node):
    \""" Sample Node for unit testing a reload process.
        Defaults to having an invalid input param value. Which gets updated later on.
    \"""

    category = "Sample"

    inputs = [
        # A Float param having the value as a string will cause the plugin to be loaded in an Error state
        desc.FloatParam(name='paramA', label='ParamA', description='', value=4.0)
    ]
    outputs = [
        desc.File(name='output', label='Output', description='', value=desc.Node.internalFolder)
    ]
    """

    with open(pluginPath, "w") as f:
        f.write(contents)


def _cleaup_package(directory):
    """ Cleans up the Package
    """
    shutil.rmtree(directory)

def test_reload_with_graph():
    """ Tests Reloading of a plugin and how does the change propagate to a graph.
    """
    # Create a temp directory
    directory = tempfile.mkdtemp()

    package = _setup_temp_package(directory, "MTest")

    # Since the Node Plugin Manager is a singleton instance
    # We should still be able to instantiate and have a look at out registered plugins directly
    pluginManager = _plugins.NodePluginManager()

    pluginManager.load(package)

    # Sample Node name
    name = "SampleTroubledNode"

    # Assert that the plugin we have registered above is indeed registered
    assert pluginManager.registered(name)

    # But the status of the plugin would be errored
    assert pluginManager.status(name) == _plugins.Status.ERRORED

    # Graph for usage
    g = Graph("")

    # Create Nodes in the Graph
    n = g.addNewNode(name)

    # Assert that the node is of an Incompatible Plugin type as the plugin had errors while loading
    assert isinstance(n, IncompatiblePluginNode)

    descriptor = pluginManager.descriptors.get(name)
    # Test that the plugin would not get reloaded
    # unless either the source has been modified or the plugin is forced to be loaded
    assert not descriptor.reload()

    # Modify the Source of the Troubled Node before we reload the plugin
    # This updates the source of the plugin and ensures that the plugin can now be loaded as expected
    _correctify_plugin(os.path.join(package, "TesingPackage", "TestInput.py"))

    # Reload the plugin as the source has been modified
    assert descriptor.reload()

    # Now the plugin has been reloaded
    assert pluginManager.status(name) == _plugins.Status.LOADED

    # Now reload the nodes of the provided type in the graph
    g.reloadNodes(name)

    # Get all the nodes and assert that they have been upgraded to Standard Nodes
    for node in g.nodesOfType(name):
        assert isinstance(node, Node)

    # Once the tests are concluded -> Cleanup
    _cleaup_package(package)
