import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

Item {

    id: root

    signal filesDropped(variant files)

    DropArea {
        anchors.fill: parent
        onEntered: dropBackground.color = _style.window.color.selected
        onExited: dropBackground.color = _style.window.color.normal
        onDropped: {
            dropBackground.color = _style.window.color.lighter
            filesDropped(drop.urls);
        }
        Rectangle {
            id: dropBackground
            anchors.fill: parent;
            color: "#222"
            Behavior on color { ColorAnimation {} }
            Image {
                anchors.fill: parent
                source: "qrc:///images/stripes.png"
                fillMode: Image.Tile
                opacity: 0.3
            }
            CustomText {
                anchors.centerIn: parent
                text: "drop area"
                textSize: _style.text.size.large
                color: _style.window.color.xlighter
            }
        }
    }
}
