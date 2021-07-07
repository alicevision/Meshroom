import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtGraphicalEffects 1.0

import Utils 1.0
import MaterialIcons 2.2


/**
 * Visual representation of a Graph Node.
 */
Item {
    id: root

    /// The underlying Node object
    property variant node
    /// Whether the node can be modified
    property bool readOnly: node.locked
    /// Whether the node is in compatibility mode
    readonly property bool isCompatibilityNode: node ? node.hasOwnProperty("compatibilityIssue") : false
    /// Mouse related states
    property bool mainSelected: false
    property bool selected: false
    property bool hovered: false
    property bool dragging: mouseArea.drag.active
    /// Combined x and y
    property point position: Qt.point(x, y)
    /// Styling
    property color shadowColor: "#cc000000"
    readonly property color defaultColor: isCompatibilityNode ? "#444" : activePalette.base
    property color baseColor: defaultColor

    Item {
        id: m
        property bool displayParams: false
    }

    // Mouse interaction related signals
    signal pressed(var mouse)
    signal doubleClicked(var mouse)
    signal moved(var position)
    signal entered()
    signal exited()

    // Already connected attribute with another edge in DropArea
    signal edgeAboutToBeRemoved(var input)

    /// Emitted when child attribute pins are created
    signal attributePinCreated(var attribute, var pin)
    /// Emitted when child attribute pins are deleted
    signal attributePinDeleted(var attribute, var pin)

    // use node name as object name to simplify debugging
    objectName: node ? node.name : ""

    // initialize position with node coordinates
    x: root.node ? root.node.x : undefined
    y: root.node ? root.node.y : undefined

    implicitHeight: childrenRect.height

    SystemPalette { id: activePalette }

    Connections {
        target: root.node
        // update x,y when node position changes
        onPositionChanged: {
            root.x = root.node.x
            root.y = root.node.y
        }
    }

    // Whether an attribute can be displayed as an attribute pin on the node
    function isFileAttributeBaseType(attribute) {
        // ATM, only File attributes are meant to be connected
        // TODO: review this if we want to connect something else
        return attribute.type == "File"
               || (attribute.type == "ListAttribute" && attribute.desc.elementDesc.type == "File")
    }

    // Used to generate list of node's label sharing the same uid
    function generateDuplicateList() {
        let str = "<b>Shares internal folder (data) with:</b>"
        for(let i = 0; i < node.duplicates.count; ++i) {
            if(i % 5 === 0)
                str += "<br>"

            const currentNode = node.duplicates.at(i)

            if(i === node.duplicates.count - 1) {
                str += currentNode.nameToLabel(currentNode.name)
                return str
            }

            str += (currentNode.nameToLabel(currentNode.name) + ", ")
        }
        return str
    }

    // Main Layout
    MouseArea {
        id: mouseArea
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
            {
                root.moved(Qt.point(root.x, root.y));
            }
        }

        cursorShape: drag.active ? Qt.ClosedHandCursor : Qt.ArrowCursor

        // Selection border
        Rectangle {
            anchors.fill: nodeContent
            anchors.margins: -border.width
            visible: root.mainSelected || root.hovered
            border.width: 2.5
            border.color: root.mainSelected ? activePalette.highlight : Qt.darker(activePalette.highlight, 1.5)
            opacity: 0.9
            radius: background.radius + border.width
            color: "transparent"
        }

        Rectangle {
            id: background
            anchors.fill: nodeContent
            color: Qt.lighter(activePalette.base, 1.4)
            layer.enabled: true
            layer.effect: DropShadow { radius: 3; color: shadowColor }
            radius: 3
            opacity: 0.7
        }

        Rectangle {
            id: nodeContent
            width: parent.width
            height: childrenRect.height
            color: "transparent"

            // Data Layout
            Column {
                id: body
                width: parent.width

                // Header
                Rectangle {
                    id: header
                    width: parent.width
                    height: headerLayout.height
                    color: root.mainSelected ? activePalette.highlight : root.selected ? Qt.darker(activePalette.highlight, 1.1): root.baseColor
                    radius: background.radius

                    // Fill header's bottom radius
                    Rectangle {
                        width: parent.width
                        height: parent.radius
                        anchors.bottom: parent.bottom
                        color: parent.color
                        z: -1
                    }

                    // Header Layout
                    RowLayout {
                        id: headerLayout
                        width: parent.width
                        spacing: 0

                        // Node Name
                        Label {
                            Layout.fillWidth: true
                            text: node ? node.label : ""
                            padding: 4
                            color: root.mainSelected ? "white" : activePalette.text
                            elide: Text.ElideMiddle
                            font.pointSize: 8
                        }

                        // Node State icons
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignRight
                            Layout.rightMargin: 2
                            spacing: 2

                            // CompatibilityBadge icon for CompatibilityNodes
                            Loader {
                                active: root.isCompatibilityNode
                                sourceComponent: CompatibilityBadge {
                                    sourceComponent: iconDelegate
                                    canUpgrade: root.node.canUpgrade
                                    issueDetails: root.node.issueDetails
                                }
                            }

                            // Data sharing indicator
                            // Note: for an unknown reason, there are some performance issues with the UI refresh.
                            // Example: a node duplicated 40 times will be slow while creating another identical node
                            // (sharing the same uid) will not be as slow. If save, quit and reload, it will become slow.
                            MaterialToolButton {
                                property string baseText: "<b>Shares internal folder (data) with other node(s). Hold click for details.</b>"
                                property string toolTipText: visible ? baseText : ""
                                visible: node.hasDuplicates
                                text: MaterialIcons.layers
                                font.pointSize: 7
                                padding: 2
                                palette.text: Colors.sysPalette.text
                                ToolTip.text: toolTipText

                                onPressed: { offsetReleased.running = false; toolTipText = visible ? generateDuplicateList() : "" }
                                onReleased: { toolTipText = "" ; offsetReleased.running = true }
                                onCanceled: released()

                                // Used for a better user experience with the button
                                // Avoid to change the text too quickly
                                Timer {
                                    id: offsetReleased
                                    interval: 750; running: false; repeat: false
                                    onTriggered: parent.toolTipText = visible ? parent.baseText : ""
                                }
                            }

                            // Submitted externally indicator
                            MaterialLabel {
                                visible: ["SUBMITTED", "RUNNING"].includes(node.globalStatus) && node.chunks.count > 0 && node.globalExecMode === "EXTERN"
                                text: MaterialIcons.cloud
                                padding: 2
                                font.pointSize: 7
                                palette.text: Colors.sysPalette.text
                                ToolTip.text: "Computed Externally"
                            }

                            // Lock indicator
                            MaterialLabel {
                                visible: root.readOnly
                                text: MaterialIcons.lock
                                padding: 2
                                font.pointSize: 7
                                palette.text: "red"
                                ToolTip.text: "Locked"
                            }
                        }
                    }
                }

                // Node Chunks
               NodeChunks {
                   defaultColor: Colors.sysPalette.mid
                   implicitHeight: 3
                   width: parent.width
                   model: node ? node.chunks : undefined

                   Rectangle {
                       anchors.fill: parent
                       color: Colors.sysPalette.mid
                       z: -1
                   }
               }

                // Vertical Spacer
                Item { width: parent.width; height: 2 }

                // Input/Output Attributes
                Item {
                    id: nodeAttributes
                    width: parent.width - 2
                    height: childrenRect.height
                    anchors.horizontalCenter: parent.horizontalCenter

                    Column {
                        id: attributesColumn
                        width: parent.width
                        spacing: 5
                        bottomPadding: 2

                        Column {
                            id: outputs
                            width: parent.width
                            spacing: 3
                            Repeater {
                                model: node ? node.attributes : undefined

                                delegate: Loader {
                                    id: outputLoader
                                    active: object.isOutput && isFileAttributeBaseType(object)
                                    anchors.right: parent.right
                                    width: outputs.width

                                    sourceComponent: AttributePin {
                                        id: outPin
                                        nodeItem: root
                                        attribute: object

                                        property real globalX: root.x + nodeAttributes.x + outputs.x + outputLoader.x + outPin.x
                                        property real globalY: root.y + nodeAttributes.y + outputs.y + outputLoader.y + outPin.y

                                        onPressed: root.pressed(mouse)
                                        onEdgeAboutToBeRemoved: root.edgeAboutToBeRemoved(input)

                                        Component.onCompleted: attributePinCreated(object, outPin)
                                        Component.onDestruction: attributePinDeleted(attribute, outPin)
                                    }
                                }
                            }
                        }

                        Column {
                            id: inputs
                            width: parent.width
                            spacing: 3

                            Repeater {
                                model: node ? node.attributes : undefined
                                delegate: Loader {
                                    id: inputLoader
                                    active: !object.isOutput && isFileAttributeBaseType(object)
                                    width: inputs.width

                                    sourceComponent: AttributePin {
                                        id: inPin
                                        nodeItem: root
                                        attribute: object

                                        property real globalX: root.x + nodeAttributes.x + inputs.x + inputLoader.x + inPin.x
                                        property real globalY: root.y + nodeAttributes.y + inputs.y + inputLoader.y + inPin.y

                                        readOnly: root.readOnly || object.isReadOnly
                                        Component.onCompleted: attributePinCreated(attribute, inPin)
                                        Component.onDestruction: attributePinDeleted(attribute, inPin)
                                        onPressed: root.pressed(mouse)
                                        onEdgeAboutToBeRemoved: root.edgeAboutToBeRemoved(input)
                                        onChildPinCreated: attributePinCreated(childAttribute, inPin)
                                        onChildPinDeleted: attributePinDeleted(childAttribute, inPin)
                                    }
                                }
                            }
                        }

                        // Vertical Spacer
                        Rectangle {
                            height: inputParams.height > 0 ? 3 : 0
                            visible: (height == 3)
                            Behavior on height { PropertyAnimation {easing.type: Easing.Linear} }
                            width: parent.width
                            color: Colors.sysPalette.mid
                            MaterialToolButton {
                                text: " "
                                width: parent.width
                                height: parent.height
                                padding: 0
                                spacing: 0
                                anchors.margins: 0
                                font.pointSize: 6
                                onClicked: {
                                    m.displayParams = ! m.displayParams
                                }
                            }
                        }

                        Rectangle {
                            id: inputParamsRect
                            width: parent.width
                            height: childrenRect.height
                            color: "transparent"

                            Column {
                                id: inputParams
                                width: parent.width
                                spacing: 3
                                Repeater {
                                    id: inputParamsRepeater
                                    model: node ? node.attributes : undefined
                                    delegate: Loader {
                                        id: paramLoader
                                        active: !object.isOutput && !isFileAttributeBaseType(object)
                                        property bool isFullyActive: (m.displayParams || object.isLink || object.hasOutputConnections)
                                        width: parent.width

                                        sourceComponent: AttributePin {
                                            id: inPin
                                            nodeItem: root
                                            property real globalX: root.x + nodeAttributes.x + inputParamsRect.x + paramLoader.x + inPin.x
                                            property real globalY: root.y + nodeAttributes.y + inputParamsRect.y + paramLoader.y + inPin.y

                                            height: isFullyActive ? childrenRect.height : 0
                                            Behavior on height { PropertyAnimation {easing.type: Easing.Linear} }
                                            visible: (height == childrenRect.height)
                                            attribute: object
                                            readOnly: root.readOnly || object.isReadOnly
                                            Component.onCompleted: attributePinCreated(attribute, inPin)
                                            Component.onDestruction: attributePinDeleted(attribute, inPin)
                                            onPressed: root.pressed(mouse)
                                            onEdgeAboutToBeRemoved: root.edgeAboutToBeRemoved(input)
                                            onChildPinCreated: attributePinCreated(childAttribute, inPin)
                                            onChildPinDeleted: attributePinDeleted(childAttribute, inPin)
                                        }
                                    }
                                }
                            }
                        }

                        MaterialToolButton {
                            text: root.hovered ? (m.displayParams ? MaterialIcons.arrow_drop_up : MaterialIcons.arrow_drop_down) : " "
                            Layout.alignment: Qt.AlignBottom
                            width: parent.width
                            height: 5
                            padding: 0
                            spacing: 0
                            anchors.margins: 0
                            font.pointSize: 10
                            onClicked: {
                                m.displayParams = ! m.displayParams
                            }
                        }
                    }
                }
            }
        }
    }
}

