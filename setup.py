import sys

import setuptools  # for bdist
from cx_Freeze import setup, Executable


build_exe_options = {
    # include dynamically loaded plugins
    "packages": ["meshroom.nodes", "meshroom.submitters"]
}

meshroomExe = Executable(
    "meshroom/ui/__main__.py",
    targetName="Meshroom",
)

# Customize executable for each target platform
if sys.platform.startswith("win32"):
    # meshroomExe.base = "Win32GUI"  # for no-console version
    meshroomExe.targetName += ".exe"
    meshroomExe.icon = "meshroom/ui/img/meshroom.ico"
elif sys.platform.startswith("darwin"):
    meshroomExe.targetName += ".app"
    # TODO: icon for Mac

setup(
    name="Meshroom",
    description="Meshroom",
    install_requires=['psutil', 'pytest', 'PySide2'],
    extras_require={
        ':python_version < "3.4"': [
            'enum34',
        ],
    },
    version="1.0",  # TODO: get correct version info
    options={"build_exe": build_exe_options},
    executables=[meshroomExe],
)
