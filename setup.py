import platform

import os
import setuptools  # for bdist
from cx_Freeze import setup, Executable
import meshroom


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
        if platform.system() in (self.Linux, self.Darwin):
            currentDir = os.path.dirname(os.path.abspath(__file__))
            initScript = os.path.join(currentDir, "setupInitScriptUnix.py")
        super(PlatformExecutable, self).__init__(script, initScript, base, targetName, icon, shortcutName,
                                                 shortcutDir, copyright, trademarks)


build_exe_options = {
    # include dynamically loaded plugins
    "packages": ["meshroom.nodes", "meshroom.submitters"],
    "includes": [
        "idna.idnadata",  # Dependency needed by SketchfabUpload node, but not detected by cx_Freeze
    ],
    "include_files": ["CHANGES.md", "COPYING.md", "LICENSE-MPL2.md", "README.md"]
}

if platform.system() == PlatformExecutable.Linux:
    # include required system libs
    # from https://github.com/Ultimaker/cura-build/blob/master/packaging/setup_linux.py.in
    build_exe_options.update({
        "bin_path_includes": [
            "/lib",
            "/lib64",
            "/usr/lib",
            "/usr/lib64",
        ],
        "bin_includes": [
            "libssl3",
            "libssl",
            "libcrypto",
        ],
        "bin_excludes": [
            "linux-vdso.so",
            "libpthread.so",
            "libdl.so",
            "librt.so",
            "libstdc++.so",
            "libm.so",
            "libgcc_s.so",
            "libc.so",
            "ld-linux-x86-64.so",
            "libz.so",
            "libgcc_s.so",
            "libglib-2",
            "librt.so",
            "libcap.so",
            "libGL.so",
            "libglapi.so",
            "libXext.so",
            "libXdamage.so",
            "libXfixes.so",
            "libX11-xcb.so",
            "libX11.so",
            "libxcb-glx.so",
            "libxcb-dri2.so",
            "libxcb.so",
            "libXxf86vm.so",
            "libdrm.so",
            "libexpat.so",
            "libXau.so",
            "libglib-2.0.so",
            "libgssapi_krb5.so",
            "libgthread-2.0.so",
            "libk5crypto.so",
            "libkeyutils.so",
            "libkrb5.so",
            "libkrb5support.so",
            "libresolv.so",
            "libutil.so",
            "libXrender.so",
            "libcom_err.so",
            "libgssapi_krb5.so",
        ]
    })

meshroomExe = PlatformExecutable(
    "meshroom/ui/__main__.py",
    targetName="Meshroom",
    icons={PlatformExecutable.Windows: "meshroom/ui/img/meshroom.ico"}
)

meshroomPhotog = PlatformExecutable(
    "bin/meshroom_photogrammetry"
)

meshroomCompute = PlatformExecutable(
    "bin/meshroom_compute"
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
    executables=[meshroomExe, meshroomPhotog, meshroomCompute],
)
