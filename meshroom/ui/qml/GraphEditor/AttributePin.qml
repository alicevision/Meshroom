import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import Utils 1.0

/**
  The representation of an Attribute on a Node.
*/
RowLayout {
    id: root

    property var nodeItem
    property var attribute
    property bool readOnly: false

    // position of the anchor for attaching and edge to this attribute pin
    readonly property point inputAnchorPos: Qt.point(inputAnchor.x + inputAnchor.width/2,
                                                    inputAnchor.y + inputAnchor.height/2)

    readonly property point outputAnchorPos: Qt.point(outputAnchor.x + outputAnchor.width/2,
                                                    outputAnchor.y + outputAnchor.height/2)

    readonly property bool isList: attribute.type == "ListAttribute"

    signal childPinCreated(var childAttribute, var pin)
    signal childPinDeleted(var childAttribute, var pin)

    signal pressed(var mouse)


    objectName: attribute.name + "."
    layoutDirection: Qt.LeftToRight
    spacing: 2

    // Instantiate empty Items for each child attribute
    Repeater {
        id: childrenRepeater
        model: isList && !attribute.isLink ? attribute.value : 0
        onItemAdded: {childPinCreated(item.childAttribute, item)}
        onItemRemoved: {childPinDeleted(item.childAttribute, item)}
        delegate: Item {
            property var childAttribute: object
        }
    }

    Rectangle {
        visible: !attribute.isOutput
        id: inputAnchor

        width: 7
        height: width
        radius: isList ? 0 : width/2
        Layout.alignment: Qt.AlignVCenter
        border.color: "#3e3e3e"
        color: {
            if(inputConnectMA.containsMouse || inputConnectMA.drag.active || (inputDropArea.containsDrag && inputDropArea.acceptableDrop))
                return nameLabel.palette.highlight
            else if(attribute.isLink)
                return "#3e3e3e"
            return "white"
        }

        DropArea {
            id: inputDropArea

            property bool acceptableDrop: false

            // add negative margins for DropArea to make the connection zone easier to reach
            anchors.fill: parent
            anchors.margins: -2
            // add horizontal negative margins according to the current layout
            anchors.rightMargin: -root.width * 0.45

            keys: [inputDragTarget.objectName]
            onEntered: {
                // Filter drops:
                  if( root.readOnly
                   || drag.source.objectName != inputDragTarget.objectName  // not an edge connector
                   || drag.source.nodeItem == inputDragTarget.nodeItem   // connection between attributes of the same node
                   || inputDragTarget.attribute.isLink                    // already connected attribute
                   || (drag.source.isList && !inputDragTarget.isList)     // connection between a list and a simple attribute
                   || (drag.source.isList && childrenRepeater.count) // source/target are lists but target already has children
                   || drag.source.connectorType == "input"
                   )
                {
                    drag.accepted = false
                }
                inputDropArea.acceptableDrop = drag.accepted
            }
            onExited: {
                acceptableDrop = false
            }

            onDropped: {
                _reconstruction.addEdge(drag.source.attribute, inputDragTarget.attribute)
            }
        }

        Item {
            id: inputDragTarget
            objectName: "edgeConnector"
            readonly property string connectorType: "input"
            readonly property alias attribute: root.attribute
            readonly property alias nodeItem: root.nodeItem
            readonly property bool isOutput: attribute.isOutput
            readonly property alias isList: root.isList
            anchors.centerIn: root.state == "DraggingInput" ? undefined : parent
            width: 4
            height: 4
            Drag.keys: [inputDragTarget.objectName]
            Drag.active: inputConnectMA.drag.active
            Drag.hotSpot.x: width*0.5
            Drag.hotSpot.y: height*0.5
            anchors.onCenterInChanged: {
                // snap inputDragTarget to current mouse position in inputConnectMA
                if(anchors.centerIn == undefined) {
                    var pos = mapFromItem(inputConnectMA, inputConnectMA.mouseX, inputConnectMA.mouseY)
                    x = pos.x
                    y = pos.y
                }
            }
        }

        MouseArea {
            id: inputConnectMA
            // If an input attribute is connected (isLink), we disable drag&drop
            drag.target: attribute.isLink ? undefined : inputDragTarget
            drag.threshold: 0
            enabled: !root.readOnly
            anchors.fill: parent
            // use the same negative margins as DropArea to ease pin selection
            anchors.margins: inputDropArea.anchors.margins
            anchors.leftMargin: inputDropArea.anchors.leftMargin
            anchors.rightMargin: inputDropArea.anchors.rightMargin
            onPressed: {
                root.pressed(mouse)
            }
            onReleased: {
                inputDragTarget.Drag.drop()
            }
            hoverEnabled: true
        }

        Edge {
            id: inputConnectEdge
            visible: false
            point1x: inputDragTarget.x + inputDragTarget.width/2
            point1y: inputDragTarget.y + inputDragTarget.height/2
            point2x: parent.width / 2
            point2y: parent.width / 2
            color: nameLabel.color
            thickness: outputDragTarget.dropAccepted ? 2 : 1
        }
    }



    // Attribute name
    Item {
        id: nameContainer
        Layout.fillWidth: true
        implicitHeight: 10

        Label {
            id: nameLabel

            property bool hovered: (inputConnectMA.containsMouse || inputConnectMA.drag.active || inputDropArea.containsDrag || outputConnectMA.containsMouse || outputConnectMA.drag.active || outputDropArea.containsDrag)
            text: attribute.name
            elide: hovered ? Text.ElideNone : Text.ElideMiddle
            width: hovered ? contentWidth : parent.width
            font.pointSize: 5
            horizontalAlignment: attribute.isOutput ? Text.AlignRight : Text.AlignLeft
            anchors.right: attribute.isOutput ? parent.right : undefined
            rightPadding: 0
            color: hovered ? Colors.sysPalette.highlight : Colors.sysPalette.text
        }
    }

    Rectangle {
        id: outputAnchor

        width: 7
        height: width
        radius: isList ? 0 : width/2
        Layout.alignment: Qt.AlignVCenter
        border.color: "#3e3e3e"
        color: {
            if(outputConnectMA.containsMouse || outputConnectMA.drag.active || (outputDropArea.containsDrag && outputDropArea.acceptableDrop))
                return nameLabel.palette.highlight
            return attribute.isOutput ? "white" : "#75a0bd"
        }

        DropArea {
            id: outputDropArea

            property bool acceptableDrop: false

            // add negative margins for DropArea to make the connection zone easier to reach
            anchors.fill: parent
            anchors.margins: -2
            // add horizontal negative margins according to the current layout
            anchors.leftMargin: attribute.isOutput ? -root.width * 0.9 : -root.width * 0.42

            keys: [outputDragTarget.objectName]
            onEntered: {
                // Filter drops:
                if( drag.source.objectName != outputDragTarget.objectName  // not an edge connector
                   ||  drag.source.nodeItem == outputDragTarget.nodeItem   // connection between attributes of the same node
                   || drag.source.attribute.isLink                                   // already connected attribute
                   || (!drag.source.isList && outputDragTarget.isList)     // connection between a list and a simple attribute
                   || (drag.source.isList && childrenRepeater.count) // source/target are lists but target already has children
                   || drag.source.connectorType == "output"
                   )
                {
                    drag.accepted = false
                }
                outputDropArea.acceptableDrop = drag.accepted
            }
            onExited: acceptableDrop = false

            onDropped: {
                _reconstruction.addEdge(outputDragTarget.attribute, drag.source.attribute)
            }
        }

        Item {
            id: outputDragTarget
            objectName: "edgeConnector"
            readonly property string connectorType: "output"
            readonly property alias attribute: root.attribute
            readonly property alias nodeItem: root.nodeItem
            readonly property bool isOutput: attribute.isOutput
            readonly property alias isList: root.isList
            anchors.centerIn: root.state == "DraggingOutput" ? undefined : parent
            width: 4
            height: 4
            Drag.keys: [outputDragTarget.objectName]
            Drag.active: outputConnectMA.drag.active
            Drag.hotSpot.x: width*0.5
            Drag.hotSpot.y: height*0.5
            anchors.onCenterInChanged: {
                if(anchors.centerIn == undefined) {
                    var pos = mapFromItem(outputConnectMA, outputConnectMA.mouseX, outputConnectMA.mouseY)
                    x = pos.x
                    y = pos.y
                }
            }
        }

        MouseArea {
            id: outputConnectMA
            drag.target: outputDragTarget
            drag.threshold: 0
            anchors.fill: parent
            // use the same negative margins as DropArea to ease pin selection
            anchors.margins: outputDropArea.anchors.margins
            anchors.leftMargin: outputDropArea.anchors.leftMargin
            anchors.rightMargin: outputDropArea.anchors.rightMargin
            onPressed: {
                root.pressed(mouse)
            }
            onReleased: {
                outputDragTarget.Drag.drop()
            }
            hoverEnabled: true
        }

        Edge {
            id: outputConnectEdge
            visible: false
            point1x: parent.width / 2
            point1y: parent.width / 2
            point2x: outputDragTarget.x + outputDragTarget.width/2
            point2y: outputDragTarget.y + outputDragTarget.height/2
            color: nameLabel.color
            thickness: outputDragTarget.dropAccepted ? 2 : 1
        }
    }

    state: (inputConnectMA.pressed && !attribute.isLink) ? "DraggingInput" : outputConnectMA.pressed ? "DraggingOutput" : ""

    states: [
        State {
            name: ""
        },

        State {
            name: "DraggingInput"
            PropertyChanges {
                target: inputConnectEdge
                z: 100
                visible: true
            }
        },
        State {
            name: "DraggingOutput"
            PropertyChanges {
                target: outputConnectEdge
                z: 100
                visible: true
            }
        }
    ]

}
