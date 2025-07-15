import os
import sys
import zipimport

FILE_NAME = sys.executable
DIR_NAME = os.path.dirname(sys.executable)

paths = os.environ.get("ALICEVISION_LIBPATH", "").split(os.pathsep)
if DIR_NAME not in paths:
    paths.insert(0, DIR_NAME)
    paths.insert(0, os.path.join(DIR_NAME, "lib"))
    paths.insert(0, os.path.join(DIR_NAME, "aliceVision", "lib"))
    paths.insert(0, os.path.join(DIR_NAME, "aliceVision", "bin"))
    #paths.insert(0, os.path.join(DIR_NAME, "lib", "PySide6", "Qt", "qml", "QtQuick", "Dialogs"))

    os.environ["ALICEVISION_LIBPATH"] = os.pathsep.join(paths)
    os.environ["PYTHONPATH"] = os.path.join(DIR_NAME, "aliceVision", "lib", "python")
    os.execv(sys.executable, sys.argv)

sys.frozen = True
sys.path = sys.path[:5]

def run(*args):
    m = __import__("__main__")
    importer = zipimport.zipimporter(DIR_NAME + "/lib/library.zip")
    if len(args) == 0:
        name, ext = os.path.splitext(os.path.basename(os.path.normcase(FILE_NAME)))
        moduleName = "%s__main__" % name
    else:
        moduleName = args[0]
    sys.path.append(os.getenv("PYTHONPATH", ""))
    code = importer.get_code(moduleName)
    exec(code, m.__dict__)
