import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0

Item {
    id: root
    property variant scene

    clip: true

    ColumnLayout {
        Layout.fillWidth: false
        anchors.fill: parent
        ListView {
            id: graphsListView
            model: scene.graphs
            Layout.fillHeight: true
            Layout.fillWidth: true
            currentIndex: scene.graphs.indexOf(scene.graph)
            delegate: Rectangle {
                id: delegate
                width: parent.width
                height: childrenRect.height
                color: control.highlighted ? "#25252A" : control.hovered ? "#222225" :"transparent"
                RowLayout {
                    width: parent.width
                    height: control.height
                    ItemDelegate {
                        id: control
                        text: qtObject.name
                        Layout.fillWidth: true
                        highlighted: delegate.ListView.isCurrentItem
                        onClicked: scene.graph = qtObject
                        background: Item {}
                        contentItem: RowLayout {
                            Text {
                                text: index + 1 + ". "
                                font: control.font
                                color: "#CCC"
                            }
                            Text {
                                Layout.fillWidth: true
                                text: control.text
                                font: control.font
                                color: "#CCC"
                                elide: Text.ElideRight
                            }
                        }
                    }
                    Button {
                        text: "⚙"
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
