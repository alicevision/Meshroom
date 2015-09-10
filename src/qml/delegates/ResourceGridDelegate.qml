import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../styles"
import "../components"

Item {

    id: root
    property bool selected: false
    property bool highlighted: false
    property bool enabled: true

    signal itemToggled(int index)
    signal itemDeleted(int index)

    function toggleSelectedState() {
        root.selected = !root.selected;
    }
    function toggleHighlightedState() {
        root.highlighted = !root.highlighted;
    }

    width: GridView.view.cellWidth
    height: GridView.view.cellHeight

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        anchors.margins: 2
        drag.target: tile
        cursorShape: Qt.PointingHandCursor
        hoverEnabled: true
        // acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: {
            (mouse.button == Qt.LeftButton) ? itemToggled(index) : menu.popup();
        }
        onReleased: tile.Drag.drop()
        Rectangle {
            id: tile
            property string url: modelData.url
            color: root.highlighted ? "#A00" : root.selected ? "#5BB1F7" : "#99111111"
            width: mouseArea.width
            height: mouseArea.height
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            Drag.active: mouseArea.drag.active
            Drag.hotSpot.x: tile.width/2
            Drag.hotSpot.y: tile.height/2
            states: State {
                when: mouseArea.drag.active
                ParentChange { target: tile; parent: _mainLoader }
                AnchorChanges { target: tile; anchors.verticalCenter: undefined; anchors.horizontalCenter: undefined }
            }
        }
        Image {
            anchors.fill: parent
            anchors.margins: 2
            sourceSize.width: parent.width
            sourceSize.height: parent.height
            source: modelData.url
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            Rectangle {
                id: container
                width: parent.width
                height: childrenRect.height
                color: "#99000000"
                Behavior on height { NumberAnimation {} }
                Text {
                    width: parent.width
                    text: modelData.name
                    verticalAlignment: Text.AlignVCenter
                    color: "white"
                    font.pixelSize: 10
                    elide: Text.ElideRight
                    wrapMode: Text.WrapAnywhere
                    maximumLineCount: (mouseArea.containsMouse) ? 4 : 1
                }
            }
            Item { // pair indicator
                anchors.fill: parent
                visible: (modelData.isPairImageA || modelData.isPairImageB)
                Rectangle {
                    anchors.fill: parent
                    color: "black"
                    opacity: 0.5
                }
                CustomText {
                    anchors.centerIn: parent
                    text: modelData.isPairImageA ? "A" : "B"
                    textSize: _style.text.size.xlarge
                    color: "#5BB1F7"
                }
            }
            Rectangle { // state indicator (enabled or not)
                anchors.fill: parent
                visible: !root.enabled
                color: "black"
                opacity: 0.5
            }
        }
    }
}
