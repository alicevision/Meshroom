""" Test for Meshroom Plugins.
"""
#!/usr/bin/env python
# coding:utf-8

from meshroom.core import _plugins
from meshroom.core import desc, registerNodeType, unregisterNodeType


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
