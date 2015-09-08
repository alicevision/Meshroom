import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

Item {

    id: root
    property string title: ""
    property bool enabled: true
    signal filesDropped(variant files)

    DropArea {
        anchors.fill: parent
        enabled: root.enabled
        onEntered: dropBackground.color = _style.window.color.selected
        onExited: dropBackground.color = _style.window.color.darker
        onDropped: {
            dropBackground.color = _style.window.color.darker;
            (!drag.source) ? filesDropped(drop.urls) : filesDropped([drop.source.url]);
        }
        Rectangle {
            id: dropBackground
            anchors.fill: parent;
            color: _style.window.color.darker
            Behavior on color { ColorAnimation {} }
            Image {
                anchors.fill: parent
                source: "qrc:///images/stripes.png"
                fillMode: Image.Tile
                opacity: 0.5
            }
            CustomText {
                anchors.centerIn: parent
                text: root.title
                textSize: _style.text.size.large
                color: _style.window.color.xlighter
            }
        }
    }
}
