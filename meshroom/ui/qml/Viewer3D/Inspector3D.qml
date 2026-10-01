import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

FloatingPane {
    id: root

    implicitWidth: 200
    opaque: true
    property var collection: null
    readonly property bool hasImageContent: root.collection && root.collection.sceneView && root.collection.sceneView.imageLayerRef
                                          && root.collection.sceneView.imageLayerRef.source !== undefined
                                          && root.collection.sceneView.imageLayerRef.source.length > 0
    readonly property bool hasMeshContent: root.collection && root.collection.meshModel.count > 0
    readonly property bool hasSfmDataContent: root.collection && root.collection.sfmDataModel.count > 0
    readonly property bool hasDepthmapContent: root.collection && root.collection.depthmapModel.count > 0
    readonly property bool hasAnyContent: hasImageContent || hasMeshContent || hasSfmDataContent || hasDepthmapContent

    padding: 0

    MouseArea {
        anchors.fill: parent
        onWheel: function(wheel) {
            wheel.accepted = true
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        CameraGroup {
            Layout.fillWidth: true
            visible: root.collection && root.collection.selectedSfmDataObject === null
            collection: root.collection
        }

        Group {
            title: "3D Objects"
            Layout.fillWidth: true
            Layout.fillHeight: true
            sidePadding: 0
            visible: hasAnyContent

            ColumnLayout {
                anchors.fill: parent
                spacing: 4

                ImageGroup3D {
                    visible: hasImageContent
                    collection: root.collection
                }

                MeshesGroup3D {
                    Layout.fillHeight: hasMeshContent && !hasSfmDataContent
                    visible: hasMeshContent
                    collection: root.collection
                }

                SfmDataGroup3D {
                    Layout.fillHeight: true
                    visible: hasSfmDataContent
                    collection: root.collection
                }

                DepthmapGroup3D {
                    Layout.fillHeight: true
                    visible: hasDepthmapContent
                    collection: root.collection
                }

                Item {
                    visible: !hasSfmDataContent && !hasMeshContent && !hasDepthmapContent
                    Layout.fillHeight: true
                }
            }
        }

        Label {
            visible: root.collection && !hasAnyContent
            text: "No 3D content"
            color: palette.mid
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
            Layout.fillHeight: true
            verticalAlignment: Text.AlignVCenter
        }

        Label {
            visible: !root.collection
            text: "Waiting for Viewer3D collection..."
            color: palette.mid
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
            Layout.fillHeight: true
            verticalAlignment: Text.AlignVCenter
        }
    }
}
