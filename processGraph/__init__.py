from .Graph import *
from . import desc

import os
import sys
import re
import inspect
import importlib
import json

cacheFolder = '/tmp/processGraphCache'
nodesDesc = {}


def loadNodesDesc(folder, package='nodes'):
    '''
    '''
    global nodesDesc

    pysearchre = re.compile('.py$', re.IGNORECASE)
    pluginfiles = filter(pysearchre.search,
                           os.listdir(os.path.join(folder,
                                                 package)))
    # import parent module
    importlib.import_module(package)
    nodeTypes = []
    errors = []
    for pluginFile in pluginfiles:
        if pluginFile.startswith('__'):
            continue

        try:
            pluginName = os.path.splitext(pluginFile)[0]
            module = '.' + pluginName
            m = importlib.import_module(module, package=package)
            p = [a for a in m.__dict__.values() if inspect.isclass(a) and issubclass(a, desc.Node)]
            if not p:
                raise RuntimeError('No class defined in plugin: %s' % module)
            nodeTypes.extend(p)
        except Exception as e:
            errors.append('  * Errors while loading "{}".\n    File: {}\n    {}'.format(pluginName, pluginFile, str(e)))


    nodesDesc = dict([(m.__name__, m) for m in nodeTypes])
    print('Plugins loaded: ', ', '.join(nodesDesc.keys()))
    if errors:
        print('== Error while loading the following plugins: ==')
        print('\n'.join(errors))
        print('================================================')

    return nodeTypes

# Load plugins
loadNodesDesc(folder=os.path.dirname(os.path.dirname(__file__)))

