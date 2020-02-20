import QtQuick 2.11
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Controls 1.0

FloatingPane {
    id: root
    anchors.margins: 0
    padding: 5
    radius: 0

    property real gammaDefaultValue: 1
    property real offsetDefaultValue: 0
    property real gammaValue: gammaCtrl.value
    property real offsetValue: offsetCtrl.value
    property string channelModeValue: channelsCtrl.value

    background: Rectangle { color: root.palette.window }

    RowLayout {
        id: toolLayout
        anchors.verticalCenter: parent
        anchors.fill: parent

        // channel mode
        ComboBox {
            id: channelsCtrl

            // set min size to 4 characters + one margin for the combobox
            Layout.minimumWidth: 5.0 * Qt.application.font.pixelSize
            Layout.preferredWidth: Layout.minimumWidth
            flat: true

            property var channels: ["rgba", "rgb", "r", "g", "b","a"]
            property string value: channels[currentIndex]

            model: channels
        }

        // gamma slider
        RowLayout {
            spacing: 5

            ToolButton {
                text: "γ"

                background: Rectangle {
                    color: "transparent"
                    border.color: "transparent"
                }

                onClicked: {
                    gammaCtrl.value = gammaDefaultValue;
                }
            }

            Slider {
                id: gammaCtrl
                Layout.fillWidth: true
                from: 0
                to: 3
                value: 1
                stepSize: 0.01
            }

            Label {
                text: gammaValue.toFixed(2)
            }
        }

        // space
        Item {
            width: 20
        }

        // offset slider
        RowLayout {
            spacing: 5

            ToolButton {
                text: "Offset"

                background: Rectangle {
                    color: "transparent"
                    border.color: "transparent"
                }

                onClicked: {
                    offsetCtrl.value = offsetDefaultValue;
                }
            }

            Slider {
                id: offsetCtrl
                Layout.fillWidth: true
                from: -1
                to: 1
                value: 0
                stepSize: 0.01
            }

            Label {
                text: offsetValue.toFixed(2)
            }
        }
    }
}
