import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

import "../styles"

Item {

    id: root

    signal filesDropped(variant files)

    DropArea {
        anchors.fill: parent
        onEntered: dropBackground.color = "#5BB1F7"
        onExited: dropBackground.color = "#222"
        onDropped: {
            dropBackground.color = "#222";
            filesDropped(drop.urls);
        }
        Rectangle {
            id: dropBackground
            anchors.fill: parent;
            color: "#222"
            Behavior on color { ColorAnimation {} }
            Image {
                anchors.fill: parent
                source: "qrc:/images/stripes.png"
                fillMode: Image.Tile
                opacity: 0.3
            }
            Text {
                anchors.centerIn: parent
                color: "#444"
                text: "drop area"
                font.pointSize: 18
            }
        }
    }
}
