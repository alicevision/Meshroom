import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Inspector3DUtils.js" as Inspector3DUtils

import MaterialIcons 2.2

/**
 * ListView delegate for one entry of a LayerList: selection bar, loading/remove button, label,
 * visibility / picking toggles and an optional expandable advanced section.
 *
 * @p advancedComponent root item must declare `property var entry`; it is bound to this row's entry.
 */
MouseArea {
    id: root

    required property int index
    required property string label

    property LayerList layerList: null
    property bool showPicking: false
    property Component advancedComponent: null
    property bool expanded: false

    readonly property var entry: {
        if (!layerList)
        {
            return null
        }

        // entryAt() is not notifiable: depend on revision to re-evaluate when entries are (re)created
        layerList.revision
        return layerList.entryAt(index)
    }
    readonly property var entryLayer: entry ? entry.layer : null
    readonly property bool loading: entry ? entry.loading : false
    readonly property bool isCurrent: ListView.isCurrentItem

    hoverEnabled: true
    height: content.implicitHeight

    onClicked: ListView.view.currentIndex = index

    ColumnLayout {
        id: content
        width: parent.width
        spacing: 3

        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 2
                color: root.isCurrent ? palette.highlight
                     : root.containsMouse ? Qt.darker(palette.highlight, 1.5)
                     : "transparent"
            }

            LoadingRemoveButton {
                loading: root.loading
                onRemoveRequested: root.layerList.remove(root.index)
            }

            Label {
                Layout.fillWidth: true
                text: root.label.length > 0 ? root.label : Inspector3DUtils.randomLabel(root.index, root.layerList.typeName)
                color: palette.text
                elide: Text.ElideMiddle
                font.weight: root.isCurrent ? Font.DemiBold : Font.Normal
                topPadding: 3
                bottomPadding: topPadding
            }

            ToggleIconButton {
                enabled: root.entryLayer !== null
                active: root.entryLayer ? root.entryLayer.visible : true
                activeIcon: MaterialIcons.visibility
                inactiveIcon: MaterialIcons.visibility_off
                activeToolTip: "Visible"
                inactiveToolTip: "Hidden"
                onClicked: root.entryLayer.visible = !root.entryLayer.visible
            }

            ToggleIconButton {
                visible: root.showPicking
                enabled: root.entryLayer !== null
                active: root.entryLayer ? root.entryLayer.picking : true
                activeIcon: MaterialIcons.touch_app
                activeToolTip: "Pickable"
                inactiveToolTip: "Not Pickable"
                onClicked: root.entryLayer.picking = !root.entryLayer.picking
            }

            ToggleIconButton {
                visible: root.advancedComponent !== null
                enabled: !root.loading
                active: root.expanded
                inactiveOpacity: 1.0
                activeIcon: MaterialIcons.keyboard_arrow_down
                inactiveIcon: MaterialIcons.keyboard_arrow_right
                activeToolTip: "Hide Advanced"
                inactiveToolTip: "Show Advanced"
                onClicked: root.expanded = !root.expanded
            }
        }

        Loader {
            Layout.fillWidth: true
            Layout.leftMargin: 12
            Layout.rightMargin: 8
            active: root.expanded && root.entry !== null
            visible: active
            sourceComponent: root.advancedComponent
            onLoaded: item.entry = Qt.binding(() => root.entry)
        }
    }
}
