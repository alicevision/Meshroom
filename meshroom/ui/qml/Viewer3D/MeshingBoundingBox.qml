import QtQuick

import meshViewer

/**
 * Binds the "boundingBox" attribute of a Meshing @p node to a BoxControlLayer @p layer.
 *
 * Node values (computer vision convention) are converted to the viewer convention and applied to the layer,
 * except while @p editing (the layer is then driven by the gizmo). commit() writes the layer values back to the node.
 * The layer is visible when the node uses its bounding box and @p userVisible is set.
 */
QtObject {
    id: root

    property var node: null
    property BoxControlLayer layer: null
    /** True while the layer is being edited; node values are not applied meanwhile. */
    property bool editing: false
    property bool userVisible: true

    function attributeValue(name, defaultValue)
    {
        return node ? node.attribute("boundingBox." + name).value : defaultValue
    }

    // Translation: y and z axes are flipped between computer vision and viewer conventions
    readonly property vector3d nodeTranslation: Qt.vector3d(
        attributeValue("bboxTranslation.x", 0),
        -attributeValue("bboxTranslation.y", 0),
        -attributeValue("bboxTranslation.z", 0)
    )

    readonly property vector3d nodeRotation: Transformations3DHelper.convertRotationFromCV2GL(Qt.vector3d(
        attributeValue("bboxRotation.x", 0),
        attributeValue("bboxRotation.y", 0),
        attributeValue("bboxRotation.z", 0)
    ))

    readonly property vector3d nodeScale: Qt.vector3d(
        attributeValue("bboxScale.x", 1),
        attributeValue("bboxScale.y", 1),
        attributeValue("bboxScale.z", 1)
    )

    readonly property bool nodeUsesBoundingBox: node !== null && node.attribute("useBoundingBox").value

    /**
     * Write the layer transform back to the node, as a single undoable command.
     * @p type is "translation", "rotation", "scale" or "all" (see BoxControlMouseArea.editFinished).
     */
    function commit(type)
    {
        if (!node || !layer)
        {
            return
        }

        const t = layer.translation
        const s = layer.scale
        // The conversion between conventions is its own inverse
        const r = Transformations3DHelper.convertRotationFromCV2GL(layer.rotation)
        const translation = [t.x, -t.y, -t.z]
        const rotation = [r.x, r.y, r.z]
        const scale = [s.x, s.y, s.z]

        switch (type)
        {
            case "translation":
                _currentScene.setAttribute(node.attribute("boundingBox.bboxTranslation"), JSON.stringify(translation))
                break
            case "rotation":
                _currentScene.setAttribute(node.attribute("boundingBox.bboxRotation"), JSON.stringify(rotation))
                break
            case "scale":
                _currentScene.setAttribute(node.attribute("boundingBox.bboxScale"), JSON.stringify(scale))
                break
            default:
                _currentScene.setAttribute(node.attribute("boundingBox"), JSON.stringify([translation, rotation, scale]))
                break
        }
    }

    // RestoreNone: keep the edited values when a binding is released, instead of restoring older ones
    readonly property Binding translationBinding: Binding {
        target: root.layer
        property: "translation"
        value: root.nodeTranslation
        when: root.layer !== null && !root.editing
        restoreMode: Binding.RestoreNone
    }

    readonly property Binding rotationBinding: Binding {
        target: root.layer
        property: "rotation"
        value: root.nodeRotation
        when: root.layer !== null && !root.editing
        restoreMode: Binding.RestoreNone
    }

    readonly property Binding scaleBinding: Binding {
        target: root.layer
        property: "scale"
        value: root.nodeScale
        when: root.layer !== null && !root.editing
        restoreMode: Binding.RestoreNone
    }

    readonly property Binding visibleBinding: Binding {
        target: root.layer
        property: "visible"
        value: root.nodeUsesBoundingBox && root.userVisible
        when: root.layer !== null
    }
}
