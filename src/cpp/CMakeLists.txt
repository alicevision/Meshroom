
# Target srcs
file(GLOB_RECURSE TARGET_SRCS *.cpp *.cxx *.cc *.C *.c *.h *.hpp)
file(GLOB_RECURSE QML_SRCS *.qml)

# Target name
set(TARGETOBJ ${PROJECT_NAME})

# DGlib dependency
include_directories(${DG_INCLUDE_DIR})

# graph editor headers
include_directories(${NODEEDITOR_INCLUDE_DIR})
list(APPEND TARGET_SRCS ${NODEEDITOR_HEADERS})

# OpenGL dependency
find_package(OpenGL REQUIRED)
include_directories(${OPENGL_INCLUDE_DIR})

# Qt dependency
if(POLICY CMP0043)
    cmake_policy(SET CMP0043 OLD)
endif()
set(CMAKE_AUTOMOC ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)
find_package(Qt5Core REQUIRED)
find_package(Qt5Qml REQUIRED)
find_package(Qt5Widgets REQUIRED)
find_package(Qt5Quick REQUIRED)
find_package(Qt5QuickControls2 REQUIRED)
add_definitions(-DQT_NO_KEYWORDS)
add_definitions(-DQT_MESSAGELOGCONTEXT)
QT5_ADD_RESOURCES(TARGET_QRCS ${PROJECT_SOURCE_DIR}/src/qml/resources.qrc)

# Debug flags
# Enable QML debugging
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -DQT_QML_DEBUG")

# Target properties
include_directories(${PROJECT_SOURCE_DIR}/plugins/cpp)
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
add_executable(${TARGETOBJ} ${TARGET_SRCS} ${TARGET_QRCS})
target_link_libraries(${TARGETOBJ} ${OPENGL_LIBRARIES} ${DG_LIBRARY})
QT5_USE_MODULES(${TARGETOBJ} Core Qml Quick QuickControls2 Widgets)

# Install settings
install(TARGETS ${TARGETOBJ}
        DESTINATION ${CMAKE_INSTALL_PREFIX})
