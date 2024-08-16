import QtQuick 2.15
import MaterialIcons 2.2
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.11

/*
* IntSelector with arrows and a text input to select a number
*/

Item {
    id: root

    property int value: 0
    property var range: { "min" : 0, "max" : 0 }

    Layout.preferredWidth: previousIntButton.width + intMetrics.width + nextIntButton.width
    Layout.preferredHeight: intInput.height

    MouseArea {
        id: mouseAreaIntLabel

        anchors.fill: parent

        hoverEnabled: true

        onEntered: {
            previousIntButton.opacity = 1
            nextIntButton.opacity = 1
        }

        onExited: {
            previousIntButton.opacity = 0
            nextIntButton.opacity = 0
        } 

        MaterialToolButton {
            id: previousIntButton

            anchors.verticalCenter: mouseAreaIntLabel.verticalCenter

            opacity: 0
            width: 10
            text: MaterialIcons.navigate_before
            ToolTip.text: "Previous Integer"

            onClicked: {
                if (value > range.min) {
                    value -= 1
                }
            }
        }

        TextInput {
            id: intInput

            anchors.horizontalCenter: mouseAreaIntLabel.horizontalCenter
            anchors.verticalCenter: mouseAreaIntLabel.verticalCenter
            Layout.preferredWidth: intMetrics.width

            color: palette.text
            horizontalAlignment: Text.AlignHCenter
            selectByMouse: true

            text: value

            onEditingFinished: {
                // We first assign the frame to the entered text even if it is an invalid frame number. We do it for extreme cases, for example without doing it, if we are at 0, and put a negative number, value would be still 0 and nothing happens but we will still see the wrong number
                value = parseInt(text)
                value = Math.min(range.max, Math.max(range.min, parseInt(text)))
                focus = false
            }
        }

        MaterialToolButton {
            id: nextIntButton

            anchors.right: mouseAreaIntLabel.right
            anchors.verticalCenter: mouseAreaIntLabel.verticalCenter

            width: 10
            opacity: 0
            text: MaterialIcons.navigate_next
            ToolTip.text: "Next Integer"

            onClicked: {
                if (value < range.max) {
                    value += 1
                }
            }
        }

        TextMetrics {
            id: intMetrics

            font: intInput.font
            text: "10000"
        }
    }


}