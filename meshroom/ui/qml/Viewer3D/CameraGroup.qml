import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import meshViewer

ExpandableGroup {
    id: root

    property var collection: null

    function cameraInfo() {
        if (!root.collection || !root.collection.sceneView)
        {
            return null
        }

        return root.collection.sceneView.cameraInfo
    }
    
    function basecameraInfo() {
        if (!root.collection || !root.collection.sceneView)
        {
            return null
        }

        if (!(root.collection.sceneView.cameraInfo instanceof BaseCameraInfo))
        {
            return null
        }

        return root.collection.sceneView.cameraInfo
    }

    Layout.fillWidth: true
    title: "Camera Properties"

    Component.onCompleted: expanded = false

    Loader {
        id: contentLoader
        active: root.expanded
        width: parent.width
        height: active ? (item ? item.implicitHeight : 0) : 0

        sourceComponent: ColumnLayout {
            width: contentLoader.width
            spacing: 2

            RowLayout {
                width: parent.width
                spacing: 4

                Label {
                    text: "FOV"
                    Layout.preferredWidth: 42
                    color: palette.text
                }

                Slider {
                    Layout.fillWidth: true
                    from: 10
                    to: 120
                    stepSize: 0.1
                    value: root.basecameraInfo() ? root.basecameraInfo().fov : 70.0
                    onMoved: {
                        if (root.basecameraInfo())
                        {
                            root.basecameraInfo().fov = value
                        }
                    }
                    ToolTip.text: "FOV: " + value.toFixed(1)
                    ToolTip.visible: hovered || pressed
                    ToolTip.delay: 100
                }
            }

            RowLayout {
                width: parent.width
                spacing: 4

                Label {
                    text: "Near"
                    Layout.preferredWidth: 42
                    color: palette.text
                }

                Slider {
                    Layout.fillWidth: true
                    from: 0.01
                    to: 10.0
                    stepSize: 0.01
                    value: root.cameraInfo() ? root.cameraInfo().nearPlane : 0.1
                    onMoved: {
                        if (root.cameraInfo())
                        {
                            root.cameraInfo().nearPlane = value
                        }
                    }
                    ToolTip.text: "Near Plane: " + value.toFixed(2)
                    ToolTip.visible: hovered || pressed
                    ToolTip.delay: 100
                }
            }

            RowLayout {
                width: parent.width
                spacing: 4

                Label {
                    text: "Far"
                    Layout.preferredWidth: 42
                    color: palette.text
                }

                Slider {
                    Layout.fillWidth: true
                    from: 10.0
                    to: 100000.0
                    stepSize: 10.0
                    value: root.cameraInfo() ? root.cameraInfo().farPlane : 10000.0
                    onMoved: {
                        if (root.cameraInfo())
                        {
                            root.cameraInfo().farPlane = value
                        }
                    }
                    ToolTip.text: "Far Plane: " + value.toFixed(0)
                    ToolTip.visible: hovered || pressed
                    ToolTip.delay: 100
                }
            }
        }
    }
}
