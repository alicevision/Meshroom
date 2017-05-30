import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import FontAwesome 1.0

Item {
    id: root
    property variant scene

    clip: true

    ColumnLayout {
        Layout.fillWidth: false
        anchors.fill: parent
        spacing: 1

        ListView {
            id: graphsListView
            model: scene.graphs
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.margins: 1
            currentIndex: scene.graphs.indexOf(scene.graph)
            delegate: Rectangle {
                id: delegate
                width: parent.width
                height: childrenRect.height
                color: control.highlighted ? "#25252A" : control.hovered ? "#222225" :"transparent"
                RowLayout {
                    width: parent.width - 4
                    height: control.height
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 2
                    ItemDelegate {
                        id: control
                        text: qtObject.name
                        Layout.fillWidth: true
                        highlighted: delegate.ListView.isCurrentItem
                        onClicked: scene.graph = qtObject
                        background: Item {}
                        contentItem: Text {
                            Layout.fillWidth: true
                            text: control.text
                            font: control.font
                            color: "#CCC"
                            elide: Text.ElideRight
                        }
                    }
                    // Kill WorkerThread button
                    ToolButton {
                        id: button
                        text: hovered ? FontAwesome.stop : ""
                        font.family: FontAwesome.fontFamily
                        visible: qtObject.isRunning
                        onClicked: qtObject.stopWorkerThread()

                        Label {
                            id: runningIcon
                            anchors.centerIn: parent
                            text: FontAwesome.circleONotch
                            font.family: FontAwesome.fontFamily
                            visible: !parent.hovered
                            PropertyAnimation {
                                target: runningIcon
                                running: true
                                property: "rotation"
                                from: 0
                                to: 360
                                duration: 800
                                loops: Animation.Infinite
                            }
                        }
                    }

                    ToolButton {
                        text: FontAwesome.cog
                        font.family: FontAwesome.fontFamily
                        onClicked: menu.open()
                        Menu {
                            id: menu
                            MenuItem {
                                text: "Duplicate"
                                onTriggered: scene.duplicateGraph(qtObject, true);
                            }
                            MenuItem {
                                text: "Delete"
                                enabled: scene.graphs.count > 1
                                onTriggered: scene.deleteGraph(qtObject);
                            }
                        }
                    }
                }
            }
        }
        Button {
            Layout.alignment: Qt.AlignRight
            text: "+"
            onClicked: scene.addGraph(true)
        }
    }
}
