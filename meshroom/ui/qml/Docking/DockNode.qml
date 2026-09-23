import QtQuick
import QtQuick.Controls

import Controls 1.0

/**
 * DockNode displays a node of the dock layout: a DockGroup for a "tabs" node, or the children of a
 * "split" node side by side in a SplitView, each of them being displayed by a nested DockNode.
 *
 * A node is hidden, and ignored by the SplitView it belongs to, when all its panels are closed.
 */

Item {
    id: root

    /// Node of the dock layout
    property var node
    property DockManager manager
    /// The DockArea displaying the node
    property Item area

    visible: manager.hasOpenPanel(node)

    Loader {
        anchors.fill: parent
        sourceComponent: root.node.type === "split" ? splitComponent : groupComponent
    }

    Component {
        id: groupComponent
        DockGroup {
            node: root.node
            manager: root.manager
            area: root.area
        }
    }

    Component {
        id: splitComponent
        MSplitView {
            id: split

            readonly property bool horizontal: orientation === Qt.Horizontal
            /// Size of each child as a fraction of the space, including the hidden ones
            property var fractions: root.node.sizes
            /// Whether each child is displayed
            readonly property var displayed: root.node.children.map(function(child) { return root.manager.hasOpenPanel(child) })
            readonly property real displayedFraction: fractions.reduce(function(sum, f, i) { return displayed[i] ? sum + f : sum }, 0)
            /// The last displayed child takes the remaining space
            readonly property int fillIndex: displayed.lastIndexOf(true)
            readonly property int handleSize: 5
            readonly property real available: (horizontal ? width : height) - Math.max(0, displayed.filter(Boolean).length - 1) * handleSize

            orientation: root.node.orientation === "vertical" ? Qt.Vertical : Qt.Horizontal

            onResizingChanged: {
                if (resizing)
                    return
                // Store the sizes set by the user. The fractions have to be updated as well, otherwise
                // the sizes would be reset the next time the preferred sizes are evaluated.
                var sizes = []
                for (var i = 0; i < childRepeater.count; ++i) {
                    var item = childRepeater.itemAt(i)
                    sizes.push(item && item.visible ? (horizontal ? item.width : item.height) : -1)
                }
                var newFractions = root.manager.layoutModel.setSizes(root.node.id, sizes)
                if (newFractions.length === fractions.length)
                    fractions = newFractions
            }

            Repeater {
                id: childRepeater
                model: root.node.children.length

                delegate: Loader {
                    id: childLoader
                    visible: split.displayed[index]

                    SplitView.fillWidth: split.horizontal && index === split.fillIndex
                    SplitView.fillHeight: !split.horizontal && index === split.fillIndex
                    SplitView.preferredWidth: split.horizontal ? split.fractions[index] / split.displayedFraction * split.available : -1
                    SplitView.preferredHeight: split.horizontal ? -1 : split.fractions[index] / split.displayedFraction * split.available
                    SplitView.minimumWidth: split.horizontal ? 80 : 0
                    SplitView.minimumHeight: split.horizontal ? 0 : 80

                    // A component cannot instantiate itself by type name: load the nested node by url
                    Component.onCompleted: setSource(Qt.resolvedUrl("DockNode.qml"), {
                        "node": root.node.children[index],
                        "manager": root.manager,
                        "area": root.area
                    })
                }
            }
        }
    }
}
