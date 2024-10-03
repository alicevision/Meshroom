

import os
from meshroom.core.plugin import PluginNode, PluginCommandLineNode, EnvType

#Python nodes

class DummyConda(PluginNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.CONDA
    envFile = os.path.join(os.path.dirname(__file__), "env.yaml")

    inputs = []
    outputs = []

    def processChunk(self, chunk):
        import numpy as np
        chunk.logManager.start("info")
        chunk.logger.info(np.abs(-1))

class DummyDocker(PluginNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.DOCKER
    envFile = os.path.join(os.path.dirname(__file__), "Dockerfile")

    inputs = []
    outputs = []

    def processChunk(self, chunk):
        import numpy as np
        chunk.logManager.start("info")
        chunk.logger.info(np.abs(-1))


class DummyVenv(PluginNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.VENV
    envFile = os.path.join(os.path.dirname(__file__), "requirements.txt")

    inputs = []
    outputs = []

    def processChunk(self, chunk):
        import numpy as np
        chunk.logManager.start("info")
        chunk.logger.info(np.abs(-1))

class DummyPip(PluginNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.PIP
    envFile = os.path.join(os.path.dirname(__file__), "requirements.txt")

    inputs = []
    outputs = []

    def processChunk(self, chunk):
        import numpy as np
        chunk.logManager.start("info")
        chunk.logger.info(np.abs(-1))

class DummyNone(PluginNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.NONE
    envFile = None

    inputs = []
    outputs = []

    def processChunk(self, chunk):
        import numpy as np
        chunk.logManager.start("info")
        chunk.logger.info(np.abs(-1))

class DummyRez(PluginNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.REZ
    envFile = "numpy"

    inputs = []
    outputs = []

    def processChunk(self, chunk):
        import numpy as np
        chunk.logManager.start("info")
        chunk.logger.info(np.abs(-1))

#Command line node
        
class DummyCondaCL(PluginCommandLineNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.CONDA
    envFile = os.path.join(os.path.dirname(__file__), "env.yaml")

    inputs = []
    outputs = []

    commandLine = "python -c \"import numpy as np; print(np.abs(-1))\""

class DummyDockerCL(PluginCommandLineNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.DOCKER
    envFile = os.path.join(os.path.dirname(__file__), "Dockerfile")

    inputs = []
    outputs = []

    commandLine = "python -c \"import numpy as np; print(np.abs(-1))\""


class DummyVenvCL(PluginCommandLineNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.VENV
    envFile = os.path.join(os.path.dirname(__file__), "requirements.txt")

    inputs = []
    outputs = []

    commandLine = "python -c \"import numpy as np; print(np.abs(-1))\""
  
class DummyPipCL(PluginCommandLineNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.PIP
    envFile = os.path.join(os.path.dirname(__file__), "requirements.txt")

    inputs = []
    outputs = []

    commandLine = "python -c \"import numpy as np; print(np.abs(-1))\""

class DummyNoneCL(PluginCommandLineNode):

    category = 'Dummy'
    documentation = ''' '''

    envType = EnvType.NONE
    envFile = None

    inputs = []
    outputs = []

    commandLine = "python -c \"import numpy as np; print(np.abs(-1))\""