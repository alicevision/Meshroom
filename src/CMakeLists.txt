
#
# Target srcs
#
file(GLOB_RECURSE TARGET_SRCS *.cpp *.cxx *.cc *.C *.c *.h *.hpp)
file(GLOB_RECURSE QML_SRCS *.qml)

#
# Target name
#
set(TARGETOBJ meshroom)

#
# dependencies
#

# OpenGL
find_package(OpenGL REQUIRED)
include_directories(${OPENGL_INCLUDE_DIR})

# Qt
set(CMAKE_AUTOMOC ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)
find_package(Qt5Core REQUIRED)
find_package(Qt5Qml REQUIRED)
find_package(Qt5Quick REQUIRED)
find_package(Qt5QuickControls2 REQUIRED)

#
# Add definitions
#
add_definitions(-DQT_MESSAGELOGCONTEXT)
add_definitions(-DQT_NO_KEYWORDS)

#
# Target properties
#
include_directories(${ROOT}/plugins)
include_directories(${ROOT}/src)
include_directories(${DG_INCLUDE_DIR})
add_executable(${TARGETOBJ} ${TARGET_SRCS} ${TARGET_QRCS})
target_link_libraries(${TARGETOBJ} ${OPENGL_LIBRARIES} ${DG_LIBRARY})
QT5_ADD_RESOURCES(TARGET_QRCS qml/resources.qrc)
QT5_USE_MODULES(${TARGETOBJ} Core Qml Quick QuickControls2)

#
# Install settings
#
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
	set(CMAKE_INSTALL_PREFIX ${ROOT}/dist CACHE STRING "Plugin install path" FORCE)
endif(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
install(TARGETS ${TARGETOBJ} DESTINATION ${CMAKE_INSTALL_PREFIX})
install(DIRECTORY ${CMAKE_CURRENT_LIST_DIR}/qml DESTINATION ${CMAKE_INSTALL_PREFIX} FILES_MATCHING PATTERN "*.qml")

#
# QML modules
#
add_subdirectory(../dependencies/qml_modules/Logger ../qml_modules/Logger)
add_subdirectory(../dependencies/qml_modules/GlobalShortcut ../qml_modules/GlobalShortcut)
add_subdirectory(../dependencies/qml_modules/DarkStyle ../qml_modules/DarkStyle)
add_subdirectory(../dependencies/qml_modules/ImageGallery ../qml_modules/ImageGallery)
add_subdirectory(../dependencies/qml_modules/NodeEditor ../qml_modules/NodeEditor)
add_subdirectory(../dependencies/qml_modules/Qt3DAlembicEntity ../qml_modules/Qt3DAlembicEntity)
