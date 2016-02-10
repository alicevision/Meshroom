import QtQuick 2.5
import QtQuick.Controls 1.4
import ".."
import "."

DropArea {

    id: root
    property bool hideBackground: false
    property string title: ""
    signal filesDropped(variant files)

    onEntered: background.color = Style.window.color.selected
    onExited: background.color = "transparent"
    onDropped: {
        background.color = "transparent";
        (!drag.source) ? filesDropped(drop.urls) : filesDropped([drop.source.url]);
    }
    Rectangle {
        id: background
        anchors.fill: parent;
        visible: !root.hideBackground
        color: "transparent"
        Behavior on color { ColorAnimation {} }
        Image {
            anchors.fill: parent
            source: "qrc:///images/stripes.png"
            fillMode: Image.Tile
            opacity: 0.3
        }
        Text {
            anchors.centerIn: parent
            text: root.title
            font.pixelSize: Style.text.size.large
            color: Style.text.color.dark
        }
    }
}
