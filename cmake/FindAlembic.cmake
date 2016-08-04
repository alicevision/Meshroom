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

# Alembic includes half.h for a single function "half to float", this is unfortunate
FIND_PATH(ABC_HALF_INCLUDE_DIR half.h
    HINTS
        ${ALEMBIC_ILMBASE_ROOT}/include
        $ENV{ALEMBIC_ILMBASE_ROOT}/include
        $ENV{ILMBASE_INCLUDE_DIR}
    PATH_SUFFIXES
        OpenEXR
    )

FIND_LIBRARY(ABC_ILMBASE_IEX_LIB NAMES Iex
    PATHS
        ${ALEMBIC_ILMBASE_ROOT}/lib
        ${ALEMBIC_ILMBASE_ROOT}/lib/static
        ${ALEMBIC_ILMBASE_ROOT}/lib64
        $ENV{ALEMBIC_ILMBASE_ROOT}/lib
        $ENV{ALEMBIC_ILMBASE_ROOT}/lib64
        $ENV{ILMBASE_LIBRARY_DIR}
    )

GET_FILENAME_COMPONENT(ABC_ILMBASE_LIBS_PATH ${ABC_ILMBASE_IEX_LIB} DIRECTORY)

FIND_LIBRARY(ABC_ILMBASE_IEX Iex PATHS ${ABC_ILMBASE_LIBS_PATH})
FIND_LIBRARY(ABC_ILMBASE_IEXMATH IexMath PATHS ${ABC_ILMBASE_LIBS_PATH})
IF(ABC_ILMBASE_IEXMATH MATCHES ".*-NOTFOUND")
  # This library is optional, so ignore if not found.
  SET(ABC_ILMBASE_IEXMATH "")
ENDIF()
FIND_LIBRARY(ABC_ILMBASE_HALF Half PATHS ${ABC_ILMBASE_LIBS_PATH})
SET(ABC_ILMBASE_LIBS ${ABC_ILMBASE_IEX} ${ABC_ILMBASE_IEXMATH} ${ABC_ILMBASE_HALF})

# OpenEXR
FIND_LIBRARY(ABC_OPENEXR_LIBS IlmImf 
    PATHS 
        ${ALEMBIC_OPENEXR_ROOT}/lib
        ${ALEMBIC_OPENEXR_ROOT}/lib64
        $ENV{ALEMBIC_OPENEXR_ROOT}/lib 
        $ENV{ALEMBIC_OPENEXR_ROOT}/lib64
        $ENV{OPENEXR_LIBRARY_DIR}
    )

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
       )
FIND_LIBRARY(ABC_HDF5 hdf5 PATHS ${ABC_HDF5_LIBS_PATH})
FIND_LIBRARY(ABC_HDF5_HL hdf5_hl PATHS ${ABC_HDF5_LIBS_PATH})
SET(ABC_HDF5_LIBS  ${ABC_HDF5_HL} ${ABC_HDF5})

################################################################################
# ALEMBIC include and library dir
################################################################################

FIND_PATH(ABC_INCLUDE_DIR Alembic/Abc/All.h
    PATHS
        $ENV{ALEMBIC_ROOT}/include
        $ENV{ALEMBIC_INCLUDE_DIR}
        ${ALEMBIC_ROOT}/include
        ${ALEMBIC_INCLUDE_DIR}
    PATH_SUFFIXES
        alembic
    )

# message(STATUS "ALEMBIC_ROOT: ${ALEMBIC_ROOT}")
# message(STATUS "ABC_INCLUDE_DIR: ${ABC_INCLUDE_DIR}")
# message(STATUS "ABC_OPENEXR_LIBS ${ABC_OPENEXR_LIBS}")

#
# We force the use of dynamic libraries as using the static ones had caused some 
# initialization problems.

# try to find the all-in-one library
message(STATUS "trying to found the all-in-one libAlembic.so")
FIND_LIBRARY(ABC_LIBRARY_ALLINONE Alembic
    PATHS
        ${ALEMBIC_ROOT}/lib
        ${ALEMBIC_ROOT}/lib/static
        ${ALEMBIC_ROOT}/lib64
        $ENV{ALEMBIC_ROOT}/lib
        $ENV{ALEMBIC_ROOT}/lib/static
        $ENV{ALEMBIC_ROOT}/lib64
        $ENV{ALEMBIC_LIBRARY_DIR}
        $ENV{ALEMBIC_LIBRARY_DIR}/static
    )
# message(STATUS "ABC_LIBRARY_ALLINONE ${ABC_LIBRARY_ALLINONE}")
if( EXISTS ${ABC_LIBRARY_ALLINONE})
    message(STATUS "found the all-in-one libAlembic: ${ABC_LIBRARY_ALLINONE}")
    SET(ABC_CORE_LIBS ${ABC_LIBRARY_ALLINONE})
    GET_FILENAME_COMPONENT(ABC_LIBRARY_DIR ${ABC_LIBRARY_ALLINONE} DIRECTORY)
else()
    message(STATUS "all-in-one not found, try finding individual ones --  ${ABC_LIBRARY_ALLINONE}")

    FIND_LIBRARY(ABC_LIBRARY AlembicAbc
        PATHS
            ${ALEMBIC_ROOT}/lib
            ${ALEMBIC_ROOT}/lib/static
            ${ALEMBIC_ROOT}/lib64
            $ENV{ALEMBIC_ROOT}/lib
            $ENV{ALEMBIC_ROOT}/lib64
            $ENV{ALEMBIC_LIBRARY_DIR}
        )
    GET_FILENAME_COMPONENT(ABC_LIBRARY_DIR ${ABC_LIBRARY} DIRECTORY)

    FIND_LIBRARY(ABC_COLLECTION AlembicAbcCollection PATHS ${ABC_LIBRARY_DIR})
    FIND_LIBRARY(ABC_COREFACTORY AlembicAbcCoreFactory PATHS ${ABC_LIBRARY_DIR})
    FIND_LIBRARY(ABC_COREOGAWA AlembicAbcCoreOgawa PATHS ${ABC_LIBRARY_DIR})
    #FIND_LIBRARY(ABC_MATERIAL libAlembicAbcMaterial.so PATHS ${ABC_LIBRARY_DIR})
    FIND_LIBRARY(ABC_OGAWA AlembicOgawa PATHS ${ABC_LIBRARY_DIR})
    #FIND_LIBRARY(ABC_OPENGL libAlembicAbcOpenGL.so PATHS ${ABC_LIBRARY_DIR})
    #FIND_LIBRARY(ABC_WFOBJCONVERT libAbcWFObjConvert.so PATHS ${ABC_LIBRARY_DIR})
    FIND_LIBRARY(ABC_COREABSTRACT AlembicAbcCoreAbstract PATHS ${ABC_LIBRARY_DIR})
    FIND_LIBRARY(ABC_COREHDF5 AlembicAbcCoreHDF5 PATHS ${ABC_LIBRARY_DIR})
    FIND_LIBRARY(ABC_GEOM AlembicAbcGeom PATHS ${ABC_LIBRARY_DIR})
    FIND_LIBRARY(ABC_UTIL AlembicUtil PATHS ${ABC_LIBRARY_DIR})
    SET(ABC_CORE_LIBS ${ABC_LIBRARY} 
                      ${ABC_GEOM} 
                      ${ABC} 
                      ${ABC_COREFACTORY} 
                      ${ABC_COREHDF5} 
                      ${ABC_COREOGAWA} 
                      ${ABC_COREABSTRACT} 
                      ${ABC_UTIL} 
                      ${ABC_OGAWA} 
                      ${ABC_COLLECTION})
endif()

SET(ABC_LIBRARIES ${ABC_CORE_LIBS} ${ABC_HDF5_LIBS} "-ldl" ${ABC_OPENEXR_LIBS} ${ABC_ILMBASE_LIBS})
SET(ABC_INCLUDE_DIR ${ABC_INCLUDE_DIR} ${ABC_HALF_INCLUDE_DIR})

message(STATUS "ABC_LIBRARIES: ${ABC_LIBRARIES}")
message(STATUS "ABC_INCLUDE_DIR: ${ABC_INCLUDE_DIR}")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS("Alembic" DEFAULT_MSG ABC_LIBRARIES ABC_LIBRARY_DIR ABC_INCLUDE_DIR ABC_HDF5_LIBS)

if (ALEMBIC_FOUND)
    mark_as_advanced(ABC_LIBRARY_DIR ABC_HDF5_LIBS_PATH ABC_ILMBASE_LIBS_PATH)
    message("Found Alembic - will build alembic importer")
else()
    message("Alembic NOT FOUND")   
endif()
