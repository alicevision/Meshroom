
cmake_minimum_required(VERSION 2.6.2)
project(meshroom)

#
# Versioning
#
set(APPLICATION_VERSION_MAJOR 0)
set(APPLICATION_VERSION_MINOR 1)
set(APPLICATION_VERSION_DEBUG 0)

#
# Project Output Paths
#
set(ROOT ${PROJECT_SOURCE_DIR})

#
# Project Search Paths
#
list(APPEND CMAKE_PREFIX_PATH "${ROOT}")
set(CMAKE_MODULE_PATH "${ROOT}/cmake")

#
# C++11
#
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

#
# RPATH handling
#
set(CMAKE_MACOSX_RPATH TRUE)
set(CMAKE_SKIP_BUILD_RPATH FALSE)
set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
set(CMAKE_INSTALL_RPATH @loader_path/lib @loader_path/../lib)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

#
# Add Build Targets
#
add_subdirectory(dependencies/dependency_graph/src/dglib dglib)
add_subdirectory(src meshroom)
add_subdirectory(plugins)
