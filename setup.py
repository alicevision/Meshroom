import sys

import setuptools  # for bdist
from cx_Freeze import setup, Executable


def getExecutableExtension():
    """ Return file extension for an executable program based on current platform. """
    if sys.platform == "win32":
        return ".exe"
    if sys.platform == "darwin":
        return ".app"
    return ""


build_exe_options = {
    # include dynamically loaded plugins
    "packages": ["meshroom.nodes", "meshroom.submitters"]
}

executables = [
    Executable(
        "meshroom/ui/__main__.py",
        targetName="Meshroom" + getExecutableExtension(),
    ),
]

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
    executables=executables,
)
