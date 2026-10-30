import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0

/**
 * A component to display and edit the attributes of a Node.
 */

ListView {
    id: root
    property bool readOnly: false
    property int labelWidth: 180
    property bool objectsHideable: true
    property string filterText: ""
    // AnySet child attribute whose description is being edited in the form under its row
    property var editedAnySetAttribute: null

    signal upgradeRequest()
    signal attributeDoubleClicked(var mouse, var attribute)
    signal inAttributeClicked(var srcItem, var mouse, var inAttributes)
    signal outAttributeClicked(var srcItem, var mouse, var outAttributes)
    signal showInViewer(var attribute)

    implicitHeight: contentHeight

    spacing: 2
    clip: true
    ScrollBar.vertical: MScrollBar { id: scrollBar }

    delegate: Loader {
        active: !object.hasDisplayableShape && (object.enabled || object.hasAnyOutputLinks) && (
            !objectsHideable
            || ((!object.desc.advanced || GraphEditorSettings.showAdvancedAttributes)
            && (object.isDefault && GraphEditorSettings.showDefaultAttributes || !object.isDefault && GraphEditorSettings.showModifiedAttributes)
            && (object.isOutput && GraphEditorSettings.showOutputAttributes || !object.isOutput && GraphEditorSettings.showInputAttributes)
            && (object.hasAnyInputLinks && GraphEditorSettings.showLinkAttributes || !object.isLink && GraphEditorSettings.showNotLinkAttributes))
            ) && object.matchText(filterText)
        visible: active

        sourceComponent: Item {
            id: delegateItem
            readonly property bool editing: root.editedAnySetAttribute === object

            width: root.width - scrollBar.width
            implicitHeight: delegateLayout.implicitHeight

            // Highlight the attribute while its description is being edited
            Rectangle {
                visible: delegateItem.editing
                width: parent.width
                height: attributeDelegate.height
                color: Qt.rgba(palette.highlight.r, palette.highlight.g, palette.highlight.b, 0.2)
            }
            Rectangle {
                visible: delegateItem.editing
                anchors.fill: parent
                color: "transparent"
                border.color: palette.highlight
                radius: 2
                z: 1
            }

            ColumnLayout {
                id: delegateLayout
                width: parent.width
                spacing: 0

                AttributeItemDelegate {
                    id: attributeDelegate
                    Layout.fillWidth: true
                    readOnly: root.readOnly
                    labelWidth: root.labelWidth
                    filterText: root.filterText
                    objectsHideable: root.objectsHideable
                    attribute: object

                    onDoubleClicked: function(mouse, attr) {
                        root.attributeDoubleClicked(mouse, attr)
                    }
                    onInAttributeClicked: function(srcItem, mouse, inAttributes) {
                        root.inAttributeClicked(srcItem, mouse, inAttributes)
                    }
                    onOutAttributeClicked: function(srcItem, mouse, outAttributes) {
                        root.outAttributeClicked(srcItem, mouse, outAttributes)
                    }

                    onShowInViewer: function(attr) {
                        root.showInViewer(attr)
                    }

                    onEditAnySetAttributeRequested: function(attr) {
                        root.editedAnySetAttribute = attr
                    }
                }

                Loader {
                    active: delegateItem.editing
                    visible: active
                    Layout.fillWidth: true
                    sourceComponent: AnySetAttributeEditor {
                        targetAttribute: object
                        onClosed: root.editedAnySetAttribute = null
                    }
                }
            }
        }

        onActiveChanged: height = active ? item.implicitHeight : -spacing

        Connections {
            target: item
            function onImplicitHeightChanged() {
                // Handles cases where an attribute is created and its height is then updated as it is filled
                height = item.implicitHeight
            }
        }
    }

    // Helper MouseArea to lose edit/activeFocus when clicking on the background
    MouseArea {
        anchors.fill: parent
        onClicked: forceActiveFocus()
        z: -1
    }
}
