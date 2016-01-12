import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Item {

    id: root
    objectName: "resourceDelegate"

    property bool selected: false
    property bool isPairA: false
    property bool isPairB: false

    signal itemToggled(int index, bool doClear)
    signal performMultiSelection(int index)
    signal viewInFullscreen(string url)

    function refreshInitialPairIndicators() {
        root.isPairA = currentJob.modelData.isPairA(model.url);
        root.isPairB = currentJob.modelData.isPairB(model.url);
    }
    function refreshSelectionState() {
        selected = isSelected(index);
    }

    Component.onCompleted: refreshInitialPairIndicators()

    Menu {
        id: contextMenu
        MenuItem {
            text: root.selected ? "Unselect" : "Select"
            onTriggered: itemToggled(index, false)
        }
        MenuItem {
            text: "View in fullscreen"
            onTriggered: viewInFullscreen(model.url)
        }
        MenuSeparator {}
        MenuItem {
            text: "Open parent directory"
            onTriggered: {
                var urlStr = model.url.toString();
                Qt.openUrlExternally(urlStr.substring(0, urlStr.lastIndexOf('/')));
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        anchors.margins: 2
        cursorShape: Qt.PointingHandCursor
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: {
            if(mouse.button == Qt.LeftButton){
                if(mouse.modifiers & Qt.ShiftModifier) {
                    performMultiSelection(index);
                    return;
                }
                if(mouse.modifiers & Qt.ControlModifier) {
                    itemToggled(index, false);
                    return;
                }
                if(mouse.button == Qt.LeftButton){
                    itemToggled(index, true);
                    return;
                }
            }
            contextMenu.popup();
        }
        Rectangle {
            id: tile
            property string url: model.url
            color: {
                if(root.selected)
                    return Style.window.color.selected;
                if(mouseArea.containsMouse)
                    return Style.window.color.xlight;
                return Style.window.color.dark;
            }
            width: mouseArea.width
            height: mouseArea.height
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
        }
        Image {
            anchors.fill: parent
            anchors.margins: 2
            sourceSize.width: 320
            sourceSize.height: 320
            source: model.url
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            Rectangle {
                id: container
                width: parent.width
                height: childrenRect.height
                Behavior on height { NumberAnimation {} }
                color: "#66111111"
                Text {
                    width: parent.width
                    text: model.name
                    color: Style.text.color.xlight
                    font.pixelSize: Style.text.size.xsmall
                    maximumLineCount: (mouseArea.containsMouse) ? 4 : 1
                }
            }
            Item {
                id: pairIndicator
                anchors.fill: parent
                visible: root.isPairA || root.isPairB
                Rectangle {
                    anchors.fill: parent
                    color: "black"
                    opacity: 0.5
                }
                Text {
                    anchors.centerIn: parent
                    text: root.isPairA ? "A" : "B"
                    font.pixelSize: Style.text.size.xlarge
                    color: Style.text.color.selected
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
