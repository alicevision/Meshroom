import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtGraphicalEffects 1.0

Item {
    id: root
    property variant node: object
    property bool readOnly: false
    property color baseColor: "#607D8B"
    property color shadowColor: "black"

    signal pressed(var mouse)
    signal doubleClicked(var mouse)
    signal attributePinCreated(var attribute, var pin)

    signal computeRequest()
    signal removeRequest()

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

        onDoubleClicked: root.doubleClicked(mouse)

        Menu {
            id: nodeMenu
            MenuItem {
                text: "Compute"
                enabled: !root.readOnly
                onTriggered: root.computeRequest()
            }
            MenuItem {
                text: "Open Folder"
                onTriggered: Qt.openUrlExternally(node.internalFolder)
            }
            MenuSeparator {}
            MenuItem {
                text: "Clear Data"
                enabled: !root.readOnly
                onTriggered: node.clearData()
            }
            MenuItem {
                text: "Delete Node"
                enabled: !root.readOnly
                onTriggered: root.removeRequest()
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
        NodeChunks {
            defaultColor: Qt.darker(baseColor, 1.3)
            implicitHeight: 3
            width: parent.width
            model: node.chunks
        }

        Item { width: 1; height: 2}

        Item {
            width: parent.width + 6
            height: childrenRect.height
            anchors.horizontalCenter: parent.horizontalCenter

            Column {
                id: inputs
                width: parent.width / 2
                Repeater {
                    model: node.attributes
                    delegate: Loader {
                        active: !object.isOutput && object.type == "File"
                                || (object.type == "ListAttribute" && object.desc.elementDesc.type == "File") // TODO: review this
                        width: inputs.width

                        sourceComponent: AttributePin {
                            id: inPin
                            nodeItem: root
                            attribute: object
                            readOnly: root.readOnly
                            Component.onCompleted: attributePinCreated(attribute, inPin)
                            onChildPinCreated: attributePinCreated(childAttribute, inPin)
                        }
                    }
                }
            }
            Column {
                id: outputs
                width: parent.width / 2
                anchors.right: parent.right
                Repeater {
                    model: node.attributes

                    delegate: Loader {
                        active: object.isOutput
                        anchors.right: parent.right
                        width: outputs.width

                        sourceComponent: AttributePin {
                            id: outPin
                            nodeItem: root
                            attribute: object
                            readOnly: root.readOnly
                            Component.onCompleted: attributePinCreated(object, outPin)
                        }
                    }
                }
            }
        }
        Item { width: 1; height: 2}
    }
}
