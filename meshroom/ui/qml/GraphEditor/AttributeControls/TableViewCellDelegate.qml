import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import MaterialIcons 2.2
import Utils 1.0

Rectangle {
    id: cellRect
    property int cellIndex: 0
    property var rowObject: null
    property int rowIndex: 0
    property real cellWidth:  100
    property real cellHeight: 24
    property bool editable: true
    width : cellWidth
    height : cellHeight
    property var appPalette: palette
    color : palette.window
    border.color : cellFocused ? palette.highlight : palette.mid
    clip : true
    property var cell: rowObject.value.at(cellIndex)
    property bool cellFocused: {
        var item = cellLoader.item
        if (!item)
            return false
        return item.activeFocus ||
               (item.children && item.children.length > 0 &&
                item.children[0] && item.children[0].activeFocus)
    }
    Rectangle {
        anchors.centerIn: parent
        width: cellLoader.width + 8
        height: cellLoader.height + 4
        radius: 3
        color: palette.base
        visible: cellRect.cell &&
                 (cellRect.cell.type === "BoolParam" ||
                  cellRect.cell.type === "ChoiceParam")
    }
    Loader {
        id: cellLoader
        anchors.centerIn: parent
        width: parent.width
        height: parent.height
        property var attribute: cellRect.cell
        sourceComponent: {
            if (!attribute)
                return null
            switch (attribute.type) {
                case "PushButtonParam": return cellPushButtonComponent
                case "ChoiceParam":
                    return (attribute.desc && attribute.desc.exclusive)
                           ? cellChoiceComponent
                           : cellChoiceMultiComponent
                case "IntParam": return cellSliderComponent
                case "FloatParam":
                    return (attribute.desc && attribute.desc.semantic === "color/hue")
                           ? cellColorHueComponent
                           : cellSliderComponent
                case "BoolParam": return cellCheckboxComponent
                case "StringParam":
                    return (attribute.desc && attribute.desc.semantic &&
                            attribute.desc.semantic.includes("multiline"))
                           ? cellTextAreaComponent
                           : cellTextFieldComponent
                case "ColorParam": return cellColorComponent
                default: return cellTextFieldComponent
            }
        }
        Component {
            id: cellChoiceComponent
            Choice {
                value: cellLoader.attribute
                       ? cellLoader.attribute.value 
                       : ""
                values: cellLoader.attribute
                        ? cellLoader.attribute.values
                        : []
                enabled: cellRect.editable
                Component.onCompleted: {
                    if (typeof popup !== "undefined" && popup !== null) {
                        popup.margins = -1
                    }
                }
                onEditingFinished: function(value) {
                    if (cellLoader.attribute)
                        _currentScene.setAttribute(cellLoader.attribute, value)
                }
            }
        }
        Component {
            id: cellChoiceMultiComponent
            ChoiceMulti {
                value: cellLoader.attribute
                       ? cellLoader.attribute.value
                       : []
                values: cellLoader.attribute
                        ? cellLoader.attribute.values
                        : []
                enabled: cellRect.editable
                customValueColor: Colors.orange
                onToggled: function(value, checked) {
                    if (!cellLoader.attribute)
                        return
                    var cur = cellLoader.attribute.value.slice()
                    if (!checked) {
                        var idx = cur.indexOf(value)
                        if (idx !== -1) cur.splice(idx, 1)
                    } else {
                        cur.push(value)
                    }
                    _currentScene.setAttribute(cellLoader.attribute, cur)
                }
            }
        }
        Component {
            id: cellSliderComponent
            RowLayout {
                spacing: 2
                TextField {
                    id: cellNumField
                    Layout.fillWidth: !cellSliderLoader.active
                    implicitWidth: 70
                    enabled: cellRect.editable
                    selectByMouse: true
                    horizontalAlignment: TextInput.AlignRight
                    text: {
                        if (cellSliderLoader.active && cellSliderLoader.item &&
                                cellSliderLoader.item.pressed)
                            return String(cellSliderLoader.item.formattedValue)
                        return cellLoader.attribute
                               ? String(cellLoader.attribute.value)
                               : ""
                    }
                    background: Rectangle { color: Qt.darker(palette.window, 1.2); radius: 2 }
                    color: palette.text
                    onEditingFinished: {
                        if (cellLoader.attribute)
                            _currentScene.setAttribute(cellLoader.attribute,
                                cellLoader.attribute.type === "IntParam"
                                    ? parseInt(text)
                                    : parseFloat(text))
                    }
                    WheelHandler {
                        onWheel: function(event) {
                            if (!cellRect.editable || !cellLoader.attribute)
                                return
                            var step = 1
                            if (cellLoader.attribute.desc &&
                                    cellLoader.attribute.desc.range &&
                                    cellLoader.attribute.desc.range.length === 3)
                                step = cellLoader.attribute.desc.range[2]
                            var dir = event.angleDelta.y > 0
                                ? 1
                                : -1
                            var v = Number(cellLoader.attribute.value) + dir * step
                            if (cellLoader.attribute.desc && cellLoader.attribute.desc.range) {
                                v = Math.max(cellLoader.attribute.desc.range[0],
                                    Math.min(cellLoader.attribute.desc.range[1], v))
                            }
                            _currentScene.setAttribute(cellLoader.attribute,
                                cellLoader.attribute.type === "IntParam"
                                    ? Math.round(v)
                                    : v)
                            event.accepted = true
                        }
                    }
                }
                Loader {
                    id: cellSliderLoader
                    Layout.fillWidth: true
                    active: cellLoader.attribute &&
                            cellLoader.attribute.desc &&
                            cellLoader.attribute.desc.range &&
                            cellLoader.attribute.desc.range.length === 3
                    sourceComponent: Slider {
                        readonly property int stepDecimalCount: stepSize < 1
                            ? String(stepSize).split(".").pop().length
                            : 0
                        readonly property real formattedValue: value.toFixed(stepDecimalCount)
                        enabled: cellRect.editable
                        value: cellLoader.attribute
                               ? cellLoader.attribute.value
                               : 0
                        from: cellLoader.attribute.desc.range[0]
                        to: cellLoader.attribute.desc.range[1]
                        stepSize: cellLoader.attribute.desc.range[2]
                        snapMode: Slider.SnapAlways
                        onPressedChanged: {
                            if (!pressed && cellLoader.attribute)
                                _currentScene.setAttribute(cellLoader.attribute,
                                    formattedValue)
                        }
                    }
                }
            }
        }
        Component {
            id: cellCheckboxComponent
            CheckBox {
                enabled: cellRect.editable
                checked: cellLoader.attribute
                         ? cellLoader.attribute.value
                         : false
                onToggled: {
                    if (cellLoader.attribute)
                        _currentScene.setAttribute(
                            cellLoader.attribute, checked)
                }
                background: Rectangle { color:palette.window; radius: 2 }
            }
        }
        Component {
            id: cellTextFieldComponent
            TextField {
                enabled: cellRect.editable
                text: cellLoader.attribute
                      ? String(cellLoader.attribute.value)
                      : ""
                placeholderText: cellLoader.attribute.isMandatory ? "This field is required" : ""
                placeholderTextColor: "gray"
                selectByMouse: true
                background: Rectangle {
                    color: Qt.darker(palette.window, 1.2)
                    radius: 2
                }
                color: palette.text
                onEditingFinished: {
                    if (cellLoader.attribute)
                        _currentScene.setAttribute(
                            cellLoader.attribute, text.trim())
                }
            }
        }
        Component {
            id: cellTextAreaComponent
            TextField {
                enabled: cellRect.editable
                text: cellLoader.attribute
                      ? String(cellLoader.attribute.value)
                      : ""
                selectByMouse: true
                background: Rectangle {
                    color: palette.base
                    radius: 2
                }
                color: palette.text
                onEditingFinished: {
                    if (cellLoader.attribute)
                        _currentScene.setAttribute(
                            cellLoader.attribute, text.trim())
                }
            }
        }
        Component {
            id: cellColorComponent
            TextField {
                enabled: cellRect.editable
                text: cellLoader.attribute
                      ? String(cellLoader.attribute.value)
                      : ""
                selectByMouse: true
                background: Rectangle {
                    color: Qt.darker(palette.window, 1.2)
                    radius: 2
                }
                color: palette.text
                onEditingFinished: {
                    if (cellLoader.attribute)
                        _currentScene.setAttribute(
                            cellLoader.attribute, text)
                }
            }
        }
        Component {
            id: cellPushButtonComponent
            Button {
                text: cellLoader.attribute
                      ? cellLoader.attribute.label
                      : ""
                enabled: cellRect.editable
                onClicked: {
                    if (cellLoader.attribute)
                        cellLoader.attribute.clicked()
                }
            }
        }
        Component {
            id: cellColorHueComponent
            RowLayout {
                Slider {
                    id: cellHueSlider
                    Layout.fillWidth: true
                    enabled: cellRect.editable
                    value: cellLoader.attribute
                           ? cellLoader.attribute.value
                           : 0
                    from: 0
                    to: 1
                    stepSize: 0.01
                    snapMode: Slider.SnapAlways
                    onPressedChanged: {
                        if (!pressed && cellLoader.attribute)
                            _currentScene.setAttribute(
                                cellLoader.attribute,
                                value.toFixed(2))
                    }
                }
                Rectangle {
                    width: 16
                    height: 16
                    color: Qt.hsla(cellHueSlider.value, 1, 0.5, 1)
                }
            }
        }
    }
}
