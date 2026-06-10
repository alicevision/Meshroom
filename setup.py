import os
import pathlib
import platform
import subprocess
import setuptools  # for bdist
from cx_Freeze import setup, Executable
from cx_Freeze.command.build_exe import build_exe
import meshroom

currentDir = os.path.dirname(os.path.abspath(__file__))


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
            initScript = os.path.join(currentDir, "setupInitScriptUnix.py")
        elif platform.system() is self.Windows:
            initScript = os.path.join(currentDir, "setupInitScriptWindows.py")
        super(PlatformExecutable, self).__init__(script, initScript, base, targetName, icon, shortcutName,
                                                 shortcutDir, copyright, trademarks)

# Post-build strip for Linux
cmdclass = {}

if platform.system() == "Linux":

    class build_exe_and_strip(build_exe):
        """Strip debug symbols from all .so files after the normal build."""

        def run(self):
            super().run()

            build_dir = pathlib.Path(self.build_exe)
            so_files = [
                f for f in build_dir.rglob("*.so*")
                if f.is_file() and not f.is_symlink()
            ]
            print(f"-- Stripping {len(so_files)} .so files in {build_dir}")
            for so in so_files:
                result = subprocess.run(
                    ["strip", "--strip-unneeded", str(so)],
                    capture_output=True, text=True,
                )
                if result.returncode != 0:
                    print(f"   WARNING: strip failed on {so.name}: {result.stderr.strip()}")
            print("-- Stripping done.")

    cmdclass = {"build_exe": build_exe_and_strip}

build_exe_options = {
    # include dynamically loaded plugins
    "packages": ["meshroom.nodes", "meshroom.submitters"],
    "includes": [
        "idna.idnadata",  # Dependency needed by SketchfabUpload node, but not detected by cx_Freeze
        "timeit",
        "pickletools",
        "modulefinder",
        "cProfile",
        "colorsys",
        "xml.dom.minidom",
        "http.cookies",
        "filecmp",
        "logging.handlers",
        "cmath",
        "numpy"
    ],
    "include_files": ["CHANGES.md", "COPYING.md", "LICENSE-MPL2.md", "README.md", "bin"],
    "excludes": [
        # Python stdlib bloat
        "tkinter",
        "unittest",
        "email",
        "html",
        "http.server",
        "xmlrpc",
        # Unused PySide6/Qt modules
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtSpatialAudio",
        "PySide6.QtDataVisualization",
        "PySide6.QtGraphs",
        "PySide6.QtGraphsWidgets",
        "PySide6.QtBluetooth",
        "PySide6.QtNfc",
        "PySide6.QtSerialPort",
        "PySide6.QtSerialBus",
        "PySide6.QtPositioning",
        "PySide6.QtLocation",
        "PySide6.QtSensors",
        "PySide6.QtTextToSpeech",
        "PySide6.QtVirtualKeyboard",
        "PySide6.QtWebSockets",
        "PySide6.QtWebChannel",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtQuick3D",
        "PySide6.QtRemoteObjects",
        "PySide6.QtScxml",
        "PySide6.QtStateMachine",
        "PySide6.QtNetworkAuth",
        "PySide6.QtAxContainer",
    ],
}
if os.path.isdir(os.path.join(currentDir, "tractor")):
    build_exe_options["packages"].append("tractor")
if os.path.isdir(os.path.join(currentDir, "simpleFarm")):
    build_exe_options["packages"].append("simpleFarm")

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

executables = [
    # GUI
    PlatformExecutable(
        "meshroom/ui/__main__.py",
        targetName="Meshroom",
        icons={PlatformExecutable.Windows: "meshroom/ui/img/meshroom.ico"}
    ),
    # Command line
    PlatformExecutable("bin/meshroom_batch"),
    PlatformExecutable("bin/meshroom_compute"),
    PlatformExecutable("bin/meshroom_newNodeType"),
    PlatformExecutable("bin/meshroom_statistics"),
    PlatformExecutable("bin/meshroom_status"),
    PlatformExecutable("bin/meshroom_submit"),
]

setup(
    name="Meshroom",
    description="Meshroom",
    install_requires=["psutil", "PySide6", "markdown"],
    setup_requires=[
        "cx_Freeze"
    ],
    version=meshroom.__version__,
    options={"build_exe": build_exe_options},
    executables=executables,
    cmdclass=cmdclass,
)
