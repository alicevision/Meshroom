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
    property bool selected: false
    property bool hovered: false

    signal pressed(var mouse)
    signal doubleClicked(var mouse)
    signal moved(var position)
    signal entered()
    signal exited()
    signal attributePinCreated(var attribute, var pin)
    signal attributePinDeleted(var attribute, var pin)

    implicitHeight: childrenRect.height
    objectName: node.name

    SystemPalette { id: activePalette }

    // initialize position with node coordinates
    x: root.node.x
    y: root.node.y

    Connections {
        target: root.node
        // update x,y when node position changes
        onPositionChanged: {
            root.x = root.node.x
            root.y = root.node.y
        }
    }

    // Whether an attribute can be displayed as an attribute pin on the node
    function isDisplayableAsPin(attribute) {
        // ATM, only File attributes are meant to be connected
        // TODO: review this if we want to connect something else
        return attribute.type == "File"
               || (attribute.type == "ListAttribute" && attribute.desc.elementDesc.type == "File")
    }

    MouseArea {
        width: parent.width
        height: body.height
        drag.target: parent
        // small drag threshold to avoid moving the node by mistake
        drag.threshold: 2
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: root.pressed(mouse)
        onDoubleClicked: root.doubleClicked(mouse)
        onEntered: root.entered()
        onExited: root.exited()
        drag.onActiveChanged: {
            if(!drag.active)
                root.moved(Qt.point(root.x, root.y))
        }

        // Selection border
        Rectangle {
            anchors.fill: parent
            anchors.margins: -border.width
            visible: root.selected || root.hovered
            border.width: 2.5
            border.color: root.selected ? activePalette.highlight : Qt.darker(activePalette.highlight, 1.5)
            opacity: 0.9
            color: "transparent"
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
                text: node.label
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
                    spacing: 1
                    Repeater {
                        model: node.attributes
                        delegate: Loader {
                            active: !object.isOutput && isDisplayableAsPin(object)
                            width: inputs.width

                            sourceComponent: AttributePin {
                                id: inPin
                                nodeItem: root
                                attribute: object
                                readOnly: root.readOnly
                                Component.onCompleted: attributePinCreated(attribute, inPin)
                                Component.onDestruction: attributePinDeleted(attribute, inPin)
                                onPressed: root.pressed(mouse)
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
                    spacing: 1
                    Repeater {
                        model: node.attributes

                        delegate: Loader {
                            active: object.isOutput && isDisplayableAsPin(object)
                            anchors.right: parent.right
                            width: outputs.width

                            sourceComponent: AttributePin {
                                id: outPin
                                nodeItem: root
                                attribute: object
                                readOnly: root.readOnly
                                onPressed: root.pressed(mouse)
                                Component.onCompleted: attributePinCreated(object, outPin)
                                Component.onDestruction: attributePinDeleted(attribute, outPin)
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
}
