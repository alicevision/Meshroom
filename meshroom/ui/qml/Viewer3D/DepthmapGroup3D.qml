import QtQuick

LayerListGroup {
    property var collection: null

    name: "Depthmaps"
    emptyText: "No depthmap entries"
    layerList: collection ? collection.depthmaps : null
}
