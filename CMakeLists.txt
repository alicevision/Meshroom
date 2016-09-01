
cmake_minimum_required(VERSION 2.6.2)
project(meshroom)

# Versioning
set(APPLICATION_VERSION_MAJOR 0)
set(APPLICATION_VERSION_MINOR 1)
set(APPLICATION_VERSION_DEBUG 0)

# C++11
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Install settings
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
	set(CMAKE_INSTALL_PREFIX ${PROJECT_SOURCE_DIR}/dist CACHE STRING "Plugin install path" FORCE)
endif(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)

# RPATH handling
set(CMAKE_MACOSX_RPATH TRUE)
set(CMAKE_SKIP_BUILD_RPATH FALSE)
set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
set(CMAKE_INSTALL_RPATH @loader_path/lib @loader_path/../lib)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# list subdirectories macro
macro(subdirlist result curdir)
    file(GLOB children RELATIVE ${curdir} ${curdir}/*)
    set(dirlist "")
    foreach(child ${children})
        if(IS_DIRECTORY ${curdir}/${child})
            list(APPEND dirlist ${child})
        endif()
    endforeach()
    set(${result} ${dirlist})
endmacro()

# add subdirectories
add_subdirectory(dependencies/dependency_graph/src/dglib dglib)
add_subdirectory(src/cpp)
add_subdirectory(src/qml)
add_subdirectory(plugins/qml/controls/ImageGallery)
add_subdirectory(plugins/qml/controls/NodeEditor)
add_subdirectory(plugins/qml/debug/InstantCoding)
add_subdirectory(plugins/qml/debug/Logger)
add_subdirectory(plugins/qml/qt3d/AlembicEntity)
add_subdirectory(plugins/qml/qt3d/MayaCameraController)
add_subdirectory(plugins/qml/stylesheets/DarkStyle)

subdirlist(SUBDIRS ${PROJECT_SOURCE_DIR}/plugins/cpp)
foreach(subdir ${SUBDIRS})
    string(TOUPPER ${subdir} dirname) # to upper
    set(WITH_${dirname}_PLUGIN OFF CACHE BOOL "Build ${dirname} plugin")
    if(WITH_${dirname}_PLUGIN)
        add_subdirectory(${PROJECT_SOURCE_DIR}/plugins/cpp/${subdir})
    endif()
endforeach()
