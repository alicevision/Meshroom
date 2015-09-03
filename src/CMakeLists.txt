
#
# Target srcs
#
file(GLOB_RECURSE TARGET_SRCS *.cpp *.cxx *.cc *.C *.c *.h *.hpp)

#
# Target name
#
set(TARGETOBJ mockup)


#
# dependencies
#
find_package(OpenGL REQUIRED)
include_directories(${OPENGL_INCLUDE_DIR})

set(CMAKE_AUTOMOC ON)
set(CMAKE_INCLUDE_CURRENT_DIR ON)
find_package(Qt5Core REQUIRED)
find_package(Qt5Widgets REQUIRED)
QT5_ADD_RESOURCES(TARGET_QRCS qml/resources.qrc)

#
# Target properties
#
add_executable(${TARGETOBJ} ${TARGET_SRCS} ${TARGET_QRCS})
target_link_libraries(${TARGETOBJ}
                    ${GLEW_LIBRARIES}
                    ${OPENGL_LIBRARIES})
#
# Optional alembic importer
#
find_package(Alembic)
if (ALEMBIC_FOUND)
include_directories(${ABC_INCLUDE_DIR})
add_definitions(-DWITH_ALEMBIC)
target_link_libraries(${TARGETOBJ} ${ABC_LIBRARIES})
endif (ALEMBIC_FOUND)

QT5_USE_MODULES(${TARGETOBJ} Widgets Qml Quick)
