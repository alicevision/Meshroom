import logging
import os

from meshroom.core.graph import Graph

logging = logging.getLogger(__name__)

def test_pluginNodes():
    if "CI" in os.environ:
        return 
    graph = Graph('')
    graph.addNewNode('DummyCondaNode')
    graph.addNewNode('DummyDockerNode')
    graph.addNewNode('DummyPipNode')
    graph.addNewNode('DummyVenvNode')
    
  