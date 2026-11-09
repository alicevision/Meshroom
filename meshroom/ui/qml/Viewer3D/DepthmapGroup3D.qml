import QtQuick

LayerListGroup {
    property var collection: null

    name: "Depth Maps"
    emptyText: "No depth map entry"
    layerList: collection ? collection.depthmaps : null
}
