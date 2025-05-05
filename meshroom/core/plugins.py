from pathlib import Path

from meshroom.common import BaseObject

class ProcessEnv(BaseObject):
    """
    Describes the environment required by a node's process.
    """

    def __init__(self, folder: str):
        super().__init__()
        self.binPaths: list = [Path(folder, "bin")]
        self.libPaths: list = [Path(folder, "lib"), Path(folder, "lib64")]
        self.pythonPathFolders: list = [Path(folder)] + self.binPaths
