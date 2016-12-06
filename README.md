

DEPENDENCIES
------------

- CMake
- Qt 5.6
- Alembic (optional)


INSTALL
-------

You'll need a C++11 compiler.

    ./configure -DCMAKE_PREFIX_PATH=/path/to/qt/5.6/lib/cmake -DCMAKE_BUILD_TYPE=Release
    make -j
    make install


USAGE
-----

### Dependencies

In order to launch reconstructions with meshroom you need to have the following installed:

* [openMVG](https://github.com/poparteu/openMVG) from the POPART fork, `popart_develop` branch
  ```
  git clone -b popart_develop git@github.com:poparteu/openMVG.git
  ```
  * build with ALEMBIC support 
     - `-DOpenMVG_USE_ALEMBIC=ON`
	 - `-DALEMBIC_ROOT=/path/to/where/alembic/is/installed `
	 - `-DALEMBIC_HDF5_ROOT=/usr/lib/x86_64-linux-gnu/hdf5/serial `
	 - `-DALEMBIC_ILMBASE_ROOT=/usr/lib/x86_64-linux-gnu/ `
	 - `-DALEMBIC_OPENEXR_ROOT=/usr/lib/x86_64-linux-gnu/`
  * [optional] build with CCTAG support
	 - `-DOpenMVG_USE_CCTAG=ON`
  * build and install the library in any path you want, e.g. `/usr/local/`
	 - `-DCMAKE_INSTALL_PREFIX=/usr/local/`
  * then `make install`

* [simpleFarm](https://github.com/poparteu/simpleFarm), `dev_serialsubtasks` branch
  ```
  git clone -b dev_serialsubtasks git@github.com:poparteu/simpleFarm.git
  ```
	- you may need to install `dill` dependency
        - `pip install dill`

* [scriptMVG](https://github.com/poparteu/scriptMVG), `develop` branch
  ```
  git clone -b develop git@github.com:poparteu/scriptMVG.git
  ```


### Set up

Finally, you need some environment variables to be able to launch the reconstructions from meshroom
 
```shell
# these are just to have something clean
export OMVG_BASE=/usr/local/
export SCRIPTMVG_BASE=/path/where/you/cloned/scriptMVG
export SIMPLEFARM_BASE=/path/where/you/cloned/simpleFarm/

# these are actually needed by meshroom
export PYTHONPATH=${SCRIPTMVG_BASE}:${SIMPLEFARM_BASE}
export PATH=${OMVG_BASE}/bin:$PATH
export CAMERA_DATABASE=${OMVG_BASE}/share/openMVG/sensor_width_camera_database.txt
export MESHROOM_STATUS_COMMAND=${SCRIPTMVG_BASE}/job_status.py
export MESHROOM_START_COMMAND=${SCRIPTMVG_BASE}/job_start.py
```
