__version__ = "2018.1"

from enum import Enum

class Backend(Enum):
    STANDALONE = 1
    PYSIDE = 2

backend = Backend.STANDALONE

def useUI():
    global backend
    backend = Backend.PYSIDE

