

DEPENDENCIES
------------

- cmake
- Qt >= 5.6
- Alembic (optional)


INSTALL
-------

You'll need a C++11 compiler.

    ./configure -DCMAKE_BUILD_TYPE=Release \
                -DCMAKE_PREFIX_PATH=/path/to/qt/lib/cmake \
                -DWITH_OPENMVG_PLUGIN=ON
    make -j4 && make install
