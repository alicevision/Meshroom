from enum import Enum  # available by default in python3. For python2: "pip install enum34"

class Backend(Enum):
    STANDALONE = 1
    PYSIDE = 2

backend = Backend.STANDALONE

def useUI():
	global backend
	backend = Backend.PYSIDE

