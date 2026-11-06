import QtQuick
import QtQuick.Controls

import "." as AttributeControls

/**
 * ListAttributeTableWindow displays a ListAttribute of GroupAttributes as a table in a separate window.
 * It must be owned by an item that outlives the attribute editor's delegates, which can be destroyed at
 * any time (scrolling, filtering, attribute hidden after an edit...).
 * The window hides itself once its attribute or its node is removed: its owner is then expected to destroy it.
 */

Window {
    id: root

    required property var attribute
    readonly property var node: attribute ? attribute.node : null
    readonly property bool valid: !!node && node.alive
    // Same rules as the attribute editor, which can't be relied on as the window outlives its delegates
    readonly property bool editable: valid && !attribute.isOutput && !isLinked(attribute) && !node.locked &&
                                     node.compatibilityIssue === undefined

    // Whether the attribute or one of its parents is linked, the children of linked attributes being read-only
    function isLinked(attr) {
        for (let current = attr; current; current = current.root) {
            if (current.isLink)
                return true
        }
        return false
    }

    title: valid ? node.label + " - " + attribute.label : ""
    width: 800
    height: 400
    visible: true
    color: palette.window

    onValidChanged: {
        if (!valid)
            visible = false
    }

    Loader {
        anchors.fill: parent
        anchors.margins: 4
        active: root.valid
        sourceComponent: AttributeControls.ListAttributeTable {
            attribute: root.attribute
            editable: root.editable
        }
    }
}
