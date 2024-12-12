import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Utils 1.0
import MaterialIcons 2.2

/**
 * The representation of an Attribute on a Node.
 */

RowLayout {
    id: root

    property var nodeItem
    property var attribute
    property bool expanded: false
    property bool readOnly: false
    /// Whether to display an output pin for input attribute
    property bool displayOutputPinForInput: true

    // position of the anchor for attaching and edge to this attribute pin
    readonly property point inputAnchorPos: Qt.point(inputAnchor.x + inputAnchor.width / 2,
                                                     inputAnchor.y + inputAnchor.height / 2)

    readonly property point outputAnchorPos: Qt.point(outputAnchor.x + outputAnchor.width / 2,
                                                      outputAnchor.y + outputAnchor.height / 2)

    readonly property bool isList: attribute && attribute.type === "ListAttribute"
    readonly property bool isGroup: attribute && attribute.type === "GroupAttribute"
    readonly property bool isChild: attribute && attribute.root
    readonly property bool isConnected: attribute.isLinkNested || attribute.hasOutputConnections

    signal childPinCreated(var childAttribute, var pin)
    signal childPinDeleted(var childAttribute, var pin)

    signal pressed(var mouse)
    signal edgeAboutToBeRemoved(var input)
    signal clicked()

    objectName: attribute ? attribute.name + "." : ""
    layoutDirection: Qt.LeftToRight
    spacing: 3

    ToolTip {
        text: attribute.fullName + ": " + attribute.type
        visible: nameLabel.hovered

        y: nameLabel.y + nameLabel.height
        x: nameLabel.x
    }

    function updatePin(isSrc, isVisible) {
        if (isSrc) {
            innerOutputAnchor.linkEnabled = isVisible
        } else {
            innerInputAnchor.linkEnabled = isVisible
        }
    }

    function updateLabel() {
        var label = ""
        var expandedGroup = expanded ? "-" : "+"
        if (attribute && attribute.label !== undefined) {
            label = attribute.label
            if (isGroup && attribute.isOutput) {
                label = label + " " + expandedGroup
            } else if (isGroup && !attribute.isOutput) {
                label = expandedGroup + " " + label
            }
        }
        return label
    }

    // Instantiate empty Items for each child attribute
    Repeater {
        id: childrenRepeater
        model: isList && !attribute.isLink ? attribute.value : 0
        onItemAdded: function(index, item) { childPinCreated(item.childAttribute, root) }
        onItemRemoved: function(index, item) { childPinDeleted(item.childAttribute, root) }
        delegate: Item {
            property var childAttribute: object
            visible: false
        }
    }

    Rectangle {
        visible: !attribute.isOutput
        id: inputAnchor

        width: 8
        height: width
        radius: isList ? 0 : width / 2
        Layout.alignment: Qt.AlignVCenter

        border.color: Colors.sysPalette.mid
        color: Colors.sysPalette.base

        Rectangle {
            id: innerInputAnchor
            property bool linkEnabled: true
            visible: inputConnectMA.containsMouse || childrenRepeater.count > 0 || (attribute && attribute.isLink && linkEnabled) || inputConnectMA.drag.active || inputDropArea.containsDrag
            radius: isList ? 0 : 2
            anchors.fill: parent
            anchors.margins: 2
            color: {
                if (inputConnectMA.containsMouse || inputConnectMA.drag.active || (inputDropArea.containsDrag && inputDropArea.acceptableDrop))
                    return Colors.sysPalette.highlight
                return Colors.sysPalette.text
            }
        }

        DropArea {
            id: inputDropArea

            property bool acceptableDrop: false

            // Add negative margins for DropArea to make the connection zone easier to reach
            anchors.fill: parent
            anchors.margins: -2
            // Add horizontal negative margins according to the current layout
            anchors.rightMargin: -root.width * 0.3

            keys: [inputDragTarget.objectName]
            onEntered: function(drag) {
                // Check if attributes are compatible to create a valid connection
                if (root.readOnly                                            // Cannot connect on a read-only attribute
                    || drag.source.objectName != inputDragTarget.objectName  // Not an edge connector
                    || drag.source.baseType !== inputDragTarget.baseType     // Not the same base type
                    || drag.source.nodeItem === inputDragTarget.nodeItem     // Connection between attributes of the same node
                    || (drag.source.isList && childrenRepeater.count)        // Source/target are lists but target already has children
                    || drag.source.connectorType === "input"                 // Refuse to connect an "input pin" on another one (input attr can be connected to input attr, but not the graphical pin)
                   ) {
                    // Refuse attributes connection
                    drag.accepted = false
                } else if (inputDragTarget.attribute.isLink) {  // Already connected attribute
                    root.edgeAboutToBeRemoved(inputDragTarget.attribute)
                }
                inputDropArea.acceptableDrop = drag.accepted
            }

            onExited: {
                if (inputDragTarget.attribute.isLink) {  // Already connected attribute
                    root.edgeAboutToBeRemoved(undefined)
                }
                acceptableDrop = false
                drag.source.dropAccepted = false
            }

            onDropped: function(drop) {
                root.edgeAboutToBeRemoved(undefined)
                _reconstruction.addEdge(drag.source.attribute, inputDragTarget.attribute)
            }
        }

        Item {
            id: inputDragTarget
            objectName: "edgeConnector"
            readonly property string connectorType: "input"
            readonly property alias attribute: root.attribute
            readonly property alias nodeItem: root.nodeItem
            readonly property bool isOutput: Boolean(attribute.isOutput)
            readonly property string baseType: attribute.baseType !== undefined ? attribute.baseType : ""
            readonly property alias isList: root.isList
            property bool dragAccepted: false
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            height: parent.height
            Drag.keys: [inputDragTarget.objectName]
            Drag.active: inputConnectMA.drag.active
            Drag.hotSpot.x: width * 0.5
            Drag.hotSpot.y: height * 0.5
        }

        MouseArea {
            id: inputConnectMA
            drag.target: attribute.isReadOnly ? undefined : inputDragTarget
            drag.threshold: 0
            // Move the edge's tip straight to the the current mouse position instead of waiting after the drag operation has started
            drag.smoothed: false
            enabled: !root.readOnly
            anchors.fill: parent
            // Use the same negative margins as DropArea to ease pin selection
            anchors.margins: inputDropArea.anchors.margins
            anchors.leftMargin: inputDropArea.anchors.leftMargin
            anchors.rightMargin: inputDropArea.anchors.rightMargin
            onPressed: function(mouse) {
                root.pressed(mouse)
            }
            onReleased: {
                inputDragTarget.Drag.drop()
            }
            onClicked: root.clicked()
            hoverEnabled: root.visible
        }

        Edge {
            id: inputConnectEdge
            visible: false
            point1x: inputDragTarget.x + inputDragTarget.width / 2
            point1y: inputDragTarget.y + inputDragTarget.height / 2
            point2x: parent.width / 2
            point2y: parent.width / 2
            color: palette.highlight
            thickness: outputDragTarget.dropAccepted ? 2 : 1
        }
    }

    // Attribute name
    Item {
        id: nameContainer
        implicitHeight: childrenRect.height
        Layout.fillWidth: true
        Layout.alignment: {
            if (attribute.isOutput) {
                return Qt.AlignRight | Qt.AlignVCenter
            }
            return Qt.AlignLeft | Qt.AlignVCenter
        }

        MaterialToolLabel {
            id: nameLabel

            anchors.rightMargin: 0
            anchors.right: attribute && attribute.isOutput ? parent.right : undefined
            labelIconRow.layoutDirection: attribute.isOutput ? Qt.RightToLeft : Qt.LeftToRight
            labelIconRow.spacing: 0

            enabled: !root.readOnly
            visible: true
            property bool hovered: (inputConnectMA.containsMouse || inputConnectMA.drag.active ||
                                    inputDropArea.containsDrag || outputConnectMA.containsMouse ||
                                    outputConnectMA.drag.active || outputDropArea.containsDrag)

            labelIconColor: {
                if ((object.hasOutputConnections || object.isLink) && !object.enabled) {
                    return Colors.lightgrey
                } else if (hovered) {
                    return palette.highlight
                }
                return palette.text
            }
            labelIconMouseArea.enabled: false  // Prevent mixing mouse interactions between the label and the pin context

            // Text
            label.text: attribute.label
            label.font.pointSize: 7
            label.elide: hovered ? Text.ElideNone : Text.ElideMiddle
            label.horizontalAlignment: attribute && attribute.isOutput ? Text.AlignRight : Text.AlignLeft

            // Icon
            iconText: {
                if (isGroup) {
                    return expanded ? MaterialIcons.expand_more : MaterialIcons.chevron_right
                }
                return ""
            }
            iconSize: 7
            icon.horizontalAlignment: attribute && attribute.isOutput ? Text.AlignRight : Text.AlignLeft

            // Handle tree view for nested attributes
            icon.leftPadding: {
                if (attribute.depth != 0 && !attribute.isOutput) {
                    return attribute.depth * 10
                }
                return 0
            }
            icon.rightPadding: {
                if (attribute.depth != 0 && attribute.isOutput) {
                    return attribute.depth * 10
                }
                return 0
            }
        }
    }

    Rectangle {
        id: outputAnchor

        visible: displayOutputPinForInput || attribute.isOutput
        width: 8
        height: width
        radius: isList ? 0 : width / 2

        Layout.alignment: Qt.AlignVCenter

        border.color: Colors.sysPalette.mid
        color: Colors.sysPalette.base

        Rectangle {
            id: innerOutputAnchor
            property bool linkEnabled: true
            visible: (attribute.hasOutputConnections && linkEnabled) || outputConnectMA.containsMouse || outputConnectMA.drag.active || outputDropArea.containsDrag
            radius: isList ? 0 : 2
            anchors.fill: parent
            anchors.margins: 2
            color: {
                if (modelData.enabled && (outputConnectMA.containsMouse || outputConnectMA.drag.active ||
                                          (outputDropArea.containsDrag && outputDropArea.acceptableDrop)))
                    return Colors.sysPalette.highlight
                return Colors.sysPalette.text
            }
        }

        DropArea {
            id: outputDropArea

            property bool acceptableDrop: false

            // Add negative margins for DropArea to make the connection zone easier to reach
            anchors.fill: parent
            anchors.margins: -2
            // Add horizontal negative margins according to the current layout
            anchors.leftMargin: -root.width * 0.2

            keys: [outputDragTarget.objectName]
            onEntered: function(drag) {
                // Check if attributes are compatible to create a valid connection
                if (drag.source.objectName != outputDragTarget.objectName   // Not an edge connector
                    || drag.source.baseType !== outputDragTarget.baseType   // Not the same base type
                    || drag.source.nodeItem === outputDragTarget.nodeItem   // Connection between attributes of the same node
                    || (!drag.source.isList && outputDragTarget.isList)     // Connection between a list and a simple attribute
                    || (drag.source.isList && childrenRepeater.count)       // Source/target are lists but target already has children
                    || drag.source.connectorType === "output"               // Refuse to connect an output pin on another one
                   ) {
                    // Refuse attributes connection
                    drag.accepted = false
                } else if (drag.source.attribute.isLink) {  // Already connected attribute
                    root.edgeAboutToBeRemoved(drag.source.attribute)
                }
                outputDropArea.acceptableDrop = drag.accepted
            }
            onExited: {
                root.edgeAboutToBeRemoved(undefined)
                acceptableDrop = false
            }

            onDropped: function(drop) {
                root.edgeAboutToBeRemoved(undefined)
                _reconstruction.addEdge(outputDragTarget.attribute, drag.source.attribute)
            }
        }

        Item {
            id: outputDragTarget
            objectName: "edgeConnector"
            readonly property string connectorType: "output"
            readonly property alias attribute: root.attribute
            readonly property alias nodeItem: root.nodeItem
            readonly property bool isOutput: Boolean(attribute.isOutput)
            readonly property alias isList: root.isList
            readonly property string baseType: attribute.baseType !== undefined ? attribute.baseType : ""
            property bool dropAccepted: false
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width
            height: parent.height
            Drag.keys: [outputDragTarget.objectName]
            Drag.active: outputConnectMA.drag.active
            Drag.hotSpot.x: width * 0.5
            Drag.hotSpot.y: height * 0.5
        }

        MouseArea {
            id: outputConnectMA
            drag.target: outputDragTarget
            drag.threshold: 0
            // Move the edge's tip straight to the the current mouse position instead of waiting after the drag operation has started
            drag.smoothed: false
            anchors.fill: parent
            // Use the same negative margins as DropArea to ease pin selection
            anchors.margins: outputDropArea.anchors.margins
            anchors.leftMargin: outputDropArea.anchors.leftMargin
            anchors.rightMargin: outputDropArea.anchors.rightMargin

            onPressed: function(mouse) { root.pressed(mouse) }
            onReleased: outputDragTarget.Drag.drop()
            onClicked: root.clicked()

            hoverEnabled: root.visible
        }

        Edge {
            id: outputConnectEdge
            visible: false
            point1x: parent.width / 2
            point1y: parent.width / 2
            point2x: outputDragTarget.x + outputDragTarget.width / 2
            point2y: outputDragTarget.y + outputDragTarget.height / 2
            color: palette.highlight
            thickness: outputDragTarget.dropAccepted ? 2 : 1
        }
    }

    state: (inputConnectMA.pressed) ? "DraggingInput" : outputConnectMA.pressed ? "DraggingOutput" : ""

    states: [
        State {
            name: ""
            AnchorChanges {
                target: outputDragTarget
                anchors.horizontalCenter: outputAnchor.horizontalCenter
                anchors.verticalCenter: outputAnchor.verticalCenter
            }
            AnchorChanges {
                target: inputDragTarget
                anchors.horizontalCenter: inputAnchor.horizontalCenter
                anchors.verticalCenter: inputAnchor.verticalCenter
            }
            PropertyChanges {
                target: inputDragTarget
                x: 0
                y: 0
            }
            PropertyChanges {
                target: outputDragTarget
                x: 0
                y: 0
            }
        },

        State {
            name: "DraggingInput"
            AnchorChanges {
                target: inputDragTarget
                anchors.horizontalCenter: undefined
                anchors.verticalCenter: undefined
            }
            PropertyChanges {
                target: inputConnectEdge
                z: 100
                visible: true
            }
            StateChangeScript {
                script: {
                    // Add the right offset if the initial click is not exactly at the center of the connection circle.
                    var pos = inputDragTarget.mapFromItem(inputConnectMA, inputConnectMA.mouseX, inputConnectMA.mouseY);
                    inputDragTarget.x = pos.x - inputDragTarget.width / 2;
                    inputDragTarget.y = pos.y - inputDragTarget.height / 2;
                }
            }
        },
        State {
            name: "DraggingOutput"
            AnchorChanges {
                target: outputDragTarget
                anchors.horizontalCenter: undefined
                anchors.verticalCenter: undefined
            }
            PropertyChanges {
                target: outputConnectEdge
                z: 100
                visible: true
            }
            StateChangeScript {
                script: {
                    var pos = outputDragTarget.mapFromItem(outputConnectMA, outputConnectMA.mouseX, outputConnectMA.mouseY);
                    outputDragTarget.x = pos.x - outputDragTarget.width / 2;
                    outputDragTarget.y = pos.y - outputDragTarget.height / 2;
                }
            }
        }
    ]
}
