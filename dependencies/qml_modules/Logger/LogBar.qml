import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import Logger 1.0

Item {

    id: root
    implicitHeight: 30
    implicitWidth: parent ? parent.width : 200
    height: expanded ? 150 : 30
    // Behavior on height {
    //     SequentialAnimation {
    //         NumberAnimation {}
    //         ScriptAction { script: listView.positionViewAtEnd() }
    //     }
    // }

    // properties
    property bool expanded: false

    RowLayout {
        anchors.fill: parent
        spacing: 0
        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.fillHeight: true
            ScrollBar.vertical: ScrollBar {}
            clip: true
            model: LogModel {}
            snapMode: ListView.SnapToItem
            delegate: Item {
                width: ListView.view.width
                height: 30
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 5
                    Label {
                        text: "#"+index
                        state: "xsmall"
                    }
                    Label {
                        Layout.fillWidth: true
                        text: model.message
                        state: "xsmall"
                    }
                }
            }
            onCountChanged: {
                positionViewAtEnd();
                currentIndex = count - 1;
            }
        }
        ColumnLayout {
            ToolButton {
                // iconSource: "qrc:///images/expand.svg"
                onClicked: root.expanded = !root.expanded
            }
            ToolButton {
                // iconSource: "qrc:///images/trash.svg"
                onClicked: listView.model.clear()
                visible: root.expanded
            }
        }
    }
}
