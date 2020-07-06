import Qt3D.Core 2.0
import Qt3D.Render 2.9
import Qt3D.Input 2.0
import Qt3D.Extras 2.10
import QtQuick 2.9
import Qt3D.Logic 2.0

ObjectPicker {
    id: root
    hoverEnabled: true
    property bool isPressed : false
    property MouseHandler mouseController
    property var objectMaterial
    property color objectBaseColor
    
    signal pickedChanged(bool picked)

    onPressed: {
        root.isPressed = true
        pickedChanged(true)
        mouseController.currentPosition = mouseController.lastPosition = pick.position
    }
    onEntered: {
        objectMaterial.ambient = "white"
    }
    onExited: {
        if(!isPressed) objectMaterial.ambient = objectBaseColor
    }
    onReleased: {
        objectMaterial.ambient = objectBaseColor
        root.isPressed = false
        pickedChanged(false)
    }
}