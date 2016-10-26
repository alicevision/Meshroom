cmake_minimum_required(VERSION 2.6.2)
project(nodeEditorQmlPlugin)

# Target srcs
file(GLOB_RECURSE TARGET_SRCS *.cpp *.cxx *.cc *.C *.c *.h *.hpp)

# Target name
set(TARGETOBJ ${PROJECT_NAME})

# Qt dependency
if(POLICY CMP0043)
    cmake_policy(SET CMP0043 OLD)
endif()
set(CMAKE_AUTOMOC ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)
find_package(Qt5Core REQUIRED)
find_package(Qt5Qml REQUIRED)
find_package(Qt5Quick REQUIRED)
add_definitions(-DQT_NO_KEYWORDS)

# Target properties
add_library(${TARGETOBJ} SHARED ${TARGET_SRCS})
target_link_libraries(${TARGETOBJ})
QT5_USE_MODULES(${TARGETOBJ} Core Qml Quick)

# Install settings
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        DESTINATION ${CMAKE_INSTALL_PREFIX}/plugins/qml
        FILES_MATCHING PATTERN "*.qml"
        PATTERN "qmldir")
install(TARGETS ${TARGETOBJ}
        DESTINATION "${CMAKE_INSTALL_PREFIX}/plugins/qml/NodeEditor")

# Exports
set(NODEEDITOR_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/.. PARENT_SCOPE)
file(GLOB_RECURSE TARGET_HEADERS *.h *.hpp)
list(REMOVE_ITEM TARGET_HEADERS ${CMAKE_CURRENT_SOURCE_DIR}/plugin.hpp ${CMAKE_CURRENT_SOURCE_DIR}/EdgeItem.hpp)
set(NODEEDITOR_HEADERS ${TARGET_HEADERS} PARENT_SCOPE)
