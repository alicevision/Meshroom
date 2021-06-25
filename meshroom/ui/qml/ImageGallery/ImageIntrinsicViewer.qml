import QtQuick 2.9
import QtQuick.Controls 2.4
import QtQuick.Controls 1.4 as Controls1 // SplitView
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Controls 1.0


/**
 * NodeEditor allows to visualize and edit the parameters of a Node.
 * It mainly provides an attribute editor and a log inspector.
 */
Panel {
    id: root

    property variant intrinsics
    property bool readOnly: false

    signal attributeDoubleClicked(var mouse, var attribute)
    signal upgradeRequest()

    ColumnLayout {
        anchors.fill: parent

        Loader {
            Layout.fillHeight: true
            Layout.fillWidth: true
            sourceComponent: root.intrinsics ? editor_component : placeholder_component

            Component {
                id: placeholder_component

                Item {
                    Column {
                        anchors.centerIn: parent
                        MaterialLabel {
                            text: MaterialIcons.select_all
                            font.pointSize: 34
                            color: Qt.lighter(palette.mid, 1.2)
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        Label {
                            color: Qt.lighter(palette.mid, 1.2)
                            text: "Select a Node to access its Details"
                        }
                    }
                }
            }

            Component {
                id: editor_component

                Controls1.SplitView {
                    anchors.fill: parent

                    StackLayout {
                        Layout.fillHeight: true
                        Layout.fillWidth: true

                        currentIndex: 0

                        ImageIntrinsicEditor {
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            model: root.intrinsics.value
                        }

                    }
                }
            }
        }
    }
}
