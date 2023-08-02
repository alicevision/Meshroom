cmake_minimum_required(VERSION 3.12)
project(meshroom LANGUAGES C CXX)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type for Meshroom plugins" FORCE)
endif()

set(ALICEVISION_ROOT "$ENV{ALICEVISION_ROOT}" CACHE STRING "AliceVision root dir")
set(QT_DIR "$ENV{QT_DIR}" CACHE STRING "Qt root directory")

option(MR_BUILD_QTALICEVISION "Enable building of QtAliceVision plugin" ON)

if(CMAKE_BUILD_TYPE MATCHES Release)
    message(STATUS "Force CMAKE_INSTALL_DO_STRIP in Release")
    set(CMAKE_INSTALL_DO_STRIP ON)
else()
    set(CMAKE_INSTALL_DO_STRIP OFF)
endif()

set(CMAKE_CORE_BUILD_FLAGS -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} -DBUILD_SHARED_LIBS:BOOL=ON -DCMAKE_INSTALL_DO_STRIP=${CMAKE_INSTALL_DO_STRIP})

set(ALEMBIC_CMAKE_FLAGS
  -DAlembic_DIR:PATH=${ALICEVISION_ROOT}/lib/cmake/Alembic
  -DImath_DIR=${ALICEVISION_ROOT}/lib/cmake/Imath
)


include(ExternalProject)
# ==============================================================================
# GNUInstallDirs CMake module
# - Define GNU standard installation directories
# - Provides install directory variables as defined by the GNU Coding Standards.
# ==============================================================================
include(GNUInstallDirs)

# message(STATUS "QT_CMAKE_FLAGS: ${QT_CMAKE_FLAGS}")

if(MR_BUILD_QTALICEVISION)
set(QTALICEVISION_TARGET QtAliceVision)
ExternalProject_Add(${QTALICEVISION_TARGET}
      GIT_REPOSITORY https://github.com/alicevision/QtAliceVision
      GIT_TAG develop
      PREFIX ${BUILD_DIR}
      BUILD_IN_SOURCE 0
      BUILD_ALWAYS 0
      SOURCE_DIR ${CMAKE_CURRENT_BINARY_DIR}/QtAliceVision
      BINARY_DIR ${BUILD_DIR}/QtAliceVision_build
      INSTALL_DIR ${CMAKE_INSTALL_PREFIX}
      CONFIGURE_COMMAND ${CMAKE_COMMAND} ${CMAKE_CORE_BUILD_FLAGS} ${ALEMBIC_CMAKE_FLAGS} -DCMAKE_PREFIX_PATH:PATH=${QT_DIR}$<SEMICOLON>${ALICEVISION_ROOT} -DCMAKE_INSTALL_PREFIX:PATH=<INSTALL_DIR> <SOURCE_DIR>
      )
endif()

