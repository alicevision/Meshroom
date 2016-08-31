cmake_minimum_required(VERSION 2.6.2)
project(alembicEntityQmlPlugin)

# Cmake module path
set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")

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

# Alembic dependency
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-register")
find_package(Alembic REQUIRED)
include_directories(${ABC_INCLUDE_DIR})

# Target properties
add_library(${TARGETOBJ} SHARED ${TARGET_SRCS})
target_link_libraries(${TARGETOBJ} ${ABC_LIBRARIES})
QT5_USE_MODULES(${TARGETOBJ} Core Qml Quick 3DCore 3DRender 3DExtras)

# Install settings
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        DESTINATION ${CMAKE_INSTALL_PREFIX}/plugins/qml
        FILES_MATCHING PATTERN "qmldir"
        PATTERN "cmake" EXCLUDE)
install(TARGETS ${TARGETOBJ}
        DESTINATION "${CMAKE_INSTALL_PREFIX}/plugins/qml/AlembicEntity")
