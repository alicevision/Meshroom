import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

import MaterialIcons 2.2
import Utils 1.0

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
    readonly property color defaultColor: isCompatibilityNode ? "#444" : !node.isComputable ? "#BA3D69" : activePalette.base
    property color baseColor: defaultColor

    property point mousePosition: Qt.point(mouseArea.mouseX, mouseArea.mouseY)

    Item {
        id: m
        property bool displayParams: false
    }

    // Mouse interaction related signals
    signal pressed(var mouse)
    signal released(var mouse)
    signal clicked(var mouse)
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
        function onPositionChanged() {
            root.x = root.node.x
            root.y = root.node.y
        }
    }

    function formatInternalAttributesTooltip(invalidation, comment) {
        /*
         * Creates a string that contains the invalidation message (if it is not empty) in bold,
         * followed by the comment message (if it exists) in regular font, separated by an empty
         * line.
         * Invalidation and comment messages have their tabs or line returns in plain text format replaced
         * by their HTML equivalents.
         */
        let str = ""
        if (invalidation !== "") {
            let replacedInvalidation = node.invalidation.replace(/\n/g, "<br/>").replace(/\t/g, "&nbsp;&nbsp;&nbsp;&nbsp;")
            str += "<b>" + replacedInvalidation + "</b>"
        }
        if (invalidation !== "" && comment !== "") {
            str += "<br/><br/>"
        }
        if (comment !== "") {
            let replacedComment = node.comment.replace(/\n/g, "<br/>").replace(/\t/g, "&nbsp;&nbsp;&nbsp;&nbsp;")
            str += replacedComment
        }
        return str
    }

    // Used to generate list of node's label sharing the same uid
    function generateDuplicateList() {
        let str = "<b>Shares internal folder (data) with:</b>"
        for (let i = 0; i < node.duplicates.count; ++i) {
            if (i % 5 === 0)
                str += "<br>"

            const currentNode = node.duplicates.at(i)

            if (i === node.duplicates.count - 1) {
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
        // Small drag threshold to avoid moving the node by mistake
        drag.threshold: 2
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: (mouse) => root.pressed(mouse)
        onReleased: (mouse) => root.released(mouse)
        onClicked: (mouse) => root.clicked(mouse)
        onDoubleClicked: (mouse) => root.doubleClicked(mouse)
        onEntered: root.entered()
        onExited: root.exited()
        drag.onActiveChanged: {
            if (!drag.active) {
                root.moved(Qt.point(root.x, root.y))
            }
        }

        cursorShape: drag.active ? Qt.ClosedHandCursor : Qt.ArrowCursor

        // Selection border
        Rectangle {
            anchors.fill: nodeContent
            anchors.margins: -border.width
            visible: root.mainSelected || root.hovered || root.selected
            border.width: {
                if(root.mainSelected)
                    return 3
                if(root.selected)
                    return 2.5
                return 2
            }
            border.color: {
                if(root.mainSelected)
                    return activePalette.highlight
                if(root.selected)
                    return Qt.darker(activePalette.highlight, 1.2)
                return Qt.lighter(activePalette.base, 3)
            }
            opacity: 0.9
            radius: background.radius + border.width
            color: "transparent"
        }

        Rectangle {
            id: background
            anchors.fill: nodeContent
            color: node.color === "" ? Qt.lighter(activePalette.base, 1.4) : node.color
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
                    color: root.baseColor
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
                            id: nodeLabel
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

                                onPressed: {
                                    offsetReleased.running = false
                                    toolTipText = visible ? generateDuplicateList() : ""
                                }
                                onReleased: {
                                    toolTipText = ""
                                    offsetReleased.running = true
                                }
                                onCanceled: released()

                                // Used for a better user experience with the button
                                // Avoid to change the text too quickly
                                Timer {
                                    id: offsetReleased
                                    interval: 750
                                    running: false
                                    repeat: false
                                    onTriggered: parent.toolTipText = visible ? parent.baseText : ""
                                }
                            }

                            // Submitted externally indicator
                            MaterialLabel {
                                visible: ["SUBMITTED", "RUNNING"].includes(node.globalStatus) && node.chunks.count > 0 && node.isExternal
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

                            MaterialLabel {
                                id: nodeComment
                                visible: node.comment !== "" || node.invalidation !== ""
                                text: MaterialIcons.comment
                                padding: 2
                                font.pointSize: 7

                                ToolTip {
                                    id: nodeCommentTooltip
                                    parent: header
                                    visible: nodeCommentMA.containsMouse && nodeComment.visible
                                    text: formatInternalAttributesTooltip(node.invalidation, node.comment)
                                    implicitWidth: 400 // Forces word-wrap for long comments but the tooltip will be bigger than needed for short comments
                                    delay: 300

                                    // Relative position for the tooltip to ensure we won't get stuck in a case where it starts appearing over the mouse's
                                    // position because it's a bit long and cutting off the hovering of the mouse area (which leads to the tooltip beginning
                                    // to appear and immediately disappearing, over and over again)
                                    x: implicitWidth / 2.5
                                }

                                MouseArea {
                                    // If the node header is hovered, comments may be displayed
                                    id: nodeCommentMA
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }
                            }

                            MaterialLabel {
                                id: nodeImageOutput
                                visible: (node.hasImageOutput || node.has3DOutput || node.hasSequenceOutput)
                                text: MaterialIcons.visibility
                                padding: 2
                                font.pointSize: 7
                                property bool displayable: ((["SUCCESS"].includes(node.globalStatus) && node.chunks.count > 0) || !node.isComputable)
                                color: displayable ? palette.text : Qt.darker(palette.text, 1.8)

                                ToolTip {
                                    id: nodeImageOutputTooltip
                                    parent: header
                                    visible: nodeImageOutputMA.containsMouse && nodeImageOutput.visible
                                    text: {
                                        if ((node.hasImageOutput || node.hasSequenceOutput) && !node.has3DOutput)
                                            return nodeImageOutput.displayable ? "Double-click on this node to load its outputs in the Image Viewer." : "This node has image outputs."
                                        else if (node.has3DOutput && !node.hasImageOutput && !node.hasSequenceOutput)
                                            return nodeImageOutput.displayable ? "Double-click on this node to load its outputs in the 3D Viewer." : "This node has 3D outputs."
                                        else  // Handle case where a node might have both 2D and 3D outputs
                                            return nodeImageOutput.displayable ? "Double-click on this node to load its outputs in the Image or 3D Viewer." : "This node has image and 3D outputs."
                                    }
                                    implicitWidth: 500
                                    delay: 300

                                    // Relative position for the tooltip to ensure we won't get stuck in a case where it starts appearing over the mouse's
                                    // position because it's a bit long and cutting off the hovering of the mouse area (which leads to the tooltip beginning
                                    // to appear and immediately disappearing, over and over again)
                                    x: implicitWidth / 2.5
                                }

                                MouseArea {
                                    // If the node header is hovered, comments may be displayed
                                    id: nodeImageOutputMA
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }
                            }
                        }
                    }
                }

                // Node Chunks
               NodeChunks {
                   visible: node.isComputable
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
                                    active: Boolean(object.isOutput && object.desc.visible)
                                    visible: Boolean(object.enabled || object.hasOutputConnections)
                                    anchors.right: parent.right
                                    width: outputs.width

                                    sourceComponent: AttributePin {
                                        id: outPin
                                        nodeItem: root
                                        attribute: object

                                        property real globalX: root.x + nodeAttributes.x + outputs.x + outputLoader.x + outPin.x
                                        property real globalY: root.y + nodeAttributes.y + outputs.y + outputLoader.y + outPin.y

                                        onPressed: function(mouse) { root.pressed(mouse) }
                                        onEdgeAboutToBeRemoved: function(input) { root.edgeAboutToBeRemoved(input) }

                                        Component.onCompleted: attributePinCreated(attribute, outPin)
                                        onChildPinCreated: attributePinCreated(childAttribute, outPin)
                                        Component.onDestruction: attributePinDeleted(attribute, outPin)
                                        onChildPinDeleted: attributePinDeleted(childAttribute, outPin)
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
                                    active: !object.isOutput && object.desc.exposed && object.desc.visible
                                    visible: Boolean(object.enabled)
                                    width: inputs.width

                                    sourceComponent: AttributePin {
                                        id: inPin
                                        nodeItem: root
                                        attribute: object

                                        property real globalX: root.x + nodeAttributes.x + inputs.x + inputLoader.x + inPin.x
                                        property real globalY: root.y + nodeAttributes.y + inputs.y + inputLoader.y + inPin.y

                                        readOnly: Boolean(root.readOnly || object.isReadOnly)
                                        Component.onCompleted: attributePinCreated(attribute, inPin)
                                        Component.onDestruction: attributePinDeleted(attribute, inPin)
                                        onPressed: function(mouse) { root.pressed(mouse) }
                                        onEdgeAboutToBeRemoved: function(input) { root.edgeAboutToBeRemoved(input) }
                                        onChildPinCreated: function(childAttribute, inPin) { attributePinCreated(childAttribute, inPin) }
                                        onChildPinDeleted: function(childAttribute, inPin) { attributePinDeleted(childAttribute, inPin) }
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
                                        active: !object.isOutput && !object.desc.exposed && object.desc.visible
                                        visible: Boolean(object.enabled || object.isLinkNested || object.hasOutputConnections)
                                        property bool isFullyActive: Boolean(m.displayParams || object.isLinkNested || object.hasOutputConnections)
                                        width: parent.width

                                        sourceComponent: AttributePin {
                                            id: inParamsPin
                                            nodeItem: root
                                            property real globalX: root.x + nodeAttributes.x + inputParamsRect.x + paramLoader.x + inParamsPin.x
                                            property real globalY: root.y + nodeAttributes.y + inputParamsRect.y + paramLoader.y + inParamsPin.y

                                            height: isFullyActive ? childrenRect.height : 0
                                            Behavior on height { PropertyAnimation {easing.type: Easing.Linear} }
                                            visible: (height == childrenRect.height)
                                            attribute: object
                                            readOnly: Boolean(root.readOnly || object.isReadOnly)
                                            Component.onCompleted: attributePinCreated(attribute, inParamsPin)
                                            Component.onDestruction: attributePinDeleted(attribute, inParamsPin)
                                            onPressed: function(mouse) { root.pressed(mouse) }
                                            onEdgeAboutToBeRemoved: function(input) { root.edgeAboutToBeRemoved(input) }
                                            onChildPinCreated: function(childAttribute, inParamsPin) { attributePinCreated(childAttribute, inParamsPin) }
                                            onChildPinDeleted: function(childAttribute, inParamsPin) { attributePinDeleted(childAttribute, inParamsPin) }
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
