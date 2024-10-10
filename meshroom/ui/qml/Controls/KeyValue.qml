import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * KeyValue allows to create a list of key/value, like a table.
 */

Rectangle {
    property alias key: keyLabel.text
    property alias value: valueText.text

    color: activePalette.window

    width: parent.width
    height: childrenRect.height

    RowLayout {
        width: parent.width
        Rectangle {
            anchors.margins: 2
            color: Qt.darker(activePalette.window, 1.1)
            Layout.minimumWidth: 10.0 * Qt.application.font.pixelSize
            Layout.maximumWidth: 15.0 * Qt.application.font.pixelSize
            Layout.fillWidth: false
            Layout.fillHeight: true
            Label {
                id: keyLabel
                text: "test"
                anchors.fill: parent
                anchors.top: parent.top
                topPadding: 4
                leftPadding: 6
                verticalAlignment: TextEdit.AlignTop
                elide: Text.ElideRight
            }
        }
        TextArea {
            id: valueText
            text: ""
            anchors.margins: 2
            Layout.fillWidth: true
            wrapMode: Label.WrapAtWordBoundaryOrAnywhere
            textFormat: TextEdit.PlainText

            readOnly: true
            selectByMouse: true
            background: Rectangle {
                anchors.fill: parent
                color: Qt.darker(activePalette.window, 1.05)
            }
        }
    }
}
