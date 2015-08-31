#
# This module tries to find and setup an Alembic configuration for openMVG.
# You can help the search by providing several environment variable or cmake
# variable:
# ALEMBIC_ROOT
# ALEMBIC_HDF5_ROOT
# ALEMBIC_ILMBASE_ROOT
# ALEMBIC_OPENEXR_ROOT
#
# HDF5 and ILMBASE should point to the root dir used to compile alembic
#
# This module provides variables prefixed with ABC
# It also sets ALEMBIC_FOUND if all the libraries and include dirs were found
#

MESSAGE(STATUS "Looking for Alembic. 1.5.8")

################################################################################
# IlmBase include dir for half and ilm libraries used in alembic
################################################################################
# Alembic includes half.h for a single function "half to float", this is sad
FIND_PATH(ABC_HALF_INCLUDE_DIR half.h
    HINTS
    ${ALEMBIC_ILMBASE_ROOT}/include/OpenEXR
    $ENV{ALEMBIC_ILMBASE_ROOT}/include/OpenEXR
    $ENV{ILMBASE_INCLUDE_DIR} )

FIND_PATH(ABC_ILMBASE_LIBS_PATH NAMES libIex.so libIex.a
    PATHS
        ${ALEMBIC_ILMBASE_ROOT}/lib
        ${ALEMBIC_ILMBASE_ROOT}/lib/static
        ${ALEMBIC_ILMBASE_ROOT}/lib64
        $ENV{ALEMBIC_ILMBASE_ROOT}/lib
        $ENV{ALEMBIC_ILMBASE_ROOT}/lib64
        $ENV{ILMBASE_LIBRARY_DIR}
    NO_DEFAULT_PATH)

FIND_LIBRARY(ABC_ILMBASE_IEX Iex PATHS ${ABC_ILMBASE_LIBS_PATH} NO_DEFAULT_PATH)
FIND_LIBRARY(ABC_ILMBASE_IEXMATH IexMath PATHS ${ABC_ILMBASE_LIBS_PATH} NO_DEFAULT_PATH)
FIND_LIBRARY(ABC_ILMBASE_HALF Half PATHS ${ABC_ILMBASE_LIBS_PATH} NO_DEFAULT_PATH)
SET(ABC_ILMBASE_LIBS ${ABC_ILMBASE_IEX} ${ABC_ILMBASE_IEXMATH} ${ABC_ILMBASE_HALF})

# OpenEXR
FIND_LIBRARY(ABC_OPENEXR_LIBS IlmImf
    PATHS
        ${ALEMBIC_OPENEXR_ROOT}/lib
        ${ALEMBIC_OPENEXR_ROOT}/lib64
        $ENV{ALEMBIC_OPENEXR_ROOT}/lib
        $ENV{ALEMBIC_OPENEXR_ROOT}/lib64
        $ENV{OPENEXR_LIBRARY_DIR}
    NO_DEFAULT_PATH)

################################################################################
# HDF5 libraries used in alembic
################################################################################

# FIXME: hdf5 should be handled by a specialized module
FIND_PATH(ABC_HDF5_LIBS_PATH NAMES libhdf5.so libhdf5.a
       PATHS
        ${ALEMBIC_HDF5_ROOT}/lib
        ${ALEMBIC_HDF5_ROOT}/lib64
        $ENV{ALEMBIC_HDF5_ROOT}/lib
        $ENV{ALEMBIC_HDF5_ROOT}/lib64
        $ENV{HDF5_LIBRARY_DIR}
       NO_DEFAULT_PATH)
FIND_LIBRARY(ABC_HDF5 hdf5 PATHS ${ABC_HDF5_LIBS_PATH})
FIND_LIBRARY(ABC_HDF5_HL hdf5_hl PATHS ${ABC_HDF5_LIBS_PATH})
SET(ABC_HDF5_LIBS ${ABC_HDF5} ${ABC_HDF5_HL})

################################################################################
# ALEMBIC include and library dir
################################################################################

FIND_PATH(ABC_INCLUDE_DIR Alembic/Abc/All.h
    PATHS
        $ENV{ALEMBIC_ROOT}/include
        $ENV{ALEMBIC_INCLUDE_DIR}
        ${ALEMBIC_ROOT}/include
    PATH_SUFFIXES
        alembic
    NO_DEFAULT_PATH
)

#
# We force the use of dynamic libraries as using the static ones had caused some
# initialization problems.
FIND_PATH(ABC_LIBRARY_DIR libAlembicAbc.so libAlembicAbc.a
    PATHS
        ${ALEMBIC_ROOT}/lib
        ${ALEMBIC_ROOT}/lib/static
        ${ALEMBIC_ROOT}/lib64
        $ENV{ALEMBIC_ROOT}/lib
        $ENV{ALEMBIC_ROOT}/lib/static
        $ENV{ALEMBIC_ROOT}/lib64
        $ENV{ALEMBIC_LIBRARY_DIR}
        $ENV{ALEMBIC_LIBRARY_DIR}/static
    NO_DEFAULT_PATH)
FIND_LIBRARY(ABC_COLLECTION libAlembicAbcCollection.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_COREFACTORY libAlembicAbcCoreFactory.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_COREOGAWA libAlembicAbcCoreOgawa.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_MATERIAL libAlembicAbcMaterial.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_OGAWA libAlembicOgawa.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_OPENGL libAlembicAbcOpenGL.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_WFOBJCONVERT libAbcWFObjConvert.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC libAlembicAbc.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_COREABSTRACT libAlembicAbcCoreAbstract.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_COREHDF5 libAlembicAbcCoreHDF5.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_GEOM libAlembicAbcGeom.so PATHS ${ABC_LIBRARY_DIR})
FIND_LIBRARY(ABC_UTIL libAlembicUtil.so PATHS ${ABC_LIBRARY_DIR})
SET(ABC_CORE_LIBS
            ${ABC_GEOM}
            ${ABC_COREFACTORY}
            ${ABC}
            ${ABC_COREHDF5}
            ${ABC_COREOGAWA}
            ${ABC_COREABSTRACT}
            ${ABC_OGAWA}
            ${ABC_UTIL}
            #${ABC_COLLECTION}
            #${ABC_WFOBJCONVERT}
            #${ABC_MATERIAL}
            #${ABC_OPENGL}
            )


SET(ABC_LIBRARIES ${ABC_CORE_LIBS} ${ABC_HDF5_LIBS} "-ldl" ${ABC_OPENEXR_LIBS} ${ABC_ILMBASE_LIBS})
SET(ABC_INCLUDE_DIR ${ABC_INCLUDE_DIR} ${ABC_HALF_INCLUDE_DIR})

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS("Alembic" DEFAULT_MSG ABC_LIBRARIES ABC_LIBRARY_DIR ABC_INCLUDE_DIR ABC_HDF5_LIBS)

if (ALEMBIC_FOUND)
    mark_as_advanced(ABC_LIBRARY_DIR ABC_HDF5_LIBS_PATH ABC_ILMBASE_LIBS_PATH)
    message("Found Alembic - will add alembic support")
else()
    message("Alembic NOT FOUND")
endif()
