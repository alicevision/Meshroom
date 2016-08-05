
#
# Target srcs
#
file(GLOB_RECURSE TARGET_SRCS *.cpp *.cxx *.cc *.C *.c *.h *.hpp)

#
# Target name
#
set(TARGETLIB openmvgPlugin)

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
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/..) # Common plugin interface
include_directories(${CMAKE_CURRENT_BINARY_DIR} ${DG_INCLUDE_DIR})
add_library(${TARGETLIB} SHARED ${TARGET_SRCS} ${TARGET_QRCS})
target_link_libraries(${TARGETLIB} ${DG_LIBRARY})
QT5_USE_MODULES(${TARGETLIB} Core)

#
# Install settings
#
install(TARGETS ${TARGETLIB} DESTINATION ${CMAKE_INSTALL_PREFIX}/plugins)
