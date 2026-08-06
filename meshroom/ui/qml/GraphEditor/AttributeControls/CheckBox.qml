import QtQuick
import QtQuick.Controls

Row {
    id: root
    required property var attribute
    property bool editable
    CheckBox {
        enabled: root.editable
        checked: attribute.keyable ? attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId) : attribute.value
        onToggled: {
            if(attribute.keyable)
            {
                const value = attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId)
                _currentScene.addAttributeKeyValue(attribute, _currentScene.selectedViewId, !value)
            }
            else
            {
                _currentScene.setAttribute(attribute, !attribute.value)
            }
        }
    }
}