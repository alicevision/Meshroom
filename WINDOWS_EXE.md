# Meshroom executable generation on Windows

This describes how to generate Meshroom's executable on Windows. This does not include any plugin, only Meshroom itself.

## Set helper environment variables

```bash
set SRC_ROOT=/path/to/Meshroom/repository
set PYTHON=/path/to/Python/Python311/python.exe
set RELEASE_VERSION=2026.x.x
set MESHROOM_EXE_DIR=/path/to/Meshroom-%RELEASE_VERSION%
```

## Meshroom build

### Prepare environment

```bash
cd %SRC_ROOT%
%PYTHON% -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt -r dev_requirements.txt
```

### Executable generation

```bash
python setup.py install_exe -d %MESHROOM_EXE_DIR%
deactivate
```

> [!IMPORTANT]
> PySide6 >= 6.8.0 misses a DLL in its pip installation. If it is not manually added, Meshroom will run into the following error when attempting to leave the homepage and displaying the application:
> `Cannot load /path/to/pip/install/PySide6/qml/QtQuick/Scene3D/qtquickscene3dplugin.dll: specified module cannot be found`.
> The missing DLL is Qt63DQuickScene3D.dll and can be downloaded [here](https://drive.google.com/uc?export=download&id=1vhPDmDQJJfM_hBD7KVqRfh8tiqTCN7Jv) (for MSVC2022_64). Alternatively, it can be retrieved from any Qt local installation.
> It needs to be placed in `%MESHROOM_EXE_DIR%/lib/PySide6`.

### Clean the packages

Get rid of all the things that are unnecessary for Meshroom. This will lighten the final package.

```bash
cd %MESHROOM_EXE_DIR%/lib/PySide6
del /s /q Qt6Web*.dll Qt6Designer*.dll *.exe
rmdir /s /q resources translations typesystems examples include
```
