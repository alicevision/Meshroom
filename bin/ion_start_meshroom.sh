#!/bin/bash

PATH_QML=${ION_CONTAINER_ROOT}/base/qml/QtQuick
PATH_QML_TRUE=`readlink -f $PATH_QML`/../
PATH_PLUGIN=${ION_CONTAINER_ROOT}/base/imageformats/
PATH_PLUGIN_TRUE=`readlink -f $PATH_PLUGIN`/../

export QML2_IMPORT_PATH=$PATH_QML_TRUE:$QML2_IMPORT_PATH
export QT_PLUGIN_PATH=$PATH_PLUGIN_TRUE:$QT_PLUGIN_PATH

python ${ION_CONTAINER_ROOT}/base/meshroom/meshroom/ui
