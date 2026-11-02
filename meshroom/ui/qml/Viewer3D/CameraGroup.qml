import QtQuick
import QtQuick.Layouts

import Controls 1.0
import meshViewer

ExpandableGroup {
    id: root

    property var collection: null
    readonly property var cameraInfo: collection && collection.sceneView ? collection.sceneView.cameraInfo : null

    Layout.fillWidth: true
    title: "Camera Properties"

    Component.onCompleted: expanded = false

    // GroupBox sizes from its content's implicitHeight, which Loader keeps after unloading
    Item {
        width: parent.width
        implicitHeight: contentLoader.active && contentLoader.item ? contentLoader.item.implicitHeight : 0

        Loader {
            id: contentLoader
            active: root.expanded
            width: parent.width

            sourceComponent: ColumnLayout {
                spacing: 2

                PropertySlider {
                    Layout.fillWidth: true
                    label: "FOV"
                    showValue: false
                    decimals: 1
                    from: 10
                    to: 120
                    stepSize: 0.1
                    defaultValue: 70.0
                    // FOV is only editable on the free camera, not on SfM camera intrinsics
                    target: root.cameraInfo instanceof BaseCameraInfo ? root.cameraInfo : null
                    propertyName: "fov"
                }

                PropertySlider {
                    Layout.fillWidth: true
                    label: "Near"
                    toolTipName: "Near Plane"
                    showValue: false
                    from: 0.01
                    to: 10.0
                    stepSize: 0.01
                    defaultValue: 0.1
                    target: root.cameraInfo
                    propertyName: "nearPlane"
                }

                PropertySlider {
                    Layout.fillWidth: true
                    label: "Far"
                    toolTipName: "Far Plane"
                    showValue: false
                    decimals: 0
                    from: 10.0
                    to: 100000.0
                    stepSize: 10.0
                    defaultValue: 10000.0
                    target: root.cameraInfo
                    propertyName: "farPlane"
                }
            }
        }
    }
}
