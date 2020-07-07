import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.9
import Qt3D.Logic 2.0

ObjectPicker {
    id: root
    property bool isPressed : false
    property MouseHandler mouseController
    property var gizmoMaterial
    property color gizmoBaseColor
    property int gizmoAxis
    property int gizmoType
    
    signal pickedChanged(var picker)
    
    hoverEnabled: true

    onPressed: {
        root.isPressed = true
        pickedChanged(this)
        mouseController.currentPosition = mouseController.lastPosition = pick.position
    }
    onEntered: {
        gizmoMaterial.ambient = "white"
    }
    onExited: {
        if(!isPressed) gizmoMaterial.ambient = gizmoBaseColor
    }
    onReleased: {
        gizmoMaterial.ambient = gizmoBaseColor
        root.isPressed = false
        pickedChanged(this)
    }
}