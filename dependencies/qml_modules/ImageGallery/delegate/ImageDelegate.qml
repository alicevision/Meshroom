import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Package {

    id: root
    property bool selected: false
    property bool editable: true
    signal selectContiguous(int id)
    signal selectExtended(int id)
    signal selectOne(int id)
    signal unselect(int id)
    signal unselectAll()
    signal removeSelected()
    signal removeOne(int id)

    Component.onCompleted: selected = _selector.isSelected(index)
    Connections {
        target: _selector
        onRefreshSelectionFlags: root.selected = _selector.isSelected(index)
    }

    function handleMouseEvent(mouse) {
        if(mouse.button == Qt.LeftButton) {
            if(mouse.modifiers & Qt.ShiftModifier) {
                selectContiguous(index);
                return;
            }
            if(mouse.modifiers & Qt.ControlModifier) {
                root.selected ? unselect(index) : selectExtended(index);
                return;
            }
            if(mouse.button == Qt.LeftButton) {
                root.selected ? unselect(index) : selectOne(index);
                return;
            }
        }
        selectOne(index);
        contextMenu.popup();
    }

    Item {
        Package.name: 'list'
        width: ListView.view ? ListView.view.width : 0
        height: ListView.view ? ListView.view.height : 0
        clip: true
        Rectangle {
            anchors.fill: parent
            color: "black"
            Image {
                anchors.fill: parent
                source: model.url
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                BusyIndicator {
                    anchors.centerIn: parent
                    running: parent.status === Image.Loading
                }
            }
        }
    }

    Item {
        Package.name: 'detail'
        width: ListView.view ? ListView.view.width : 0
        height: ListView.view ? ListView.view.cellHeight : 0
        clip: true
        MouseArea {
            id: detailMouseArea
            anchors.fill: parent
            anchors.margins: 2
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: handleMouseEvent(mouse)
        }
        Rectangle {
            anchors.fill: parent
            color: {
                if(root.selected)
                    return Style.window.color.selected;
                if(detailMouseArea.containsMouse)
                    return Style.window.color.xlight;
                return Style.window.color.dark;
            }
            opacity: 0.2
        }
        RowLayout {
            anchors.fill: parent
            spacing: 0
            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: Math.min(parent.height*4/3.0, parent.width*0.4)
                color: "black"
                Image {
                    anchors.fill: parent
                    source: model.url
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    sourceSize: Qt.size(320, 320)
                    BusyIndicator {
                        anchors.centerIn: parent
                        running: parent.status === Image.Loading
                    }
                }
            }
            Text {
                text: model.url.toString().replace("file://", "")
            }
        }
    }

    Item {
        Package.name: 'grid'
        width: GridView.view.cellWidth
        height: GridView.view.cellHeight
        clip: true
        Keys.onPressed: {
            if(!root.editable)
                return;
            if (event.key == Qt.Key_Backspace || event.key == Qt.Key_Delete) {
                removeSelected();
                event.accepted = true;
            }
        }
        MouseArea {
            id: gridMouseArea
            anchors.fill: parent
            anchors.margins: 2
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: handleMouseEvent(mouse)
            Rectangle {
                color: {
                    if(root.selected)
                        return Style.window.color.selected;
                    if(gridMouseArea.containsMouse)
                        return Style.window.color.xlight;
                    return Style.window.color.dark;
                }
                width: gridMouseArea.width
                height: gridMouseArea.height
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Image {
                anchors.fill: parent
                anchors.margins: 2
                source: model.url
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                sourceSize: Qt.size(320, 320)
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
                        maximumLineCount: (gridMouseArea.containsMouse) ? 4 : 1
                    }
                }
                BusyIndicator {
                    anchors.centerIn: parent
                    running: parent.status === Image.Loading
                }
            }
        }
    }

    Menu {
        id: contextMenu
        MenuItem {
            text: root.selected ? "Unselect" : "Select"
            onTriggered: root.selected ? unselect(index) : selectExtended(index)
        }
        MenuItem {
            enabled: root.editable
            text: "Remove"
            onTriggered: removeOne(index)
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

}
