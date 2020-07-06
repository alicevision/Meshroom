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
    signal pickedChanged(bool picked)

    onPressed: {
        root.isPressed = true
        pickedChanged(true)
        mouseHandler.currentPosition = mouseHandler.lastPosition = pick.position
    }
    onEntered: {
        material.ambient = "white"
    }
    onExited: {
        if(!isPressed) material.ambient = baseColor
    }
    onReleased: {
        material.ambient = baseColor
        root.isPressed = false
        pickedChanged(false)
    }
}