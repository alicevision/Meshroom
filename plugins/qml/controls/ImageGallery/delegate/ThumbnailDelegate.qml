import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

Package {

    id: root

    // properties
    property bool selected: false
    property int sourceSize: 400

    // signals
    signal selectContiguous(int id)
    signal selectExtended(int id)
    signal selectOne(int id)
    signal unselect(int id)
    signal unselectAll()
    signal removeSelected()
    signal removeOne(int id)

    // connections / slots
    Component.onCompleted: selected = _selector.isSelected(index)
    Connections {
        target: _selector
        onRefreshSelectionFlags: root.selected = _selector.isSelected(index)
    }

    // functions
    function handleKeyEvent(event) {
        if (event.key == Qt.Key_Backspace || event.key == Qt.Key_Delete) {
            removeSelected();
            event.accepted = true;
        }
    }
    function handleMouseEvent(mouse, callerDelegate) {
        if(mouse.button == Qt.LeftButton) {
            if(mouse.modifiers & Qt.ShiftModifier) {
                selectContiguous(index);
                return;
            }
            if(mouse.modifiers & Qt.ControlModifier) {
                root.selected ? unselect(index) : selectExtended(index);
                return;
            }
            selectOne(index);
            return;
        }
        selectOne(index);
        contextMenu.parent = callerDelegate;
        contextMenu.x = mouse.x;
        contextMenu.y = mouse.y;
        contextMenu.open();
    }

    // list style delegate
    Item {
        id: listDelegate
        Package.name: 'list'
        width: ListView.view ? ListView.view.width : 0
        height: ListView.view ? ListView.view.cellHeight : 0
        clip: true
        Keys.onPressed: handleKeyEvent(event)
        MouseArea {
            id: listMouseArea
            anchors.fill: parent
            anchors.margins: 2
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: {
                listDelegate.forceActiveFocus();
                handleMouseEvent(mouse, listDelegate);
            }
        }
        Rectangle {
            anchors.fill: parent
            color: {
                if(root.selected)
                    return "#5BB1F7";
                if(listMouseArea.containsMouse)
                    return Qt.rgba(1, 1, 1, 0.3);
                return Qt.rgba(0, 0, 0, 0.1);
            }
        }
        RowLayout {
            anchors.fill: parent
            spacing: 10
            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: Math.min(parent.height*4/3.0, parent.width*0.4)
                color: "black"
                Image {
                    anchors.fill: parent
                    source: modelData
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    sourceSize: Qt.size(root.size, root.size)
                    BusyIndicator {
                        anchors.centerIn: parent
                        running: parent.status === Image.Loading
                    }
                }
            }
            Label {
                Layout.fillWidth: true
                text: modelData.replace("file://", "")
                state: "xsmall"
            }
            Item {
                Layout.fillWidth: true
            }
        }
    }

    // grid style delegate
    Item {
        id: gridDelegate
        Package.name: 'grid'
        width: GridView.view ? GridView.view.cellWidth : 0
        height: GridView.view ? GridView.view.cellHeight : 0
        clip: true
        Keys.onPressed: handleKeyEvent(event)
        MouseArea {
            id: gridMouseArea
            anchors.fill: parent
            anchors.margins: 2
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: {
                gridDelegate.forceActiveFocus();
                handleMouseEvent(mouse, gridDelegate);
            }
            Rectangle {
                color: {
                    if(root.selected)
                        return "#5BB1F7";
                    if(gridMouseArea.containsMouse)
                        return Qt.rgba(1, 1, 1, 0.3);
                    return Qt.rgba(0, 0, 0, 0.1);
                }
                width: gridMouseArea.width
                height: gridMouseArea.height
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Image {
                anchors.fill: parent
                anchors.margins: 2
                source: modelData
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                sourceSize: Qt.size(root.size, root.size)
                Rectangle {
                    width: parent.width
                    height: childrenRect.height
                    Behavior on height { NumberAnimation {} }
                    color: "#66111111"
                    Label {
                        width: parent.width
                        text: modelData.replace("file://", "")
                        state: "xsmall"
                        maximumLineCount: (gridMouseArea.containsMouse) ? 4 : 1
                        elide: Text.ElideMiddle
                    }
                }
                BusyIndicator {
                    anchors.centerIn: parent
                    running: parent.status === Image.Loading
                }
            }
        }
    }

    // context menu
    Menu {
        id: contextMenu
        MenuItem {
            text: "Remove"
            onTriggered: removeOne(index)
        }
        MenuItem {
            text: "Open parent directory"
            onTriggered: Qt.openUrlExternally(modelData.substring(0, modelData.lastIndexOf('/')))
        }
    }

}
