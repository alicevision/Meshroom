import QtQml

/**
 * Watches the attribute a LayerList entry was loaded from, and emits invalidated() when the
 * displayed file no longer matches it: the attribute value changed, its node is no longer
 * computed (e.g. recomputed or invalidated by an upstream change), or its node was removed.
 * Used by LayerList; not intended for direct use.
 */
QtObject {
    id: root

    required property var attribute
    /** The file displayed by the entry, as given to LayerList.add(). */
    required property string source

    signal invalidated()

    readonly property Connections attributeConnections: Connections {
        target: root.attribute

        function onValueChanged()
        {
            if (String(root.attribute.value) !== root.source)
            {
                root.invalidated()
            }
        }
    }

    readonly property Connections nodeConnections: Connections {
        target: root.attribute ? root.attribute.node : null

        function onGlobalStatusChanged()
        {
            if (!root.attribute.node.isComputed)
            {
                root.invalidated()
            }
        }

        function onAliveChanged()
        {
            if (!root.attribute.node.alive)
            {
                root.invalidated()
            }
        }
    }
}
