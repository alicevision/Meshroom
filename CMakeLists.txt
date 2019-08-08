cmake_minimum_required(VERSION 3.3)
project(meshroom LANGUAGES C CXX)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type for Meshroom plugins" FORCE)
endif()

set(ALICEVISION_ROOT "$ENV{ALICEVISION_ROOT}" CACHE STRING "AliceVision root dir")
set(QT_DIR "$ENV{QT_DIR}" CACHE STRING "Qt root directory")

option(MR_BUILD_QTOIIO "Enable building of QtOIIO plugin" ON)
option(MR_BUILD_QMLALEMBIC "Enable building of qmlAlembic plugin" ON)
option(MR_BUILD_QTALICEVISION "Enable building of qtAliceVision plugin" ON)

if(CMAKE_BUILD_TYPE MATCHES Release)
    message(STATUS "Force CMAKE_INSTALL_DO_STRIP in Release")
    set(CMAKE_INSTALL_DO_STRIP ON)
else()
    set(CMAKE_INSTALL_DO_STRIP OFF)
endif()

set(CMAKE_CORE_BUILD_FLAGS -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} -DBUILD_SHARED_LIBS:BOOL=ON -DCMAKE_INSTALL_DO_STRIP=${CMAKE_INSTALL_DO_STRIP})

set(OIIO_CMAKE_FLAGS 
  -DOPENIMAGEIO_LIBRARY_DIR_HINTS=${ALICEVISION_ROOT}/lib64
  -DOPENIMAGEIO_INCLUDE_DIR_HINTS=${ALICEVISION_ROOT}/include
  -DILMBASE_INCLUDE_PATH=${ALICEVISION_ROOT}/include
  -DOPENEXR_INCLUDE_PATH=${ALICEVISION_ROOT}/include
)
set(ALEMBIC_CMAKE_FLAGS
  -DAlembic_DIR:PATH=${ALICEVISION_ROOT}/lib64/cmake/Alembic
  -DILMBASE_ROOT=${ALICEVISION_ROOT}
)


include(ExternalProject)
# ==============================================================================
# GNUInstallDirs CMake module
# - Define GNU standard installation directories
# - Provides install directory variables as defined by the GNU Coding Standards.
# ==============================================================================
include(GNUInstallDirs)

# message(STATUS "QT_CMAKE_FLAGS: ${QT_CMAKE_FLAGS}")

if(MR_BUILD_QTOIIO)
set(QTOIIO_TARGET qtOIIO)
ExternalProject_Add(${QTOIIO_TARGET}
      GIT_REPOSITORY https://github.com/alicevision/QtOIIO
      GIT_TAG develop
      PREFIX ${BUILD_DIR}
      BUILD_IN_SOURCE 0
      BUILD_ALWAYS 0
      SOURCE_DIR ${CMAKE_CURRENT_BINARY_DIR}/qtoiio
      BINARY_DIR ${BUILD_DIR}/qtoiio_build
      INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
      CONFIGURE_COMMAND ${CMAKE_COMMAND} ${CMAKE_CORE_BUILD_FLAGS} ${OIIO_CMAKE_FLAGS} -DCMAKE_PREFIX_PATH:PATH=${QT_DIR} -DCMAKE_INSTALL_PREFIX:PATH=<INSTALL_DIR> <SOURCE_DIR>
      )
endif()


if(MR_BUILD_QMLALEMBIC)
set(QMLALEMBIC_TARGET qmlAlembic)
ExternalProject_Add(${QMLALEMBIC_TARGET}
      GIT_REPOSITORY https://github.com/alicevision/qmlAlembic
      GIT_TAG develop
      PREFIX ${BUILD_DIR}
      BUILD_IN_SOURCE 0
      BUILD_ALWAYS 0
      SOURCE_DIR ${CMAKE_CURRENT_BINARY_DIR}/qmlalembic
      BINARY_DIR ${BUILD_DIR}/qmlalembic_build
      INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
      CONFIGURE_COMMAND ${CMAKE_COMMAND} ${CMAKE_CORE_BUILD_FLAGS} ${ALEMBIC_CMAKE_FLAGS} -DCMAKE_PREFIX_PATH:PATH=${QT_DIR} -DCMAKE_INSTALL_PREFIX:PATH=<INSTALL_DIR> <SOURCE_DIR>
      )
endif()

if(MR_BUILD_QTALICEVISION)
set(QTALICEVISION_TARGET qtAliceVision)
ExternalProject_Add(${QTALICEVISION_TARGET}
      GIT_REPOSITORY https://github.com/alicevision/qtAliceVision
      GIT_TAG develop
      PREFIX ${BUILD_DIR}
      BUILD_IN_SOURCE 0
      BUILD_ALWAYS 0
      SOURCE_DIR ${CMAKE_CURRENT_BINARY_DIR}/qtAliceVision
      BINARY_DIR ${BUILD_DIR}/qtAliceVision_build
      INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
      CONFIGURE_COMMAND ${CMAKE_COMMAND} ${CMAKE_CORE_BUILD_FLAGS} ${ALEMBIC_CMAKE_FLAGS} -DCMAKE_PREFIX_PATH:PATH=${QT_DIR}$<SEMICOLON>${ALICEVISION_ROOT} -DCMAKE_INSTALL_PREFIX:PATH=<INSTALL_DIR> <SOURCE_DIR>
      )
endif()

