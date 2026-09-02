import QtQuick

QtObject {
    function setTextFieldAttribute(attribute, value, editable, currentScene, selectedViewId) {
        if (!editable)
            return
        switch (attribute.type) {
            case "IntParam":
            case "FloatParam":
                if (attribute.keyable)
                    currentScene.addAttributeKeyValue(attribute, selectedViewId, Number(value))
                else
                    currentScene.setAttribute(attribute, Number(value))
                break
            case "File":
                currentScene.setAttribute(attribute, value)
                break
            default:
                currentScene.setAttribute(attribute, value.trim())
                break
        }
    }
}