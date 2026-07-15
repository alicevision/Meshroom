import os

from meshroom.core import pluginManager


pluginManager.addPluginFromBuiltInFolder("testNodes", os.path.join(os.path.dirname(__file__), "nodes"))

if os.getenv("MESHROOM_PIPELINE_TEMPLATES_PATH", False):
    os.environ["MESHROOM_PIPELINE_TEMPLATES_PATH"] += os.pathsep + os.path.dirname(os.path.realpath(__file__))
else:
    os.environ["MESHROOM_PIPELINE_TEMPLATES_PATH"] = os.path.dirname(os.path.realpath(__file__))
