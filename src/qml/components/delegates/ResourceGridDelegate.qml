import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../../styles"

Item {

    id: root
    property bool selected: false
    property bool highlighted: false

    signal itemClicked(int index)
    signal itemDoubleClicked(int index)

    function toggleSelectedState() {
        root.selected = !root.selected;
    }
    function toggleHighlightedState() {
        root.highlighted = !root.highlighted;
    }

    width: GridView.view.cellWidth
    height: GridView.view.cellHeight

    Rectangle {
        id: background
        anchors.fill: parent
        anchors.margins: 5
        color: root.highlighted ? "#A00" : root.selected ? "#5BB1F7" : "#111"
        MouseArea {
            id: thumbMouseArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                itemClicked(index);
            }
            onDoubleClicked: {
                itemDoubleClicked(index);
            }
        }
    }
    Image {
        anchors.fill: parent
        anchors.margins: 8
        sourceSize.width: parent.width
        sourceSize.height: parent.height
        source: modelData.isDir() ? 'qrc:/images/folder_outline.svg' : modelData.url
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        Rectangle {
            id: container
            property int topMargin: (thumbMouseArea.containsMouse) ? 20 : 10
            width: parent.width
            height: childrenRect.height + topMargin
            color: "#AA000000"
            Behavior on height { NumberAnimation {} }
            Text {
                y: container.topMargin/2
                Behavior on y { NumberAnimation {} }
                width: parent.width
                text: modelData.name
                verticalAlignment: Text.AlignVCenter
                color: "white"
                font.pointSize: 10
                elide: Text.ElideRight
                wrapMode: Text.WrapAnywhere
                maximumLineCount: (thumbMouseArea.containsMouse) ? 4 : 1
            }
        }
    }

}
