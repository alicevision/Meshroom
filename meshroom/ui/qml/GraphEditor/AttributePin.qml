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

    objectName: attribute.name + "."
    layoutDirection: attribute.isOutput ? Qt.RightToLeft : Qt.LeftToRight
    spacing: 1

    // Instantiate empty Items for each child attribute
    Repeater {
        model: isList && !attribute.isLink ? attribute.value : 0
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
        Layout.alignment: Qt.AlignVCenter
        border.color: "#3e3e3e"
        color: (dropArea.containsDrag && dropArea.containsDrag) || attribute.isLink ? "#3e3e3e" : "white"

        DropArea {
            id: dropArea

            property bool acceptableDrop: false

            anchors.fill: parent
            keys: [dragTarget.objectName]
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
            Drag.keys: [dragTarget.objectName]
            Drag.active: connectMA.drag.active
            Drag.hotSpot.x: width*0.5
            Drag.hotSpot.y: height*0.5
        }

        MouseArea {
            id: connectMA
            drag.target: dragTarget
            drag.threshold: 0
            enabled: !root.readOnly
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
        elide: Text.ElideMiddle
        Layout.fillWidth: true
        font.pointSize: 5
        horizontalAlignment: attribute.isOutput ? Text.AlignRight : Text.AlignLeft

        // Extend truncated names at mouse hover
        MouseArea {
            id: ma
            anchors.fill: parent
            enabled: parent.truncated
            visible: enabled
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
        }
        Loader {
            active: ma.containsMouse
            anchors.right: root.layoutDirection == Qt.LeftToRight ? undefined : nameLabel.right
            // Non-elided label
            sourceComponent: Label {
                leftPadding: root.layoutDirection == Qt.LeftToRight ? 0 : 1
                rightPadding: root.layoutDirection == Qt.LeftToRight ? 1 : 0
                text: attribute.name
                background: Rectangle {
                    color: parent.palette.window
                }
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
