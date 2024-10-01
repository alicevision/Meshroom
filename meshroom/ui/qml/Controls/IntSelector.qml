import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2

/*
* IntSelector with arrows and a text input to select a number
*/

Row {
    id: root

    property string tooltipText: ""
    property int value: 0
    property var range: { "min" : 0, "max" : 0 }

    Layout.alignment: Qt.AlignVCenter

    spacing: 0
    property bool displayButtons: previousIntButton.hovered || intInputMouseArea.containsMouse || nextIntButton.hovered
    property real buttonsOpacity: displayButtons ? 1.0 : 0.0

    MaterialToolButton {
        id: previousIntButton

        opacity: buttonsOpacity
        width: 10
        text: MaterialIcons.navigate_before
        ToolTip.text: "Previous"

        onClicked: {
            if (value > range.min) {
                value -= 1
            }
        }
    }

    TextInput {
        id: intInput

        ToolTip.text: tooltipText
        ToolTip.visible: tooltipText && intInputMouseArea.containsMouse

        width: intMetrics.width
        height: previousIntButton.height

        color: palette.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        selectByMouse: true

        text: value

        onEditingFinished: {
            // We first assign the frame to the entered text even if it is an invalid frame number. We do it for extreme cases, for example without doing it, if we are at 0, and put a negative number, value would be still 0 and nothing happens but we will still see the wrong number
            value = parseInt(text)
            value = Math.min(range.max, Math.max(range.min, parseInt(text)))
            focus = false
        }

        MouseArea {
            id: intInputMouseArea
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
            propagateComposedEvents: true
        }
    }

    MaterialToolButton {
        id: nextIntButton

        width: 10
        opacity: buttonsOpacity
        text: MaterialIcons.navigate_next
        ToolTip.text: "Next"

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