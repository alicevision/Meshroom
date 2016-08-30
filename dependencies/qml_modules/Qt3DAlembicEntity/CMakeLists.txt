cmake_minimum_required(VERSION 2.6.2)
project(qt3DAlembicEntityQmlPlugin)

set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")

#
# Target srcs
#
file(GLOB_RECURSE TARGET_SRCS *.cpp *.cxx *.cc *.C *.c *.h *.hpp)

#
# Target name
#
set(TARGETOBJ qt3DAlembicEntityQmlPlugin)

#
# dependencies
#
set(CMAKE_AUTOMOC ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)
find_package(Qt5Core REQUIRED)
find_package(Qt5Widgets REQUIRED)
find_package(Qt53DCore REQUIRED)
find_package(Qt53DRender REQUIRED)
find_package(Qt53DExtras REQUIRED)

# Alembic
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-register")
find_package(Alembic)
include_directories(${ABC_INCLUDE_DIR})

#
# Target properties
#
add_library(${TARGETOBJ} SHARED ${TARGET_SRCS})
target_link_libraries(${TARGETOBJ} ${ABC_LIBRARIES})
QT5_USE_MODULES(${TARGETOBJ} Widgets Qml Quick 3DCore 3DRender 3DExtras)

#
# Install settings
#
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
	set(CMAKE_INSTALL_PREFIX ${ROOT}/dist CACHE STRING "Plugin install path" FORCE)
endif(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
install(DIRECTORY ${CMAKE_CURRENT_LIST_DIR} DESTINATION ${CMAKE_INSTALL_PREFIX}/qml_modules FILES_MATCHING PATTERN "*.qml" PATTERN "qmldir")
install(TARGETS ${TARGETOBJ} DESTINATION "${CMAKE_INSTALL_PREFIX}/qml_modules/Qt3DAlembicEntity")
