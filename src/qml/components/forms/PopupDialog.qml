import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../../styles"

Rectangle {

    id: root

    property string text: ''

    function popup(message) {
        root.text = message;
        root.height = Math.max(popupText.height, 25);
        timer.start();
    }
    function close() {
        root.height = 0;
    }

    anchors.bottom: parent.bottom
    width: parent.width
    color: "#DAA520"
    z: 9999
    height: 0
    Behavior on height { NumberAnimation {}}

    Timer {
        id: timer
        interval: 3000; running: false; repeat: false
        onTriggered: close()
    }

    RowLayout {
        anchors.fill: parent
        Item {
            width: 24
            height: 24
            Image {
                anchors.fill: parent
                source: 'qrc:/images/information_outline.svg'
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Text {
                id: popupText
                width: parent.width
                text: root.text
                color: "white"
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                wrapMode: Text.WrapAnywhere
                font.pointSize: 12
            }
        }
    }
}
