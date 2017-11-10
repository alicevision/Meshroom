import QtQuick 2.9
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3

Rectangle {
    id: root
    property variant node: object
    property color baseColor: "#607D8B"

    signal pressed(var mouse)
    signal attributePinCreated(var attribute, var pin)

    implicitHeight: body.height + 4

    opacity: 0.9

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

    Column {
        id: body
        width: parent.width

        Label {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            padding: 2
            text: node.nodeType
            color: "#EEE"
            font.pointSize: 8
        }

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
    }

    StateGroup {
        id: status

        state: node.statusName

        states: [
            State {
                name: "NONE"
                PropertyChanges { target: root; color: baseColor}
            },
            State {
                name: "SUBMITTED_EXTERN"
                PropertyChanges { target: root; color: "#2196F3"}
            },
            State {
                name: "SUBMITTED_LOCAL"
                PropertyChanges { target: root; color: "#009688"}
            },
            State {
                name: "RUNNING"
                PropertyChanges { target: root; color: "#FF9800"}
            },
            State {
                name: "ERROR"
                PropertyChanges { target: root; color: "#F44336"}
            },
            State {
                name: "SUCCESS"
                PropertyChanges { target: root; color: "#4CAF50"}
            }
        ]
    }
}
