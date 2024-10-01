import Qt3D.Core 2.6
import Qt3D.Render 2.6
import Qt3D.Input 2.6
import Qt3D.Extras 2.15
import Qt3D.Logic 2.6
import QtQuick

ObjectPicker {
    id: root
    property bool isPressed : false
    property MouseHandler mouseController
    property var gizmoMaterial
    property color gizmoBaseColor
    property int gizmoAxis
    property int gizmoType
    property point screenPoint
    property var modelMatrix
    property real scaleUnit
    property int button
    
    signal pickedChanged(var picker)
    
    hoverEnabled: true

    onPressed: {
        mouseController.enabled = true
        mouseController.objectPicker = this
        root.isPressed = true
        screenPoint = pick.position
        button = pick.button
        pickedChanged(this)
    }
    onEntered: {
        gizmoMaterial.ambient = "white"
    }
    onExited: {
        if (!isPressed)
            gizmoMaterial.ambient = gizmoBaseColor
    }
    onReleased: {
        gizmoMaterial.ambient = gizmoBaseColor
        root.isPressed = false
        mouseController.objectPicker = null
        mouseController.enabled = false
        pickedChanged(this)
    }
}
