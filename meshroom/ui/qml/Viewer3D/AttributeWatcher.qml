import QtQml

/**
 * Watches the attribute a LayerList entry was loaded from:
 * - @p ready tells whether the displayed file is available (the attribute's node is alive and computed);
 * - attributeValueChanged() is emitted when the attribute value no longer matches @p source;
 * - nodeRemoved() is emitted when the attribute's node is removed from the graph.
 * Used by LayerList; not intended for direct use.
 */
QtObject {
    id: root

    required property var attribute
    /** The last attribute value handled by LayerList (initially the file given to LayerList.add()). */
    required property string source

    /** Set by LayerList while the attribute has no file to display in the entry: its ready state is not updated. */
    property bool detached: false
    /** Incremented by LayerList on each attribute value change, to discard outdated deferred updates. */
    property int generation: 0

    /** Whether the attribute's node is alive and computed, i.e. whether the file can be loaded. */
    readonly property bool ready: Boolean(attribute && attribute.node && attribute.node.alive && attribute.node.isComputed)

    signal attributeValueChanged(string newValue)
    signal nodeRemoved()

    readonly property Connections attributeConnections: Connections {
        target: root.attribute

        function onValueChanged()
        {
            // A reset dynamic output is None (undefined in QML): treat it as no file
            const value = String(root.attribute.value ?? "")
            if (value !== root.source)
            {
                root.attributeValueChanged(value)
            }
        }
    }

    readonly property Connections nodeConnections: Connections {
        target: root.attribute ? root.attribute.node : null

        function onAliveChanged()
        {
            if (!root.attribute.node.alive)
            {
                root.nodeRemoved()
            }
        }
    }
}
