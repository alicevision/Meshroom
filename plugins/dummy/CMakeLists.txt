
#
# Target srcs
#
file(GLOB_RECURSE TARGET_SRCS *.cpp *.cxx *.cc *.C *.c *.h *.hpp)

#
# Target name
#
set(TARGETLIB dummyPlugin)

#
# dependencies
#
set(CMAKE_AUTOMOC ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)
find_package(Qt5Core REQUIRED)

#
# Add definitions
#
add_definitions(-DQT_MESSAGELOGCONTEXT)
add_definitions(-DQT_NO_KEYWORDS)
add_definitions(-DQT_PLUGIN)

#
# Target properties
#
include_directories(${CMAKE_CURRENT_BINARY_DIR}/..)
include_directories(${CMAKE_CURRENT_BINARY_DIR})
include_directories(${ROOT}/dependencies/dependency_graph/src)
add_library(${TARGETLIB} SHARED ${TARGET_SRCS} ${TARGET_QRCS})
target_link_libraries(${TARGETLIB} graph_core)
QT5_USE_MODULES(${TARGETLIB} Core)

#
# Install settings
#
install(TARGETS ${TARGETLIB} DESTINATION ${CMAKE_INSTALL_PREFIX}/plugins)
