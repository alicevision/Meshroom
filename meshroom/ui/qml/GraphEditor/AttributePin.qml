import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

/**
  The representation of an Attribute on a Node.
*/
RowLayout {
    id: root

    property var nodeItem
    property var attribute
    property bool readOnly: false

    // position of the anchor for attaching and edge to this attribute pin
    readonly property point edgeAnchorPos: Qt.point(edgeAnchor.x + edgeAnchor.width/2,
                                                    edgeAnchor.y + edgeAnchor.height/2)

    readonly property bool isList: attribute.type == "ListAttribute"

    signal childPinCreated(var childAttribute, var pin)
    signal childPinDeleted(var childAttribute, var pin)

    signal pressed(var mouse)

    objectName: attribute.name + "."
    layoutDirection: attribute.isOutput ? Qt.RightToLeft : Qt.LeftToRight
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
        id: edgeAnchor

        width: 7
        height: width
        radius: isList ? 0 : width/2
        Layout.alignment: Qt.AlignVCenter
        border.color: "#3e3e3e"
        color: {
            if(connectMA.containsMouse || connectMA.drag.active || (dropArea.containsDrag && dropArea.acceptableDrop))
                return nameLabel.palette.highlight
            else if(attribute.isLink)
                return "#3e3e3e"
            return "white"
        }

        DropArea {
            id: dropArea

            property bool acceptableDrop: false

            // add negative margins for DropArea to make the connection zone easier to reach
            anchors.fill: parent
            anchors.margins: -2
            // add horizontal negative margins according to the current layout
            anchors.leftMargin: root.layoutDirection == Qt.RightToLeft ?  -root.width * 0.3 : 0
            anchors.rightMargin: root.layoutDirection == Qt.LeftToRight ?  -root.width * 0.3 : 0

            keys: [dragTarget.objectName]
            onEntered: {
                // Filter drops:
                if( drag.source.objectName != dragTarget.objectName  // not an edge connector
                   ||  drag.source.nodeItem == dragTarget.nodeItem   // connection between attributes of the same node
                   || dragTarget.isOutput                            // connection on an output
                   || dragTarget.attribute.isLink                    // already connected attribute
                   || (drag.source.isList && !dragTarget.isList)     // connection between a list and a simple attribute
                   || (drag.source.isList && childrenRepeater.count) // source/target are lists but target already has children
                   )
                {
                    drag.accepted = false
                }
                dropArea.acceptableDrop = drag.accepted
            }
            onExited: acceptableDrop = false

            onDropped: {
                _reconstruction.addEdge(drag.source.attribute, dragTarget.attribute)
            }
        }

        Item {
            id: dragTarget
            objectName: "edgeConnector"
            readonly property alias attribute: root.attribute
            readonly property alias nodeItem: root.nodeItem
            readonly property bool isOutput: attribute.isOutput
            readonly property alias isList: root.isList
            anchors.centerIn: root.state == "Dragging" ? undefined : parent
            width: 4
            height: 4
            Drag.keys: [dragTarget.objectName]
            Drag.active: connectMA.drag.active
            Drag.hotSpot.x: width*0.5
            Drag.hotSpot.y: height*0.5
            anchors.onCenterInChanged: {
                // snap dragTarget to current mouse position in connectMA
                if(anchors.centerIn == undefined) {
                    var pos = mapFromItem(connectMA, connectMA.mouseX, connectMA.mouseY)
                    x = pos.x
                    y = pos.y
                }
            }
        }

        MouseArea {
            id: connectMA
            drag.target: dragTarget
            drag.threshold: 0
            enabled: !root.readOnly
            anchors.fill: parent
            // use the same negative margins as DropArea to ease pin selection
            anchors.margins: dropArea.anchors.margins
            anchors.leftMargin: dropArea.anchors.leftMargin
            anchors.rightMargin: dropArea.anchors.rightMargin
            onPressed: root.pressed(mouse)
            onReleased: dragTarget.Drag.drop()
            hoverEnabled: true
        }

        Edge {
            id: connectEdge
            visible: false
            point1x: parent.width / 2
            point1y: parent.width / 2
            point2x: dragTarget.x + dragTarget.width/2
            point2y: dragTarget.y + dragTarget.height/2
            color: nameLabel.color
        }
    }

    // Attribute name
    Item {
        id: nameContainer
        Layout.fillWidth: true
        implicitHeight: childrenRect.height

        TextMetrics {
            id: metrics
            property bool truncated: width > nameContainer.width
            text: nameLabel.text
            font: nameLabel.font
        }

        Label {
            id: nameLabel

            property bool hovered: (connectMA.containsMouse || connectMA.drag.active || dropArea.containsDrag)
            text: attribute.name
            elide: hovered ? Text.ElideNone : Text.ElideMiddle
            width: hovered ? contentWidth : parent.width
            font.pointSize: 5
            horizontalAlignment: attribute.isOutput ? Text.AlignRight : Text.AlignLeft
            anchors.right: attribute.isOutput ? parent.right : undefined

            background: Rectangle {
                visible: parent.hovered && metrics.truncated
                anchors { fill: parent; leftMargin: -1; rightMargin: -1 }
                color: parent.palette.window
            }
        }
    }

    state: connectMA.pressed ? "Dragging" : ""

    states: [
        State {
            name: ""
        },

        State {
            name: "Dragging"
            PropertyChanges {
                target: connectEdge
                z: 100
                visible: true
            }
        }
    ]

}
