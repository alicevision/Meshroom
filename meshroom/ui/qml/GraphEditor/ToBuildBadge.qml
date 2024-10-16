import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.11
import MaterialIcons 2.2

Loader {
    id: root

    sourceComponent: iconDelegate

    signal doBuild()

    property Component iconDelegate: Component {

        Label {
            text: MaterialIcons.warning
            font.family: MaterialIcons.fontFamily
            font.pointSize: 12
            color: "#66207F"

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                onPressed: mouse.accepted = false
                ToolTip.text: "Node env needs to be built"
                ToolTip.visible: containsMouse
            }
        }
    }

    property Component bannerDelegate: Component {

        Pane {
            padding: 6
            clip: true
            background: Rectangle { color: "#66207F" }

            RowLayout {
                width: parent.width
                Column {
                    Layout.fillWidth: true
                    Label {
                        width: parent.width
                        elide: Label.ElideMiddle
                        font.bold: true
                        text: "Env needs to be built"
                        color: "white"
                    }
                    Label {
                        width: parent.width
                        elide: Label.ElideMiddle
                        color: "white"
                    }
                }
                Button {
                    visible: (parent.width > width) ? 1 : 0
                    palette.window: root.color
                    palette.button: Qt.darker(root.color, 1.2)
                    palette.buttonText: "white"
                    text: "Build"
                    onClicked: doBuild()
                }
            }
        }
    }
}
