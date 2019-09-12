import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtGraphicalEffects 1.0
import Utils 1.0
import MaterialIcons 2.2

Item {
    id: root
    property variant node
    property bool readOnly: false
    property color baseColor: defaultColor
    property color shadowColor: "#cc000000"
    readonly property bool isCompatibilityNode: node.hasOwnProperty("compatibilityIssue")
    readonly property color defaultColor: isCompatibilityNode ? "#444" : "#34495e" // "#607D8B"
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
    Column {
        width: parent.width

        MouseArea {
            width: parent.width
            height: body.height
            drag.target: root
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
                radius: background.radius
                color: "transparent"
            }

            Rectangle {
                id: background
                anchors.fill: parent

                color: activePalette.base
                layer.enabled: true
                layer.effect: DropShadow { radius: 3; color: shadowColor }
                radius: 3
            }

            Column {
                id: body
                width: parent.width

                Rectangle {
                    id: stateView
                    width: parent.width
                    height: 20
                    color: root.baseColor
                    radius: background.radius

                    Rectangle {
                        width: parent.width
                        height: parent.radius
                        y: -parent.radius
                        anchors.bottom: parent.bottom
                        color: parent.color
                    }

                    RowLayout {
                        width: parent.width
                        spacing: 0

                        Label {
                            width: parent.width
                            padding: 4
                            text: node.label
                            color: "#fff" //Colors.sysPalette.text
                            font.pointSize: 7
                        }

                        RowLayout {
                            anchors.right: parent.right
                            width: 50
                            spacing: 0

                            MaterialLabel {
                                id: ghostIcon
                                visible: node.chunks.count > 0 && node.globalStatus !== "NONE" && node.chunks.at(0).statusNodeName !== node.name
                                padding: 2
                                text: MaterialIcons.layers //MaterialIcons.all_inclusive
                                font.pointSize: 8
                                color: Colors.sysPalette.text

                                MouseArea {
                                    height: parent.height
                                    width: parent.width
                                    hoverEnabled: true

                                    property bool showTooltip: false


                                    onEntered: {
                                        ghostIcon.color = Colors.cyan
                                        showTooltip = true
                                    }

                                    onExited: {
                                        ghostIcon.color = Colors.sysPalette.text
                                        showTooltip = false
                                    }

                                    ToolTip {
                                        delay: 800
                                        visible: parent.showTooltip
                                        text: ""
                                        onVisibleChanged: {
                                            text = "The data associated to this node has been computed by the other node: <b>" + node.nameToLabel(node.chunks.at(0).statusNodeName) + "</b>."
                                        }
                                    }
                                }
                            }

                            MaterialLabel {
                                id: cloudIcon
                                visible: ["SUBMITTED", "RUNNING"].includes(node.globalStatus) && node.chunks.count > 0 && node.chunks.at(0).execModeName === "EXTERN"
                                padding: 2
                                text: MaterialIcons.cloud
                                font.pointSize: 8

                                MouseArea {
                                    height: parent.height
                                    width: parent.width
                                    hoverEnabled: true

                                    property bool showTooltip: false


                                    onEntered: {
                                        cloudIcon.color = Colors.cyan
                                        showTooltip = true
                                    }

                                    onExited: {
                                        cloudIcon.color = Colors.sysPalette.text
                                        showTooltip = false
                                    }

                                    ToolTip {
                                        delay: 800
                                        visible: parent.showTooltip
                                        text: "This nodes is being computed externally"
                                    }

                                }
                            }

                            MaterialLabel {
                                id: lockIcon
                                visible: root.readOnly
                                padding: 2
                                text: MaterialIcons.lock
                                font.pointSize: 8

                                MouseArea {
                                    height: parent.height
                                    width: parent.width
                                    hoverEnabled: true

                                    property bool showTooltip: false


                                    onEntered: {
                                        lockIcon.color = Colors.red
                                        showTooltip = true
                                    }

                                    onExited: {
                                        lockIcon.color = Colors.sysPalette.text
                                        showTooltip = false
                                    }

                                    ToolTip {
                                        delay: 800
                                        visible: parent.showTooltip
                                        text: "<b>Locked</b><br/>This node cannot be edited at the moment"
                                    }

                                }
                            }
                        }
                    }



                }

                // Node Chunks
                NodeChunks {
                    defaultColor: Colors.sysPalette.mid
                    implicitHeight: 3
                    width: parent.width
                    model: node.chunks

                    Rectangle {
                        anchors.fill: parent
                        color: Colors.sysPalette.mid
                        z: -1
                    }
                }

                Item { width: 1; height: 2}

                Item {
                    id: nodeAttributes
                    width: parent.width + 6
                    height: childrenRect.height
                    anchors.horizontalCenter: parent.horizontalCenter

                    MouseArea {
                        id: disabledRect
                        visible: root.readOnly
                        width: parent.width - 6
                        height: parent.height
                        anchors.leftMargin: -6

                        Rectangle {
                            anchors.fill: parent
                            color: Colors.sysPalette.window
                            opacity: 0.5
                        }

                        z:10
                    }

                    Rectangle {
                        id: innerRect
                        width: parent.width - 6
                        height: parent.height
                        color: Colors.sysPalette.window
                        anchors.horizontalCenter: parent.horizontalCenter
                    }

                    Column {
                        width: parent.width
                        spacing: 1
                        bottomPadding: 2

                        Column {
                            id: outputs
                            width: parent.width
                            spacing: 1
                            Repeater {
                                model: node.attributes

                                delegate: Loader {
                                    id: outputLoader
                                    active: object.isOutput
                                    anchors.right: parent.right
                                    width: outputs.width

                                    Rectangle {
                                        width: innerRect.width
                                        height: parent.height
                                        color: Colors.sysPalette.base
                                        anchors.horizontalCenter: parent.horizontalCenter
                                    }

                                    sourceComponent: AttributePin {
                                        id: outPin
                                        nodeItem: root
                                        attribute: object

//                                        parentVisualised: root.visualize

                                        readOnly: root.readOnly
                                        onPressed: root.pressed(mouse)
                                        Component.onCompleted: attributePinCreated(object, outPin)
                                        Component.onDestruction: attributePinDeleted(attribute, outPin)
                                    }
                                }
                            }
                        }

                        Column {
                            id: inputs
                            width: parent.width
                            spacing: 1
                            Repeater {
                                model: node.attributes
                                delegate: Loader {
                                    active: !object.isOutput && object.type == "File"
                                            || (object.type == "ListAttribute" && object.desc.elementDesc.type == "File") // TODO: review this
                                    width: inputs.width

                                    Rectangle {
                                        width: innerRect.width
                                        height: parent.height
                                        color: Colors.sysPalette.base
                                        anchors.horizontalCenter: parent.horizontalCenter
                                    }

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
                    }
                }

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

    state: collapseGroup.checkedButton.type
    onStateChanged: console.info(state)

    states: [
        State {
            name: "showAll"
            PropertyChanges {
                target: outputLoader
                active: object.isOutput
            }
        },

        State {
            name: "showConnected"
        },
        State {
            name: "hideAll"
            PropertyChanges {
                target: outputLoader
                active: false
            }
            PropertyChanges {
                target: nodeAttributes
                height: childrenRect.height
            }
            PropertyChanges {
                target: outputs
                visible: false
            }
            PropertyChanges {
                target: inputs
                visible: false
            }
        }
    ]
}
