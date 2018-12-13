import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2
import MaterialIcons 2.2
import Utils 1.0

/**
  A component to display and edit a Node's attributes.
*/
ColumnLayout {
    id: root

    property variant node: null  // the node to edit
    property bool readOnly: false
    readonly property bool isCompatibilityNode: node.hasOwnProperty("compatibilityIssue")

    signal upgradeRequest()

    signal attributeDoubleClicked(var attribute)

    spacing: 0

    Pane {
        Layout.fillWidth: true
        background: Rectangle { color: Qt.darker(parent.palette.window, 1.15) }
        padding: 2

        RowLayout {
            width: parent.width

            Label {
                Layout.fillWidth: true
                elide: Text.ElideMiddle
                text: node.label
                horizontalAlignment: Text.AlignHCenter
                padding: 6
            }

            ToolButton {
                text: MaterialIcons.settings
                font.family: MaterialIcons.fontFamily
                onClicked: settingsMenu.popup()
                checkable: true
                checked: settingsMenu.visible
            }
        }
        Menu {
            id: settingsMenu
            MenuItem {
                text: "Advanced Attributes"
                checked: GraphEditorSettings.showAdvancedAttributes
                onClicked: GraphEditorSettings.showAdvancedAttributes = !GraphEditorSettings.showAdvancedAttributes
            }
            MenuItem {
                text: "Open Cache Folder"
                onClicked: Qt.openUrlExternally(Filepath.stringToUrl(node.internalFolder))
                ToolTip.text: node.internalFolder
                ToolTip.visible: hovered
                ToolTip.delay: 500
            }
            MenuSeparator {}
            MenuItem {
                text: "Clear Submitted Status"
                onClicked: node.clearSubmittedChunks()
            }
        }
    }

    // CompatibilityBadge banner for CompatibilityNode
    Loader {
        active: isCompatibilityNode
        Layout.fillWidth: true
        visible: active  // for layout update

        sourceComponent: CompatibilityBadge {
            canUpgrade: root.node.canUpgrade
            issueDetails: root.node.issueDetails
            onUpgradeRequest: root.upgradeRequest()
            sourceComponent: bannerDelegate
        }
    }

    StackLayout {
        Layout.fillHeight: true
        Layout.fillWidth: true

        currentIndex: tabBar.currentIndex

        Item {

            ListView {
                id: attributesListView

                anchors.fill: parent
                anchors.margins: 2
                clip: true
                spacing: 2
                ScrollBar.vertical: ScrollBar { id: scrollBar }

                model: SortFilterDelegateModel {

                    model: node ? node.attributes : null
                    filterRole: GraphEditorSettings.showAdvancedAttributes ? "" : "advanced"
                    filterValue: false
                    function modelData(item, roleName) {
                        return item.model.object.desc[roleName]
                    }

                    Component {
                        id: delegateComponent
                        AttributeItemDelegate {
                            width: attributesListView.width - scrollBar.width
                            readOnly: root.isCompatibilityNode
                            labelWidth: 180
                            attribute: object
                            onDoubleClicked: root.attributeDoubleClicked(attr)
                        }
                    }
                }

                // Helper MouseArea to lose edit/activeFocus
                // when clicking on the background
                MouseArea {
                    anchors.fill: parent
                    onClicked: root.forceActiveFocus()
                    z: -1
                }
            }
        }

        NodeLog {
            id: nodeLog

            Layout.fillHeight: true
            Layout.fillWidth: true
            node: root.node

        }
    }
    TabBar {
        id: tabBar

        Layout.fillWidth: true
        width: childrenRect.width
        position: TabBar.Footer
        TabButton {
            text: "Attributes"
            width: implicitWidth
            padding: 4
            leftPadding: 8
            rightPadding: leftPadding
        }
        TabButton {
            text: "Log"
            width: implicitWidth
            leftPadding: 8
            rightPadding: leftPadding
        }
    }
}
