file(GLOB_RECURSE QML_SRCS *.qml)
add_custom_target(_meshroom_QML_SRC SOURCES ${QML_SRCS})

# install qml files
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
		DESTINATION ${CMAKE_INSTALL_PREFIX}
		PATTERN "CMakeLists.txt" EXCLUDE
		PATTERN "resources.qrc" EXCLUDE)
