#!/bin/bash

### retrieve version ###
if [ -z "$ION_CONTAINER_ROOT" ]; then
 exit
fi

#retrieve container hash from path
HASHID=`echo $ION_CONTAINER_ROOT | grep -Po '/[0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]+'`

#retrieve file name using hash
CONFIGNAME=/mpc/ion/ci_metadata/${HASHID}/build_info*.json

#Try to retrieve version number from build info
VERSION=""
if test -f $CONFIGNAME; then
 VERSION=`cat $CONFIGNAME | jq .container_info.general.release_tag | xargs -n1 echo`
fi

### Launch meshroom ####
PATH_QML=${ION_CONTAINER_ROOT}/base/qml/QtQuick
PATH_QML_TRUE=`readlink -f $PATH_QML`/../
PATH_PLUGIN=${ION_CONTAINER_ROOT}/base/imageformats/
PATH_PLUGIN_TRUE=`readlink -f $PATH_PLUGIN`/../

export QML2_IMPORT_PATH=$PATH_QML_TRUE:$QML2_IMPORT_PATH
export QT_PLUGIN_PATH=$PATH_PLUGIN_TRUE:$QT_PLUGIN_PATH
export ION_MESHROOM_VERSION=$VERSION

python ${ION_CONTAINER_ROOT}/base/meshroom/meshroom/ui "$@"
