import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import Logger 1.0

Item {

    id: root
    implicitHeight: 30
    implicitWidth: parent ? parent.width : 200
    height: expanded ? 150 : 30
    Behavior on height {
        SequentialAnimation {
            NumberAnimation {}
            ScriptAction { script: listView.positionViewAtEnd() }
        }
    }

    // properties
    property bool expanded: false
    property url expandIcon: ""
    property url trashIcon: ""

    // functions
    function getLogColor(type) {
        switch(type) {
            case Log.INFO: return "#999"
            case Log.DEBUG: return "#666"
            case Log.WARNING: return "orange"
            case Log.CRITICAL:
            case Log.FATAL: return "red"
        }
    }

    // slots
    onExpandIconChanged: {
        if(typeof expandButton.icon == "undefined") return;
            expandButton.icon = root.expandIcon;
    }
    onTrashIconChanged: {
        if(typeof trashButton.icon == "undefined") return;
            trashButton.icon = root.trashIcon;
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Item {
                anchors.fill: parent
                anchors.leftMargin: 5
                visible: !root.expanded
                Label {
                    id: lastLogLabel
                    anchors.fill: parent
                    text: ""
                    state: "xsmall"
                    color: "red"
                    Behavior on opacity { NumberAnimation{} }
                }
                Timer {
                    id: lastLogTimer
                    interval: 5000; running: true
                    onTriggered: lastLogLabel.opacity = 0
                }
            }
            Item {
                anchors.fill: parent
                visible: root.expanded
                ListView {
                    id: listView
                    anchors.fill: parent
                    ScrollBar.vertical: ScrollBar {}
                    model: LogModel {
                        onCountChanged: {
                            var m = listView.model;
                            var log = m.data(m.index(m.count-1, 0), LogModel.ModelDataRole);
                            lastLogLabel.color = getLogColor(log.type)
                            lastLogLabel.text = log.message;
                            lastLogLabel.opacity = 1;
                            lastLogTimer.restart();
                        }
                    }
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
                                color: getLogColor(model.type)
                            }
                        }
                    }
                }
            }
        }
        ColumnLayout {
            Layout.fillHeight: true
            spacing: 0
            ToolButton {
                id: expandButton
                onClicked: root.expanded = !root.expanded
            }
            ToolButton {
                id: trashButton
                visible: root.expanded
                onClicked: listView.model.clear()
            }
        }
    }

}
