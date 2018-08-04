import sys

import setuptools  # for bdist
from cx_Freeze import setup, Executable
import meshroom

build_exe_options = {
    # include dynamically loaded plugins
    "packages": ["meshroom.nodes", "meshroom.submitters"],
    "include_files": ['COPYING.md']
}

meshroomExe = Executable(
    "meshroom/ui/__main__.py",
    targetName="Meshroom",
)

meshroomPhotog = Executable(
    "bin/meshroom_photogrammetry"
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
    install_requires=['psutil', 'pytest', 'PySide2', 'markdown'],
    extras_require={
        ':python_version < "3.4"': [
            'enum34',
        ],
    },
    setup_requires=[
        'cx_Freeze'
    ],
    version=meshroom.__version__,
    options={"build_exe": build_exe_options},
    executables=[meshroomExe, meshroomPhotog],
)
