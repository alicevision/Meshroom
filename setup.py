import platform

import os
import setuptools  # for bdist
from cx_Freeze import setup, Executable
import meshroom

build_exe_options = {
    # include dynamically loaded plugins
    "packages": ["meshroom.nodes", "meshroom.submitters"],
    "include_files": ['COPYING.md']
}


class PlatformExecutable(Executable):
    """
    Extend cx_Freeze.Executable to handle platform variations.
    """

    Windows = "Windows"
    Linux = "Linux"
    Darwin = "Darwin"

    exeExtensions = {
        Windows: ".exe",
        Linux: "",
        Darwin: ".app"
    }

    def __init__(self, script, initScript=None, base=None, targetName=None, icons=None, shortcutName=None,
                 shortcutDir=None, copyright=None, trademarks=None):

        # despite supposed to be optional, targetName is actually required on some configurations
        if not targetName:
            targetName = os.path.splitext(os.path.basename(script))[0]
        # add platform extension to targetName
        targetName += PlatformExecutable.exeExtensions[platform.system()]
        # get icon for platform if defined
        icon = icons.get(platform.system(), None) if icons else None
        super(PlatformExecutable, self).__init__(script, initScript, base, targetName, icon, shortcutName,
                                                 shortcutDir, copyright, trademarks)


meshroomExe = PlatformExecutable(
    "meshroom/ui/__main__.py",
    targetName="Meshroom",
    icons={PlatformExecutable.Windows: "meshroom/ui/img/meshroom.ico"}
)

meshroomPhotog = PlatformExecutable(
    "bin/meshroom_photogrammetry"
)

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
