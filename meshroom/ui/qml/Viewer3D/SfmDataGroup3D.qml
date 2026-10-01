import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

LayerListGroup {
    id: root

    property var collection: null

    name: "Sfm data"
    emptyText: "No sfmData entries"
    layerList: collection ? collection.sfmData : null
    showPicking: true

    advancedComponent: Component {
        ColumnLayout {
            id: advanced

            property var entry: null
            readonly property var entryLayer: entry ? entry.layer : null
            readonly property var sfmData: entry ? entry.dataObject : null

            spacing: 3

            PropertySlider {
                Layout.fillWidth: true
                icon: MaterialIcons.switch_video
                toolTipName: "ResectionId"
                from: 0
                to: advanced.sfmData && advanced.sfmData.maxResectionId !== undefined ? advanced.sfmData.maxResectionId : 100
                stepSize: 1
                decimals: 0
                defaultValue: to
                target: advanced.sfmData
                propertyName: "limitResectionId"
            }

            PropertySlider {
                Layout.fillWidth: true
                icon: MaterialIcons.videocam
                toolTipName: "Camera Scale"
                from: 0
                to: 2
                stepSize: 0.01
                defaultValue: 1.0
                target: advanced.entryLayer
                propertyName: "cameraSize"
            }

            PropertySlider {
                Layout.fillWidth: true
                icon: MaterialIcons.center_focus_strong
                toolTipName: "Point Size"
                from: 0
                to: 10
                stepSize: 0.01
                defaultValue: 1.0
                target: advanced.entryLayer
                propertyName: "pointSize"
            }

            CheckBox {
                text: "View through camera"
                font.pointSize: 10
                // Reflects the collection's selection, so selecting another SfmData unchecks this one
                checked: root.collection !== null && advanced.sfmData !== null && root.collection.selectedSfmDataObject === advanced.sfmData
                onToggled: root.collection.selectedSfmDataObject = checked ? advanced.sfmData : null
            }
        }
    }
}
