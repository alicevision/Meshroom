import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

import Utils 1.0
import "AttributeControls" as AttributeControls
import "AnySetUtils.js" as AnySetUtils

/**
 * Inline form to edit the description of an AnySet child attribute: its name and label,
 * and the parameters that depend on its type (range, choice values, default value).
 * It is displayed right under the attribute's row, with the labels above the fields so that it fits narrow panels.
 * The default value is edited with the same controls as the attribute's value in the Node Editor.
 */

Pane {
    id: root

    property var targetAttribute: null

    // Emitted when the form is done, whether the changes were applied or discarded
    signal closed()

    readonly property string attributeType: targetAttribute ? targetAttribute.type : ""
    readonly property string semantic: targetAttribute ? targetAttribute.desc.semantic : ""
    readonly property bool isInt: attributeType === "IntParam"
    readonly property bool isNumber: isInt || attributeType === "FloatParam"
    readonly property bool isHue: attributeType === "FloatParam" && semantic === "color/hue"
    readonly property bool isBool: attributeType === "BoolParam"
    readonly property bool isChoice: attributeType === "ChoiceParam"
    readonly property bool isMultiChoice: isChoice && !targetAttribute.desc.exclusive
    readonly property bool isMultiline: attributeType === "StringParam" && semantic.includes("multiline")
    readonly property bool hasDefaultValue: ["StringParam", "File", "IntParam", "FloatParam", "BoolParam", "ChoiceParam", "ColorParam"].includes(attributeType)

    // Pending default value, set by the value control and applied with the other parameters
    property var defaultValue: targetAttribute && hasDefaultValue ? targetAttribute.desc.value : undefined

    // Context expected by the AttributeControls, which are usually created by an AttributeItemDelegate
    readonly property var errorMessages: []
    readonly property Item parameterLabel: root

    readonly property bool nameValid: nameField.acceptableInput && AnySetUtils.isNameAvailable(targetAttribute, nameField.text.trim())
    readonly property bool labelValid: labelField.text.trim() !== ""
    readonly property bool hasRange: isNumber && minField.text !== "" && minField.acceptableInput && maxField.acceptableInput && stepField.acceptableInput
    readonly property bool rangeValid: !isNumber || hasRange || (minField.text === "" && maxField.text === "" && stepField.text === "")
    readonly property bool valid: nameValid && labelValid && rangeValid && (!isChoice || choiceValues().length > 0)

    readonly property var numberRegex: isInt ? /^-?\d+$/ : /^-?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/

    padding: 8
    background: Rectangle {
        color: Qt.darker(root.palette.window, 1.1)
    }

    Keys.onEscapePressed: root.cancel()

    Component.onCompleted: {
        // Wait for the menu that requested the edition to close and give the focus back before taking it
        Qt.callLater(function() {
            nameField.forceActiveFocus()
            nameField.selectAll()
        })
    }

    function typeText() {
        if (attributeType === "ListAttribute")
            return "ListAttribute of " + targetAttribute.baseType
        return semantic ? attributeType + " (" + semantic + ")" : attributeType
    }

    function rangeValue(index) {
        var range = targetAttribute ? targetAttribute.desc.range : undefined
        return range && range.length > index ? String(range[index]) : ""
    }

    function splitList(text) {
        return text.split(",").map(function(v) { return v.trim() }).filter(function(v) { return v !== "" })
    }

    function choiceValues() {
        return splitList(valuesField.text)
    }

    function parameters() {
        var params = {
            "name": nameField.text.trim(),
            "label": labelField.text.trim(),
            "description": descriptionField.text,
            "advanced": advancedCheckBox.checked
        }
        if (isNumber)
            params["defaultValue"] = Number(defaultValue)
        else if (isMultiChoice)
            // Only keep the default choices that are still available
            params["defaultValue"] = defaultValue.filter(function(v) { return choiceValues().includes(v) })
        else if (hasDefaultValue)
            params["defaultValue"] = defaultValue
        if (isNumber)
            params["range"] = hasRange ? [Number(minField.text), Number(maxField.text), Number(stepField.text)] : []
        if (isChoice)
            params["values"] = choiceValues()
        return params
    }

    function apply() {
        if (!targetAttribute || !valid)
            return
        var attribute = targetAttribute
        var params = parameters()
        // Close first: the edited attribute is replaced by a new one, which destroys this form
        root.closed()
        _currentScene.editAnySetAttribute(attribute, params)
    }

    function cancel() {
        root.closed()
    }

    // Red border on top of the default background of an invalid field
    component ErrorBorder: Rectangle {
        anchors.fill: parent
        radius: 4
        border.color: "red"
        color: "transparent"
        z: 1
    }

    component FieldLabel: Label {
        font.pointSize: 8
        Layout.fillWidth: true
        elide: Text.ElideRight
    }

    component FormField: TextField {
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        selectByMouse: true
        onAccepted: root.apply()
    }

    component NumberField: FormField {
        validator: RegularExpressionValidator { regularExpression: root.numberRegex }
    }

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 4

        FieldLabel { text: "Name" }
        FormField {
            id: nameField
            text: root.targetAttribute ? root.targetAttribute.name : ""
            validator: RegularExpressionValidator { regularExpression: /^[A-Za-z_][A-Za-z0-9_]*$/ }
            ErrorBorder { visible: !root.nameValid }
            ToolTip.text: nameField.acceptableInput ? "An attribute with this name already exists." : "Invalid attribute name."
            ToolTip.visible: !root.nameValid && hovered
        }

        FieldLabel { text: "Label" }
        FormField {
            id: labelField
            text: root.targetAttribute ? root.targetAttribute.label : ""
            ErrorBorder { visible: !root.labelValid }
        }

        RowLayout {
            spacing: 6
            Layout.fillWidth: true

            Label {
                text: "Type"
                font.pointSize: 8
            }
            Label {
                text: root.typeText()
                color: Colors.lightgrey
                elide: Text.ElideRight
                Layout.fillWidth: true
                Layout.minimumWidth: 0
            }
        }

        FieldLabel {
            visible: root.isNumber && !root.isHue
            text: "Range (min · max · step)"
        }
        RowLayout {
            visible: root.isNumber && !root.isHue
            spacing: 6
            Layout.fillWidth: true

            NumberField {
                id: minField
                text: root.rangeValue(0)
                placeholderText: "Min"
                ToolTip.text: "Minimum"
                ToolTip.visible: hovered
                ErrorBorder { visible: !root.rangeValid }
            }
            NumberField {
                id: maxField
                text: root.rangeValue(1)
                placeholderText: "Max"
                ToolTip.text: "Maximum"
                ToolTip.visible: hovered
                ErrorBorder { visible: !root.rangeValid }
            }
            NumberField {
                id: stepField
                text: root.rangeValue(2)
                placeholderText: "Step"
                ToolTip.text: "Step"
                ToolTip.visible: hovered
                ErrorBorder { visible: !root.rangeValid }
            }
        }

        FieldLabel {
            visible: root.isChoice
            text: "Values"
        }
        FormField {
            id: valuesField
            visible: root.isChoice
            text: root.isChoice ? root.targetAttribute.desc.values.join(", ") : ""
            placeholderText: "Comma-separated values"
            ErrorBorder { visible: root.isChoice && root.choiceValues().length === 0 }
        }

        FieldLabel {
            visible: root.hasDefaultValue
            text: "Default"
        }
        Loader {
            id: defaultValueLoader
            active: root.hasDefaultValue
            visible: active
            Layout.fillWidth: true
            // TextAreaFlick has a fixed height and no implicit height
            Layout.preferredHeight: item ? (item.implicitHeight > 0 ? item.implicitHeight : item.height) : 0

            sourceComponent: {
                if (root.isBool)
                    return checkBoxComponent
                if (root.isHue)
                    return hueComponent
                if (root.isNumber)
                    return sliderComponent
                if (root.isMultiChoice)
                    return choiceMultiComponent
                if (root.isChoice)
                    return choiceComponent
                if (root.attributeType === "ColorParam")
                    return colorComponent
                if (root.isMultiline)
                    return textAreaComponent
                return textFieldComponent
            }
        }

        FieldLabel { text: "Description" }
        FormField {
            id: descriptionField
            text: root.targetAttribute ? root.targetAttribute.desc.description : ""
        }

        CheckBox {
            id: advancedCheckBox
            text: "Advanced"
            checked: root.targetAttribute ? root.targetAttribute.desc.advanced : false
            padding: 0
            Layout.topMargin: 2
        }

        RowLayout {
            spacing: 6
            Layout.alignment: Qt.AlignRight

            Button {
                text: "OK"
                enabled: root.valid
                onClicked: root.apply()
            }
            Button {
                text: "Cancel"
                onClicked: root.cancel()
            }
        }
    }

    Component {
        id: textFieldComponent
        AttributeControls.TextFieldRow {
            text: root.defaultValue !== undefined && root.defaultValue !== null ? root.defaultValue : ""
            mandatory: false
            attribute: root.targetAttribute
            editable: true
            onEditingFinished: (text) => root.defaultValue = text
            onAccepted: (parameterLabel, text) => {
                root.defaultValue = text
                root.apply()
            }
            onDropped: (hasUrls, hasText, urlText, text) => {
                if (hasUrls)
                    root.defaultValue = urlText
                else if (hasText)
                    root.defaultValue = text
            }
            onTriggered: (text, start, end, length, clipboard) => {
                root.defaultValue = text.substr(0, start) + clipboard + text.substr(end, length)
            }
        }
    }

    Component {
        id: textAreaComponent
        AttributeControls.TextAreaFlick {
            label: root.defaultValue
            editable: true
            onEditingFinished: (text) => root.defaultValue = text
            onDropped: (hasUrls, hasText, urlText, text) => {
                if (hasUrls)
                    root.defaultValue = urlText
                else if (hasText)
                    root.defaultValue = text
            }
        }
    }

    Component {
        id: sliderComponent
        AttributeControls.SliderField {
            checked: root.defaultValue
            type: root.attributeType
            // The slider follows the range being edited
            length: root.hasRange ? 3 : 0
            start: root.hasRange ? Number(minField.text) : 0
            end: root.hasRange ? Number(maxField.text) : 0
            step: root.hasRange ? Number(stepField.text) : 0
            editable: true
            onEditingFinished: (hasExprError, evaluatedValue, text, displayValue) => {
                if (!hasExprError)
                    root.defaultValue = evaluatedValue
            }
            onAccepted: (hasExprError, evaluatedValue, text, displayValue) => {
                if (!hasExprError) {
                    root.defaultValue = evaluatedValue
                    root.apply()
                }
            }
            onPressedChanged: (pressed, formattedValue) => {
                if (!pressed)
                    root.defaultValue = formattedValue
            }
        }
    }

    Component {
        id: hueComponent
        AttributeControls.ColorHue {
            value: root.defaultValue
            editable: true
            onEditingFinished: (text) => root.defaultValue = Number(text)
            onAccepted: (text) => {
                root.defaultValue = Number(text)
                root.apply()
            }
            onPressedChanged: (pressed, formattedValue) => {
                if (!pressed)
                    root.defaultValue = formattedValue
            }
        }
    }

    Component {
        id: checkBoxComponent
        AttributeControls.CheckBoxRow {
            editable: true
            checked: root.defaultValue
            onToggled: root.defaultValue = !root.defaultValue
        }
    }

    Component {
        id: choiceComponent
        AttributeControls.Choice {
            // The possible values follow the values being edited
            value: root.defaultValue
            values: root.choiceValues()
            onEditingFinished: (value) => root.defaultValue = value
        }
    }

    Component {
        id: choiceMultiComponent
        AttributeControls.ChoiceMulti {
            value: root.defaultValue
            values: root.choiceValues()
            customValueColor: Colors.orange
            onToggled: (value, checked) => {
                var defaultValue = root.defaultValue.slice()
                if (checked)
                    defaultValue.push(value)
                else
                    defaultValue.splice(defaultValue.indexOf(value), 1)
                root.defaultValue = defaultValue
            }
        }
    }

    Component {
        id: colorComponent
        AttributeControls.Color {
            id: colorControl
            value: root.defaultValue
            editable: true
            onClicked: (checked, previousColor, colorTextValue) => {
                if (checked) {
                    if (colorTextValue !== "")
                        root.defaultValue = colorTextValue
                    else
                        root.defaultValue = previousColor !== "" ? previousColor : "#0000FF"
                } else {
                    colorControl.previousColor = root.defaultValue
                    root.defaultValue = ""
                }
            }
            onEditingFinished: (text) => root.defaultValue = text
            onAccepted: (text) => root.defaultValue = text
        }
    }
}
