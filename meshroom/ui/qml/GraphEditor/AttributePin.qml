import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Utils 1.0
import MaterialIcons 2.2
import "AnySetUtils.js" as AnySetUtils

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
    /// Compact mode: hides the attribute label, showing only the connection circle.
    /// Useful for embedding the pin in space-constrained areas like the node header.
    property bool compact: false

    // position of the anchor for attaching and edge to this attribute pin
    readonly property point inputAnchorPos: Qt.point(inputAnchor.x + inputAnchor.width / 2,
                                                     inputAnchor.y + inputAnchor.height / 2)

    readonly property point outputAnchorPos: Qt.point(outputAnchor.x + outputAnchor.width / 2,
                                                      outputAnchor.y + outputAnchor.height / 2)

    readonly property bool isList: attribute && attribute.type === "ListAttribute"
    readonly property bool isExpandable: attribute && attribute.isExpandable === true
    readonly property bool isDynamic: !!attribute.desc && !!attribute.desc.isCustomAttribute
    readonly property bool isAnySetChild: !!attribute && !!attribute.root && attribute.root.type === "AnySet"
    readonly property bool isConnected: attribute.hasAnyInputLinks || attribute.hasAnyOutputLinks

    signal childPinCreated(var childAttribute, var pin)
    signal childPinDeleted(var childAttribute, var pin)

    signal pressed(var mouse)
    signal edgeAboutToBeRemoved(var input)
    signal clicked()

    Component {
        id: removeAnySetAttributeMenuComp
        Menu {
            id: anySetMenu

            property real preferredX: 0
            property real preferredY: 0

            MenuItem {
                text: "Move Up"
                enabled: AnySetUtils.canMoveBy(attribute, -1)
                onTriggered: _currentScene.moveAnySetAttribute(attribute, -1)
            }
            MenuItem {
                text: "Move Down"
                enabled: AnySetUtils.canMoveBy(attribute, 1)
                onTriggered: _currentScene.moveAnySetAttribute(attribute, 1)
            }
            MenuSeparator {}
            MenuItem {
                text: "Rename Attribute"
                enabled: root.isAnySetChild
                onTriggered: {
                    var dialog = renameAnySetAttributeDialogComp.createObject(Overlay.overlay, {
                        "targetAttribute": attribute,
                        "preferredX": anySetMenu.preferredX,
                        "preferredY": anySetMenu.preferredY
                    })
                    dialog.open()
                }
            }
            MenuItem {
                text: "Remove Attribute"
                enabled: root.isAnySetChild
                onTriggered: _currentScene.removeAnySetAttribute(attribute)
            }
        }
    }

    Component {
        id: renameAnySetAttributeDialogComp
        Dialog {
            id: renameDialog

            property var targetAttribute: null
            property real preferredX: 0
            property real preferredY: 0

            title: "Rename Attribute"
            modal: true
            parent: Overlay.overlay
            contentWidth: 280
            x: parent ? Math.max(0, Math.min(preferredX, parent.width - width)) : 0
            y: parent ? Math.max(0, Math.min(preferredY, parent.height - height)) : 0
            standardButtons: Dialog.Ok | Dialog.Cancel
            closePolicy: Popup.CloseOnEscape

            GridLayout {
                columns: 2
                columnSpacing: 8
                rowSpacing: 8
                width: renameDialog.contentWidth

                Label {
                    text: "Name"
                    Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                }
                TextField {
                    id: nameField
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    text: renameDialog.targetAttribute ? renameDialog.targetAttribute.name : ""
                    selectByMouse: true
                    validator: RegularExpressionValidator { regularExpression: /^[A-Za-z_][A-Za-z0-9_]*$/ }
                    onAccepted: renameDialog.accept()
                }

                Label {
                    text: "Label"
                    Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                }
                TextField {
                    id: labelField
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    text: renameDialog.targetAttribute ? renameDialog.targetAttribute.label : ""
                    selectByMouse: true
                    onAccepted: renameDialog.accept()
                }
            }

            onOpened: {
                nameField.forceActiveFocus()
                nameField.selectAll()
            }

            onAccepted: {
                if (targetAttribute && nameField.acceptableInput && labelField.text.trim() !== "") {
                    _currentScene.renameAnySetAttribute(targetAttribute, nameField.text.trim(), labelField.text.trim())
                }
                destroy()
            }

            onRejected: destroy()
        }
    }

    objectName: attribute ? attribute.name + "." : ""
    layoutDirection: Qt.LeftToRight
    spacing: 3
    height: attribute && attribute.isOutput ? outputAnchor.height : inputAnchor.height

    function getCurrentAttributePinColor(hasChildrenConnected) {
        if (root.isDynamic) {
            return "transparent"
        }
        if (hasChildrenConnected) {
            return Colors.sysPalette.iconText
        }
        return Colors.sysPalette.mid
    }

    ToolTip {
        text: attribute.fullName + ": " + attribute.type
        visible: nameLabel.hovered
        delay: 500

        x: nameLabel.x
        y: nameLabel.y + nameLabel.height
    }

    // Instantiate empty Items for each child attribute
    Repeater {
        id: childrenRepeater
        model: root.isList && !root.attribute.isLink ? root.attribute.value : 0
        onItemAdded: function(index, item) { childPinCreated(item.childAttribute, root) }
        onItemRemoved: function(index, item) { childPinDeleted(item.childAttribute, root) }
        delegate: Item {
            property var childAttribute: object
            visible: false
        }
    }

    Item {
        width: childrenRect.width
        Layout.alignment: Qt.AlignVCenter
        Layout.fillWidth: !root.compact
        Layout.fillHeight: true

        Rectangle {
            id: inputAnchor
            visible: !root.attribute.isOutput

            width: 8
            height: width
            radius: root.isList ? 0 : width / 2
            Layout.alignment: Qt.AlignVCenter

            border.color: getCurrentAttributePinColor(innerInputAnchor.hasConnectedChildren)
            color: Colors.sysPalette.base

            Rectangle {
                id: innerInputAnchor
                property bool linkEnabled: true
                property bool hasConnectedChildren: {
                    if (!isExpandable || root.isConnected || !attribute)
                        return false
                    for (var i = 0; i < attribute.flatStaticChildren.length; ++i) {
                        if (attribute.flatStaticChildren[i].hasAnyInputLinks) {
                            return true
                        }
                    }
                    return false
                }
                visible: inputConnectMA.containsMouse || childrenRepeater.count > 0 || hasConnectedChildren ||
                        root.isDynamic ||
                        (root.attribute && root.attribute.isLink && linkEnabled) || inputConnectMA.drag.active || inputDropArea.containsDrag
                radius: root.isList ? 0 : 2
                anchors.fill: parent
                anchors.margins: 2
                color: {
                    if (inputConnectMA.containsMouse || inputConnectMA.drag.active || (inputDropArea.containsDrag && inputDropArea.acceptableDrop))
                        return Colors.sysPalette.highlight
                    if (hasConnectedChildren)
                        return Colors.sysPalette.mid
                    if (root.isDynamic)
                        return "transparent"
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
                    var validIncomingConnection = inputDragTarget.attribute.validateIncomingConnection(drag.source.attribute)
                    // Check if attributes are compatible to create a valid connection
                    if (root.readOnly                                            // Cannot connect on a read-only attribute
                        || drag.source.objectName != inputDragTarget.objectName  // Not an edge connector
                        || !validIncomingConnection                              // Connection is not allowed
                        || drag.source.nodeItem === inputDragTarget.nodeItem     // Connection between attributes of the same node
                        || drag.source.isList && childrenRepeater.count          // Source/target are lists but target already has children
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
                    _currentScene.addEdge(drag.source.attribute, inputDragTarget.attribute)
                }
            }

            Item {
                id: inputDragTarget
                objectName: "edgeConnector"
                readonly property string connectorType: "input"
                readonly property alias attribute: root.attribute
                readonly property alias nodeItem: root.nodeItem
                readonly property bool isOutput: Boolean(attribute.isOutput)
                readonly property alias isList: root.isList
                readonly property alias isExpandable: root.isExpandable
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
                drag.target: root.attribute.isReadOnly ? undefined : inputDragTarget
                drag.threshold: 0
                // Move the edge's tip straight to the current mouse position instead of waiting after the drag operation has started
                drag.smoothed: false
                enabled: !root.readOnly
                anchors.fill: parent
                hoverEnabled: root.visible

                // Use the same negative margins as DropArea to ease pin selection
                anchors.margins: inputDropArea.anchors.margins
                anchors.leftMargin: inputDropArea.anchors.leftMargin
                anchors.rightMargin: inputDropArea.anchors.rightMargin

                property bool dragTriggered: false  // An edge is being dragged from the input connector
                property bool isPressed: false  // The mouse has been pressed but not released yet
                property double initialX: 0.0
                property double initialY: 0.0

                onClicked: function() {
                    root.clicked()
                }

                onPressed: function(mouse) {
                    root.pressed(mouse)
                    isPressed = true
                    initialX = mouse.x
                    initialY = mouse.y
                }

                onReleased: {
                    inputDragTarget.Drag.drop()
                    isPressed = false
                    dragTriggered = false
                    _currentScene.edgeDraggingChanged(false)
                }

                onCanceled: {
                    isPressed = false
                    dragTriggered = false
                    _currentScene.edgeDraggingChanged(false)
                }

                onPositionChanged: function(mouse) {
                    // If there has been a significant move (5px along the -X or -Y axis) while the
                    // mouse is being pressed, then we can consider being in the dragging state
                    if (isPressed && (Math.abs(mouse.x - initialX) >= 5.0 || Math.abs(mouse.y - initialY) >= 5.0)) {
                        if (!dragTriggered) {
                            dragTriggered = true
                            _currentScene.edgeDraggingChanged(true)  
                        }
                        var windowCoords = inputConnectMA.mapToItem(null, mouse.x, mouse.y)  // null will map to window
                        _currentScene.edgeDragMousePosChanged(windowCoords.x, windowCoords.y)
                    }
                }  
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
    }

    // Attribute name
    Item {
        id: nameContainer
        implicitHeight: childrenRect.height
        implicitWidth: childrenRect.width
        visible: !root.compact
        Layout.fillWidth: !root.compact
        Layout.maximumWidth: root.compact ? 0 : Number.POSITIVE_INFINITY
        Layout.fillHeight: true
        Layout.alignment: Qt.AlignVCenter

        MaterialToolLabel {
            id: nameLabel

            anchors.fill: parent
            Layout.fillWidth: true
            Layout.fillHeight: true
            anchors.verticalCenter: parent.verticalCenter
            anchors.margins: 0
            labelIconRow.layoutDirection: root.attribute.isOutput ? Qt.RightToLeft : Qt.LeftToRight
            labelIconRow.spacing: 0

            enabled: !root.readOnly
            visible: true

            // Allow to trigger a change of state once the parent is ready, ensuring the correct width of the
            // elements upon their first display without waiting for a mouse interaction
            property bool parentNotReady: nameContainer.width == 0

            property bool hovered: (nameLabel.visible && parentNotReady) || (inputConnectMA.containsMouse ||
                                                      inputConnectMA.drag.active ||
                                                      inputDropArea.containsDrag ||
                                                      outputConnectMA.containsMouse ||
                                                      outputConnectMA.drag.active ||
                                                      outputDropArea.containsDrag)

            labelIconColor: {
                if ((root.attribute.hasAnyOutputLinks || root.attribute.isLink) && !root.attribute.enabled) {
                    return Colors.lightgrey
                } else if (hovered) {
                    return palette.highlight
                }
                return palette.text
            }
            labelIconMouseArea.enabled: false  // Prevent mixing mouse interactions between the label and the pin context

            // Text
            label.text: root.attribute.label
            label.font.pointSize: 7
            label.elide: hovered ? Text.ElideNone : Text.ElideMiddle
            label.horizontalAlignment: root.attribute && root.attribute.isOutput ? Text.AlignRight : Text.AlignLeft
            label.verticalAlignment: Text.AlignVCenter
            label.visible: true
            label.font.italic: root.isDynamic || (!!attribute.root && !!attribute.root.desc && !!attribute.root.desc.isCustomAttribute)

            // Icon
            iconText: {
                if (root.isExpandable) {
                    return root.expanded ? MaterialIcons.expand_more : MaterialIcons.chevron_right
                }
                return ""
            }
            iconSize: 7
            icon.horizontalAlignment: root.attribute && root.attribute.isOutput ? Text.AlignRight : Text.AlignLeft
            icon.verticalAlignment: Text.AlignVCenter

            // Handle tree view for nested attributes
            property int groupPaddingWidth: root.attribute.depth * 10
            icon.leftPadding: root.attribute.isOutput ? 0 : groupPaddingWidth
            icon.rightPadding: root.attribute.isOutput ? groupPaddingWidth : 0
        }

        MouseArea {
            anchors.fill: parent
            enabled: root.isAnySetChild
            acceptedButtons: Qt.RightButton
            onClicked: function(mouse) {
                var menu = removeAnySetAttributeMenuComp.createObject(nameContainer)
                var position = mapToItem(Overlay.overlay, mouse.x, mouse.y)
                menu.preferredX = position.x
                menu.preferredY = position.y
                menu.parent = nameContainer
                menu.popup()
            }
        }
    }

    Rectangle {
        id: outputAnchor

        visible: root.displayOutputPinForInput || root.attribute.isOutput
        width: 8
        height: width
        radius: root.isList ? 0 : width / 2

        Layout.alignment: Qt.AlignVCenter

        border.color: getCurrentAttributePinColor(innerOutputAnchor.hasConnectedChildren)
        color: Colors.sysPalette.base

        Rectangle {
            id: innerOutputAnchor
            property bool linkEnabled: true
            property bool hasConnectedChildren: {
                if (!root.isExpandable || root.isConnected)
                    return false
                for (var i = 0; i < attribute.flatStaticChildren.length; ++i) {
                    if (attribute.flatStaticChildren[i].hasAnyOutputLinks) {
                        return true
                    }
                }
                return false
            }
            visible: (root.attribute.hasAnyOutputLinks && linkEnabled) || outputConnectMA.containsMouse || outputConnectMA.drag.active || outputDropArea.containsDrag || hasConnectedChildren
            radius: root.isList ? 0 : 2
            anchors.fill: parent
            anchors.margins: 2
            color: {
                if (root.attribute.enabled && (outputConnectMA.containsMouse || outputConnectMA.drag.active ||
                                               (outputDropArea.containsDrag && outputDropArea.acceptableDrop)))
                    return Colors.sysPalette.highlight
                if (hasConnectedChildren)
                    return Colors.sysPalette.mid
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
                var validIncomingConnection = outputDragTarget.attribute.validateIncomingConnection(drag.source.attribute)
                // Check if attributes are compatible to create a valid connection
                if (drag.source.objectName != outputDragTarget.objectName   // Not an edge connector
                    || !validIncomingConnection                             // Connection is not allowed
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
                _currentScene.addEdge(outputDragTarget.attribute, drag.source.attribute)
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
            readonly property alias isExpandable: root.isExpandable
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
            // Move the edge's tip straight to the current mouse position instead of waiting after the drag operation has started
            drag.smoothed: false
            anchors.fill: parent
            // Use the same negative margins as DropArea to ease pin selection
            anchors.margins: outputDropArea.anchors.margins
            anchors.leftMargin: outputDropArea.anchors.leftMargin
            anchors.rightMargin: outputDropArea.anchors.rightMargin

            hoverEnabled: root.visible

            property bool dragTriggered: false  // An edge is being dragged from the output connector
            property bool isPressed: false   // The mouse has been pressed but not released yet
            property double initialX: 0.0
            property double initialY: 0.0

            onPressed: function(mouse) {
                root.pressed(mouse)
                isPressed = true
                initialX = mouse.x
                initialY = mouse.y
            }

            onClicked: function() {
                root.clicked()
            }

            onReleased: function(mouse) {
                outputDragTarget.Drag.drop()
                isPressed = false
                dragTriggered = false
                _currentScene.edgeDraggingChanged(false)
            }

            onCanceled: {
                isPressed = false
                dragTriggered = false
                _currentScene.edgeDraggingChanged(false)
            }

            onPositionChanged: function(mouse) {
                if (isPressed && (Math.abs(mouse.x - initialX) >= 5.0 || Math.abs(mouse.y - initialY) >= 5.0)) {
                    if (!dragTriggered) {
                        dragTriggered = true
                        _currentScene.edgeDraggingChanged(true)  
                    }
                    var windowCoords = outputConnectMA.mapToItem(null, mouse.x, mouse.y)  // null will map to window
                    _currentScene.edgeDragMousePosChanged(windowCoords.x, windowCoords.y)
                }
            }
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

    state: inputConnectMA.dragTriggered ? "DraggingInput" : outputConnectMA.dragTriggered ? "DraggingOutput" : ""

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
