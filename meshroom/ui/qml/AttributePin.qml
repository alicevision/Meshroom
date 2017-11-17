import QtQuick 2.9
import QtQuick.Controls 2.3

/**
  The representation of an Attribute on a Node.
*/
Row {
    id: root

    property var nodeItem
    property var attribute

    // position of the anchor for attaching and edge to this attribute pin
    readonly property point edgeAnchorPos: Qt.point(edgeAnchor.x + edgeAnchor.width/2,
                                                    edgeAnchor.y + edgeAnchor.height/2)

    readonly property bool isList: attribute.type == "ListAttribute"

    signal childPinCreated(var childAttribute, var pin)
    signal childPinDeleted(var childAttribute, var pin)

    objectName: attribute.name + "."
    layoutDirection: attribute.isOutput ? Qt.RightToLeft : Qt.LeftToRight
    spacing: 1

    // Instantiate empty Items for each child attribute
    Repeater {
        model: isList ? attribute.value : ""
        onItemAdded: {childPinCreated(item.childAttribute, item)}
        onItemRemoved: {childPinDeleted(item.childAttribute, item)}
        delegate: Item {
            property var childAttribute: object
        }
    }

    Rectangle {
        id: edgeAnchor

        width: 6
        height: width
        radius: isList ? 0 : width/2
        anchors.verticalCenter: parent.verticalCenter
        border.color: "#3e3e3e"
        color: (dropArea.containsDrag && dropArea.containsDrag) || attribute.isLink ? "#3e3e3e" : "white"

        DropArea {
            id: dropArea

            property bool acceptableDrop: false

            anchors.fill: parent

            onEntered: {
                // Filter drops:
                if( drag.source.objectName != dragTarget.objectName  // not an edge connector
                   ||  drag.source.nodeItem == dragTarget.nodeItem   // connection between attributes of the same node
                   || dragTarget.isOutput                            // connection on an output
                   || dragTarget.attribute.isLink)                   // already connected attribute
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
            //anchors.verticalCenter: root.verticalCenter
            width: 2
            height: 2
            Drag.active: connectMA.drag.active
            Drag.hotSpot.x: width*0.5
            Drag.hotSpot.y: height*0.5
        }

        MouseArea {
            id: connectMA
            drag.target: dragTarget
            drag.threshold: 0
            anchors.fill: parent
            onReleased: dragTarget.Drag.drop()
        }

        Edge {
            id: connectEdge
            visible: false
            point1x: parent.width / 2
            point1y: parent.width / 2
            point2x: dragTarget.x + dragTarget.width/2
            point2y: dragTarget.y + dragTarget.height/2
            color: nameLabel.palette.text
        }
    }

    // Attribute name
    Label {
        id: nameLabel
        text: attribute.name
        font.pointSize: 5
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
