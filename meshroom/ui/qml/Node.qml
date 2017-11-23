import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtGraphicalEffects 1.0

Item {
    id: root
    property variant node: object
    property color baseColor: "#607D8B"
    property color shadowColor: "black"

    signal pressed(var mouse)
    signal attributePinCreated(var attribute, var pin)

    implicitHeight: body.height

    MouseArea {
        anchors.fill: parent
        drag.target: parent
        drag.threshold: 0
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: {
            if(mouse.button == Qt.RightButton)
                nodeMenu.popup()
            root.pressed(mouse)
        }

        Menu {
            id: nodeMenu
            MenuItem {
                text: "Compute"
                onTriggered: _reconstruction.execute(node)
            }
            MenuItem {
                text: "Open Folder"
                onTriggered: Qt.openUrlExternally(node.internalFolder)
            }
            MenuSeparator {}
            MenuItem {
                text: "Delete"
                onTriggered: _reconstruction.removeNode(node)
            }
        }
    }

// Cheaper shadow
/*
    Rectangle {
        id: shadow
        width: parent.width
        height: parent.height
        x: 0.5
        y: 0.5
        color: "black"
        opacity: 0.4
    }
*/
    Rectangle {
        id: background
        anchors.fill: parent
        color: palette.base
        layer.enabled: true
        layer.effect: DropShadow { radius: 2; color: shadowColor }
    }

    Column {
        id: body
        width: parent.width

        Label {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            padding: 4
            text: node.nodeType
            color: "#EEE"
            font.pointSize: 8
            background: Rectangle {
                color: root.baseColor
            }
        }

        // Node Chunks
        Rectangle {
            height: 3
            width: parent.width
            anchors.horizontalCenter: parent.horizontalCenter
            color: Qt.darker(baseColor, 1.3)

            ListView {
                id: chunksListView
                anchors.fill: parent

                interactive: false
                orientation: Qt.Horizontal

                model: node.chunks
                property int chunkHeight: height

                delegate: Rectangle {
                    id: chunkDelegate
                    height: chunksListView.chunkHeight
                    width: chunksListView.width / chunksListView.count
                    state: modelData.statusName
                    states: [
                        State { name: "NONE"; PropertyChanges { target: chunkDelegate; color: "transparent"} },
                        State { name: "SUBMITTED"; PropertyChanges { target: chunkDelegate; color: modelData.execModeName == "LOCAL" ? "#009688" : "#2196F3"} },
                        State { name: "RUNNING"; PropertyChanges { target: chunkDelegate; color: "#FF9800"} },
                        State { name: "ERROR"; PropertyChanges { target: chunkDelegate; color: "#F44336"} },
                        State { name: "SUCCESS"; PropertyChanges { target: chunkDelegate; color: "#4CAF50"} }
                    ]
                }
            }
        }

        Item { width: 1; height: 2}

        RowLayout  {
            width: parent.width + 6
            anchors.horizontalCenter: parent.horizontalCenter

            Column {
                id: inputs
                Layout.fillWidth: true
                Layout.fillHeight: true
                Repeater {
                    model: node.attributes
                    delegate: Loader {
                        active: !object.isOutput && object.type == "File"
                                || (object.type == "ListAttribute" && object.desc.elementDesc.type == "File") // TODO: review this

                        sourceComponent: AttributePin {
                            id: inPin
                            nodeItem: root
                            attribute: object
                            Component.onCompleted: attributePinCreated(attribute, inPin)
                            onChildPinCreated: attributePinCreated(childAttribute, inPin)
                        }
                    }
                }
            }
            Column {
                id: outputs
                Layout.fillWidth: true
                Layout.fillHeight: true
                anchors.right: parent.right
                Repeater {
                    model: node.attributes

                    delegate: Loader {
                        active: object.isOutput
                        anchors.right: parent.right

                        sourceComponent: AttributePin {
                            id: outPin
                            nodeItem: root
                            attribute: object
                            Component.onCompleted: attributePinCreated(object, outPin)
                        }
                    }
                }
            }
        }
        Item { width: 1; height: 2}
    }
}
