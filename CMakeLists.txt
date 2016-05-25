
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
include_directories("${ROOT}/plugins")

#
# Clang && macosx
#
if(("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang") AND APPLE)
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")
endif()

#
# C++11
#
if(("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang") OR ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU"))
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
endif()

#
# Clang && debug adds address sanitizer
#
if(("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang") AND NOT APPLE)
	set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -fsanitize=address")
endif()

#
# Disabling some warnings
#
if(("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang") AND APPLE)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-register -Wc++11-extensions")
endif()

#
# RPATH handling
#
set(CMAKE_SKIP_BUILD_RPATH FALSE)
set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
list(FIND CMAKE_PLATFORM_IMPLICIT_LINK_DIRECTORIES "${CMAKE_INSTALL_PREFIX}/lib" isSystemDir)
if("${isSystemDir}" STREQUAL "-1")
	set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
endif("${isSystemDir}" STREQUAL "-1")

#
# Add Build Targets
#
add_subdirectory(dependencies/dependency_graph dependency_graph)
add_subdirectory(src meshroom)
add_subdirectory(plugins)
