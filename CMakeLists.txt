
cmake_minimum_required(VERSION 2.6.2)
project(mockup)

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
set(LIBRARY_OUTPUT_PATH "${ROOT}/dist/lib")
set(EXECUTABLE_OUTPUT_PATH "${ROOT}/dist/bin")

#
# Project Search Paths
#
list(APPEND CMAKE_PREFIX_PATH "${ROOT}")
set(CMAKE_MODULE_PATH "${ROOT}/cmake")
include_directories("${ROOT}/src")

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
if(("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang") AND NOT APPLE)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-register -Wc++11-extensions")
endif()

#
# Add Build Targets
#
add_subdirectory(src)
