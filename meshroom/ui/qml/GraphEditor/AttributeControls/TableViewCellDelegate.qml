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
    property real cellWidth: 100
    property real cellHeight: 24
    property bool editable: true
    property bool cellReady: false
    property real minCellWidth: 60
    signal loaderReady()
    width: cellWidth
    height: cellHeight
    color: palette.window
    border.color: palette.mid
    clip: true
    property var cell: rowObject
                       ? rowObject.value.at(cellIndex)
                       : null
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
        anchors.fill: parent
        property var attribute: cellRect.cell
        onStatusChanged: {
            if (status !== Loader.Ready)
                return
            cellRect.minCellWidth = (item && item.minWidth !== undefined)
                                    ? item.minWidth
                                    : 60
            cellRect.cellReady = true
            cellRect.loaderReady()
        }
        sourceComponent: {
            if (!attribute)
                return null
            switch (attribute.type) {
                case "PushButtonParam":
                    return cellPushButtonComponent
                case "ChoiceParam":
                    return (attribute.desc && attribute.desc.exclusive)
                           ? cellChoiceComponent
                           : cellChoiceMultiComponent
                case "IntParam":
                    return cellSliderComponent
                case "FloatParam":
                    return (attribute.desc &&
                            attribute.desc.semantic === "color/hue")
                           ? cellColorHueComponent :
                           cellSliderComponent
                case "BoolParam":
                    return cellCheckboxComponent
                case "StringParam":
                    return (attribute.desc && attribute.desc.semantic &&
                            attribute.desc.semantic.includes("multiline"))
                           ? cellTextAreaComponent :
                           cellTextFieldComponent
                case "ColorParam":
                    return cellColorComponent
                default:
                    return cellTextFieldComponent
            }
        }
        Component {
            id: cellChoiceComponent
            Item {
                property real minWidth: 80
                Choice {
                    id: innerChoice
                    anchors.fill: parent
                    value: cellLoader.attribute
                           ? cellLoader.attribute.value
                           : ""
                    values: cellLoader.attribute
                            ? cellLoader.attribute.values
                            : []
                    enabled: cellRect.editable
                    Component.onCompleted: {
                        if (typeof popup !== "undefined" && popup !== null)
                            popup.margins = -1
                    }
                    onEditingFinished: function(v) {
                        if (!cellLoader.attribute)
                            return
                        _currentScene.setAttribute(cellLoader.attribute, v)
                    }
                }
                Rectangle {
                    anchors.fill: innerChoice
                    color: "transparent"
                    radius: 3
                    z: 10
                    enabled: false
                    border.width: innerChoice.activeFocus
                                  ? 1
                                  : 0
                    border.color: palette.highlight
                }
            }
        }
        Component {
            id: cellChoiceMultiComponent
            Item {
                property real minWidth: 80
                ChoiceMulti {
                    id: innerChoiceMulti
                    anchors.fill: parent
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
                            if (idx !== -1)
                                cur.splice(idx, 1)
                        } else {
                            cur.push(value)
                        }
                        _currentScene.setAttribute(cellLoader.attribute, cur)
                    }
                }
                Rectangle {
                    anchors.fill: innerChoiceMulti
                    color: "transparent"
                    radius: 3
                    z: 10
                    enabled: false
                    border.width: innerChoiceMulti.activeFocus
                                  ? 1
                                  : 0
                    border.color: palette.highlight
                }
            }
        }
        Component {
            id: cellSliderComponent
            FocusScope {
                id: sliderScope
                property real minWidth: cellNumField.implicitWidth
                readonly property int decimals: {
                    if (!cellLoader.attribute)
                        return 0
                    if (cellLoader.attribute.type === "IntParam")
                        return 0
                    var step = (cellLoader.attribute.desc &&
                                cellLoader.attribute.desc.range &&
                                cellLoader.attribute.desc.range.length === 3)
                               ? cellLoader.attribute.desc.range[2]
                               : 0.01
                    if (step <= 0 || step >= 1)
                        return 2
                    return String(step).split(".").pop().length
                }
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    radius: 3
                    z: 10
                    enabled: false
                    border.width: sliderScope.activeFocus
                                  ? 1
                                  : 0
                    border.color: palette.highlight
                }
                RowLayout {
                    anchors.fill: parent
                    spacing: 2
                    TextField {
                        id: cellNumField
                        Layout.fillWidth: !cellSliderLoader.active
                        implicitWidth: 70
                        enabled: cellRect.editable
                        selectByMouse: true
                        horizontalAlignment: TextInput.AlignRight
                        text: {
                            if (cellSliderLoader.active &&
                                cellSliderLoader.item &&
                                cellSliderLoader.item.pressed)
                                return cellSliderLoader.item.value
                                           .toFixed(sliderScope.decimals)
                            if (!cellLoader.attribute)
                                return ""
                            var v = Number(cellLoader.attribute.value)
                            return isNaN(v)
                                   ? String(cellLoader.attribute.value)
                                   : v.toFixed(sliderScope.decimals)
                        }
                        background: Rectangle {
                            color: Qt.darker(palette.window, 1.2)
                            radius: 2
                            border.width: cellNumField.activeFocus
                                          ? 1 :
                                          0
                            border.color: palette.highlight
                        }
                        color: palette.text
                        onEditingFinished: {
                            if (!cellLoader.attribute || !cellNumField.activeFocus)
                                return
                            _currentScene.setAttribute(
                                cellLoader.attribute,
                                cellLoader.attribute.type === "IntParam"
                                    ? parseInt(text)
                                    : parseFloat(text))
                        }
                        WheelHandler {
                            enabled: cellNumField.activeFocus
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
                                var v = Number(cellLoader.attribute.value) +
                                        dir * step
                                if (cellLoader.attribute.desc &&
                                    cellLoader.attribute.desc.range) {
                                    v = Math.max(cellLoader.attribute.desc.range[0],
                                        Math.min(cellLoader.attribute.desc.range[1], v))
                                }
                                _currentScene.setAttribute(
                                    cellLoader.attribute,
                                    cellLoader.attribute.type === "IntParam"
                                        ? Math.round(v)
                                        : parseFloat(v.toFixed(sliderScope.decimals)))
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
                            id: innerSlider
                            enabled: cellRect.editable
                            from: cellLoader.attribute.desc.range[0]
                            to: cellLoader.attribute.desc.range[1]
                            stepSize: cellLoader.attribute.desc.range[2]
                            snapMode: Slider.SnapAlways
                            value: {
                                if (!cellLoader.attribute)
                                    return from
                                var v = Number(cellLoader.attribute.value)
                                if (isNaN(v))
                                    return from
                                return Math.max(from, Math.min(to, v))
                            }
                            background: Rectangle {
                                x: innerSlider.leftPadding
                                y: innerSlider.topPadding +
                                   innerSlider.availableHeight / 2 - height / 2
                                width: innerSlider.availableWidth
                                height: 4
                                radius: 2
                                color: Qt.darker(palette.window, 1.4)
                                border.width: innerSlider.activeFocus
                                              ? 1
                                              : 0
                                border.color: palette.highlight
                                Rectangle {
                                    width: innerSlider.visualPosition * parent.width
                                    height: parent.height
                                    color: palette.highlight
                                    radius: 2
                                }
                            }
                            onPressedChanged: {
                                if (!cellLoader.attribute || pressed)
                                    return
                                var v = parseFloat(
                                    value.toFixed(sliderScope.decimals))
                                if (isNaN(v))
                                    return
                                _currentScene.setAttribute(
                                    cellLoader.attribute, v)
                            }
                        }
                    }
                }
            }
        }
        Component {
            id: cellCheckboxComponent
            Item {
                property real minWidth: 40
                CheckBox {
                    id: innerCheckBox
                    anchors.centerIn: parent
                    enabled: cellRect.editable
                    checked: cellLoader.attribute
                             ? cellLoader.attribute.value
                             : false
                    onToggled: {
                        if (!cellLoader.attribute)
                            return
                        _currentScene.setAttribute(cellLoader.attribute, checked)
                    }
                }
                Rectangle {
                    anchors.fill: innerCheckBox
                    color: "transparent"
                    radius: 2
                    border.width: innerCheckBox.activeFocus ? 2 : 0
                    border.color: root.appPalette.highlight
                    z: 10
                    enabled: false
                }
            }
        }
        Component {
            id: cellTextFieldComponent
            TextField {
                id: innerTextField
                property real minWidth: 120
                anchors.fill: parent
                enabled: cellRect.editable
                text: cellLoader.attribute
                      ? String(cellLoader.attribute.value)
                      : ""
                placeholderText: cellLoader.attribute &&
                                 cellLoader.attribute.isMandatory
                                 ? "This field is required"
                                 : ""
                placeholderTextColor: "gray"
                selectByMouse: true
                background: Rectangle {
                    anchors.fill: innerTextField
                    color: Qt.darker(palette.window, 1.2)
                    radius: 2
                    border.width: innerTextField.activeFocus
                                  ? 1
                                  : 0
                    border.color: palette.highlight
                }
                color: palette.text
                onEditingFinished: {
                    if (!cellLoader.attribute || !activeFocus)
                        return
                    _currentScene.setAttribute(
                        cellLoader.attribute, text.trim())
                }
            }
        }
        Component {
            id: cellTextAreaComponent
            TextField {
                id: innerTextArea
                property real minWidth: 120
                anchors.fill: parent
                enabled: cellRect.editable
                text: cellLoader.attribute
                      ? String(cellLoader.attribute.value)
                      : ""
                selectByMouse: true
                background: Rectangle {
                    anchors.fill: innerTextArea
                    color: palette.base
                    radius: 2
                    border.width: innerTextArea.activeFocus
                                  ? 1
                                  : 0
                    border.color: palette.highlight
                }
                color: palette.text
                onEditingFinished: {
                    if (!cellLoader.attribute || !activeFocus)
                        return
                    _currentScene.setAttribute(
                        cellLoader.attribute, text.trim())
                }
            }
        }
        Component {
            id: cellColorComponent
            TextField {
                id: innerColor
                property real minWidth: 60
                anchors.fill: parent
                enabled: cellRect.editable
                text: cellLoader.attribute
                      ? String(cellLoader.attribute.value)
                      : ""
                selectByMouse: true
                background: Rectangle {
                    anchors.fill: innerColor
                    color: Qt.darker(palette.window, 1.2)
                    radius: 2
                    border.width: innerColor.activeFocus
                                  ? 1
                                  : 0
                    border.color: palette.highlight
                }
                color: palette.text
                onEditingFinished: {
                    if (!cellLoader.attribute || !activeFocus)
                        return
                    _currentScene.setAttribute(cellLoader.attribute, text)
                }
            }
        }
        Component {
            id: cellPushButtonComponent
            Button {
                id: innerButton
                property real minWidth: 80
                anchors.fill: parent
                text: cellLoader.attribute
                      ? cellLoader.attribute.label
                      : ""
                background: Rectangle {
                    anchors.fill: innerButton
                    color: palette.button
                    radius: 3
                    border.width: innerButton.activeFocus 
                                  ? 1
                                  : 0
                    border.color: innerButton.activeFocus
                                  ? palette.highlight
                                  : palette.mid
                }
                enabled: cellRect.editable
                onClicked: {
                    if (!cellLoader.attribute)
                        return
                    cellLoader.attribute.clicked()
                }
            }
        }
        Component {
            id: cellColorHueComponent
            FocusScope {
                id: hueScope
                property real minWidth: 96
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    radius: 3
                    z: 10
                    enabled: false
                    border.width: hueScope.activeFocus
                                  ? 1
                                  : 0
                    border.color: palette.highlight
                }
                RowLayout {
                    anchors.fill: parent
                    spacing: 4
                    Slider {
                        id: cellHueSlider
                        Layout.fillWidth: true
                        enabled: cellRect.editable
                        from: 0; to: 1; stepSize: 0.01
                        snapMode: Slider.SnapAlways
                        value: cellLoader.attribute
                               ? Number(cellLoader.attribute.value)
                               : 0
                        onPressedChanged: {
                            if (!cellLoader.attribute || pressed)
                                return
                            _currentScene.setAttribute(
                                cellLoader.attribute,
                                parseFloat(value.toFixed(2)))
                        }
                    }
                    Rectangle {
                        width: 16
                        height: 16
                        radius: 2
                        color: Qt.hsla(cellHueSlider.value, 1, 0.5, 1)
                        border.width: 1
                        border.color: palette.mid
                    }
                }
            }
        }
    }
}
