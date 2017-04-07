cmake_minimum_required(VERSION 2.6.2)
project(darkStylePlugin)

file(GLOB_RECURSE QML_SRCS *.qml)
add_custom_target(_darkStyle_QML_SRC SOURCES ${QML_SRCS})

# Install settings
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        DESTINATION ${CMAKE_INSTALL_PREFIX}/plugins/qml
        FILES_MATCHING PATTERN "*.qml"
        PATTERN "qmldir")
