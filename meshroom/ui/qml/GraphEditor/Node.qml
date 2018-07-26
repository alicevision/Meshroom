import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtGraphicalEffects 1.0
import Utils 1.0

Item {
    id: root
    property variant node
    property bool readOnly: false
    property color baseColor: defaultColor
    property color shadowColor: "black"
    readonly property bool isCompatibilityNode: node.hasOwnProperty("compatibilityIssue")
    readonly property color defaultColor: isCompatibilityNode ? "#444" : "#607D8B"

    signal pressed(var mouse)
    signal doubleClicked(var mouse)
    signal attributePinCreated(var attribute, var pin)
    signal attributePinDeleted(var attribute, var pin)

    implicitHeight: body.height
    objectName: node.name

    SystemPalette { id: activePalette }

    MouseArea {
        anchors.fill: parent
        drag.target: parent
        drag.threshold: 0
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: root.pressed(mouse)
        onDoubleClicked: root.doubleClicked(mouse)
    }

    Rectangle {
        id: background
        anchors.fill: parent
        color: activePalette.base
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
                            Component.onDestruction: attributePinDeleted(attribute, inPin)
                            onChildPinCreated: attributePinCreated(childAttribute, inPin)
                            onChildPinDeleted: attributePinDeleted(childAttribute, inPin)
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

    // CompatibilityBadge icon for CompatibilityNodes
    Loader {
        active: root.isCompatibilityNode
        anchors {
            right: parent.right
            top: parent.top
            margins: -4
        }
        sourceComponent: CompatibilityBadge {
            sourceComponent: iconDelegate
            canUpgrade: root.node.canUpgrade
            issueDetails: root.node.issueDetails
        }
    }
}
