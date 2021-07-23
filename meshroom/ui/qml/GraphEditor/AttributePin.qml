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
    /// Whether to display an output pin for input attribute
    property bool displayOutputPinForInput: true

    // position of the anchor for attaching and edge to this attribute pin
    readonly property point inputAnchorPos: Qt.point(inputAnchor.x + inputAnchor.width/2,
                                                    inputAnchor.y + inputAnchor.height/2)

    readonly property point outputAnchorPos: Qt.point(outputAnchor.x + outputAnchor.width/2,
                                                    outputAnchor.y + outputAnchor.height/2)

    readonly property bool isList: attribute && attribute.type === "ListAttribute"

    signal childPinCreated(var childAttribute, var pin)
    signal childPinDeleted(var childAttribute, var pin)

    signal pressed(var mouse)
    signal edgeAboutToBeRemoved(var input)

    objectName: attribute ? attribute.name + "." : ""
    layoutDirection: Qt.LeftToRight
    spacing: 3

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

        width: 8
        height: width
        radius: isList ? 0 : width/2
        Layout.alignment: Qt.AlignVCenter

        border.color:  Colors.sysPalette.mid
        color: Colors.sysPalette.base

        Rectangle {
            visible: inputConnectMA.containsMouse || childrenRepeater.count > 0 || (attribute && attribute.isLink)
            radius: isList ? 0 : 2
            anchors.fill: parent
            anchors.margins: 2
            color: {
                if(inputConnectMA.containsMouse || inputConnectMA.drag.active || (inputDropArea.containsDrag && inputDropArea.acceptableDrop))
                    return Colors.sysPalette.highlight
                return Colors.sysPalette.text
            }
        }

        DropArea {
            id: inputDropArea

            property bool acceptableDrop: false

            // add negative margins for DropArea to make the connection zone easier to reach
            anchors.fill: parent
            anchors.margins: -2
            // add horizontal negative margins according to the current layout
            anchors.rightMargin: -root.width * 0.3

            keys: [inputDragTarget.objectName]
            onEntered: {
                // Check if attributes are compatible to create a valid connection
                if( root.readOnly                                         // cannot connect on a read-only attribute
                  || drag.source.objectName != inputDragTarget.objectName // not an edge connector
                  || drag.source.baseType != inputDragTarget.baseType     // not the same base type
                  || drag.source.nodeItem == inputDragTarget.nodeItem     // connection between attributes of the same node
                  || (drag.source.isList && !inputDragTarget.isList)      // connection between a list and a simple attribute
                  || (drag.source.isList && childrenRepeater.count)       // source/target are lists but target already has children
                  || drag.source.connectorType == "input"                 // refuse to connect an "input pin" on another one (input attr can be connected to input attr, but not the graphical pin)
                  )
                {
                    // Refuse attributes connection
                    drag.accepted = false
                }
                else if (inputDragTarget.attribute.isLink) { // already connected attribute
                    root.edgeAboutToBeRemoved(inputDragTarget.attribute)
                }
                inputDropArea.acceptableDrop = drag.accepted
            }
            onExited: {
                if (inputDragTarget.attribute.isLink) { // already connected attribute
                    root.edgeAboutToBeRemoved(undefined)
                }
                acceptableDrop = false
                drag.source.dropAccepted = false
            }

            onDropped: {
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
            readonly property bool isOutput: attribute.isOutput
            readonly property string baseType: attribute.baseType
            readonly property alias isList: root.isList
            property bool dragAccepted: false
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            width: 4
            height: 4
            Drag.keys: [inputDragTarget.objectName]
            Drag.active: inputConnectMA.drag.active
            Drag.hotSpot.x: width*0.5
            Drag.hotSpot.y: height*0.5
        }

        MouseArea {
            id: inputConnectMA
            drag.target: attribute.isReadOnly ? undefined : inputDragTarget
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
            color: palette.highlight
            thickness: outputDragTarget.dropAccepted ? 2 : 1
        }
    }



    // Attribute name
    Item {
        id: nameContainer
        Layout.fillWidth: true
        implicitHeight: childrenRect.height

        Label {
            id: nameLabel

            enabled: !root.readOnly
            property bool hovered: (inputConnectMA.containsMouse || inputConnectMA.drag.active || inputDropArea.containsDrag || outputConnectMA.containsMouse || outputConnectMA.drag.active || outputDropArea.containsDrag)
            text: attribute ? attribute.label : ""
            elide: hovered ? Text.ElideNone : Text.ElideMiddle
            width: hovered ? contentWidth : parent.width
            font.pointSize: 7
            horizontalAlignment: attribute && attribute.isOutput ? Text.AlignRight : Text.AlignLeft
            anchors.right: attribute && attribute.isOutput ? parent.right : undefined
            rightPadding: 0
            color: hovered ? palette.highlight : palette.text
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
            visible: attribute.hasOutputConnections
            radius: isList ? 0 : 2
            anchors.fill: parent
            anchors.margins: 2
            color: {
                if(outputConnectMA.containsMouse || outputConnectMA.drag.active || (outputDropArea.containsDrag && outputDropArea.acceptableDrop))
                    return Colors.sysPalette.highlight
                return Colors.sysPalette.text
            }
        }

        DropArea {
            id: outputDropArea

            property bool acceptableDrop: false

            // add negative margins for DropArea to make the connection zone easier to reach
            anchors.fill: parent
            anchors.margins: -2
            // add horizontal negative margins according to the current layout
            anchors.leftMargin: -root.width * 0.2

            keys: [outputDragTarget.objectName]
            onEntered: {
                // Check if attributes are compatible to create a valid connection
                if( drag.source.objectName != outputDragTarget.objectName // not an edge connector
                  || drag.source.baseType != outputDragTarget.baseType    // not the same base type
                  || drag.source.nodeItem == outputDragTarget.nodeItem    // connection between attributes of the same node
                  || (!drag.source.isList && outputDragTarget.isList)     // connection between a list and a simple attribute
                  || (drag.source.isList && childrenRepeater.count)       // source/target are lists but target already has children
                  || drag.source.connectorType == "output"                // refuse to connect an output pin on another one
                  )
                {
                    // Refuse attributes connection
                    drag.accepted = false
                }
                else if (drag.source.attribute.isLink) { // already connected attribute
                    root.edgeAboutToBeRemoved(drag.source.attribute)
                }
                outputDropArea.acceptableDrop = drag.accepted
            }
            onExited: {
                root.edgeAboutToBeRemoved(undefined)
                acceptableDrop = false
            }

            onDropped: {
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
            readonly property bool isOutput: attribute.isOutput
            readonly property alias isList: root.isList
            readonly property string baseType: attribute.baseType
            property bool dropAccepted: false
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            width: 4
            height: 4
            Drag.keys: [outputDragTarget.objectName]
            Drag.active: outputConnectMA.drag.active
            Drag.hotSpot.x: width*0.5
            Drag.hotSpot.y: height*0.5
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

            onPressed: root.pressed(mouse)
            onReleased: outputDragTarget.Drag.drop()

            hoverEnabled: true
        }

        Edge {
            id: outputConnectEdge
            visible: false
            point1x: parent.width / 2
            point1y: parent.width / 2
            point2x: outputDragTarget.x + outputDragTarget.width/2
            point2y: outputDragTarget.y + outputDragTarget.height/2
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
                    var pos = inputDragTarget.mapFromItem(inputConnectMA, inputConnectMA.mouseX, inputConnectMA.mouseY);
                    inputDragTarget.x = pos.x - inputDragTarget.width/2;
                    inputDragTarget.y = pos.y - inputDragTarget.height/2;
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
                    outputDragTarget.x = pos.x - outputDragTarget.width/2;
                    outputDragTarget.y = pos.y - outputDragTarget.height/2;
                }
            }
        }
    ]

}
