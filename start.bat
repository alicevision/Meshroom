REM Windows
REM Add the aliceVision and qtPlugins folders with the binaries to this directory

set MESHROOM_INSTALL_DIR=%CD%
set PYTHONPATH=%CD%

REM # Development options
REM set MESHROOM_OUTPUT_QML_WARNINGS=1
REM set MESHROOM_INSTANT_CODING=1
REM set QT_PLUGIN_PATH=C:\dev\meshroom\install
REM set QML2_IMPORT_PATH=C:\dev\meshroom\install\qml
REM set PATH=C:\dev\AliceVision\install\bin;C:\dev\vcpkg\installed\x64-windows\bin

python meshroom\ui

