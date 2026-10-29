import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2

// Non-collapsible group exposing the point layer settings
Group {
    id: root

    property var collection: null
    readonly property var pointLayer: collection && collection.sceneView ? collection.sceneView.pointLayerRef : null

    Layout.fillWidth: true
    title: "Point Layer"

    PropertySlider {
        width: parent.width
        icon: MaterialIcons.circle
        toolTipName: "Point Size"
        from: 1
        to: 25
        stepSize: 1
        decimals: 0
        defaultValue: 15
        target: root.pointLayer
        propertyName: "size"
    }
}
