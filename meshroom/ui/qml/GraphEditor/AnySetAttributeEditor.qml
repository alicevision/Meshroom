import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

import Utils 1.0
import "AnySetUtils.js" as AnySetUtils

/**
 * Inline form to edit the description of an AnySet child attribute: its name and label,
 * and the parameters that depend on its type (default value, range, choice values).
 * It is displayed right under the attribute's row, with the labels above the fields so that it fits narrow panels.
 */

Pane {
    id: root

    property var targetAttribute: null

    // Emitted when the form is done, whether the changes were applied or discarded
    signal closed()

    readonly property string attributeType: targetAttribute ? targetAttribute.type : ""
    readonly property bool isInt: attributeType === "IntParam"
    readonly property bool isNumber: isInt || attributeType === "FloatParam"
    readonly property bool isBool: attributeType === "BoolParam"
    readonly property bool isChoice: attributeType === "ChoiceParam"
    readonly property bool isMultiChoice: isChoice && !targetAttribute.desc.exclusive
    readonly property bool hasDefaultValue: ["StringParam", "File", "IntParam", "FloatParam", "BoolParam", "ChoiceParam", "ColorParam"].includes(attributeType)

    readonly property bool nameValid: nameField.acceptableInput && AnySetUtils.isNameAvailable(targetAttribute, nameField.text.trim())
    readonly property bool labelValid: labelField.text.trim() !== ""
    readonly property bool rangeValid: !isNumber || (minField.text === "" && maxField.text === "" && stepField.text === "")
                                       || (minField.acceptableInput && maxField.acceptableInput && stepField.acceptableInput)
    readonly property bool valid: nameValid && labelValid && rangeValid
                                  && (!isNumber || defaultField.acceptableInput)
                                  && (!isChoice || choiceValues().length > 0)

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

    function rangeValue(index) {
        var range = targetAttribute ? targetAttribute.desc.range : undefined
        return range && range.length > index ? String(range[index]) : ""
    }

    function defaultValueText() {
        var value = targetAttribute.desc.value
        if (value === undefined || value === null)
            return ""
        return isMultiChoice ? value.join(", ") : String(value)
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
        if (isBool)
            params["defaultValue"] = defaultCheckBox.checked
        else if (isNumber)
            params["defaultValue"] = Number(defaultField.text)
        else if (isMultiChoice)
            params["defaultValue"] = splitList(defaultField.text)
        else if (hasDefaultValue)
            params["defaultValue"] = defaultField.text
        if (isNumber)
            params["range"] = minField.text === "" ? [] : [Number(minField.text), Number(maxField.text), Number(stepField.text)]
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

        GridLayout {
            columns: 2
            columnSpacing: 6
            rowSpacing: 4
            Layout.fillWidth: true

            FieldLabel {
                text: "Default"
                visible: root.hasDefaultValue
                Layout.preferredWidth: 1
            }
            FieldLabel {
                text: "Type"
                Layout.preferredWidth: 1
            }

            Item {
                visible: root.hasDefaultValue
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
                implicitHeight: root.isBool ? defaultCheckBox.implicitHeight : defaultField.implicitHeight

                FormField {
                    id: defaultField
                    visible: !root.isBool
                    width: parent.width
                    text: root.targetAttribute && root.hasDefaultValue ? root.defaultValueText() : ""
                    validator: RegularExpressionValidator { regularExpression: root.isNumber ? root.numberRegex : /.*/ }
                    ErrorBorder { visible: root.isNumber && !defaultField.acceptableInput }
                }
                CheckBox {
                    id: defaultCheckBox
                    visible: root.isBool
                    anchors.verticalCenter: parent.verticalCenter
                    checked: root.isBool && root.targetAttribute.desc.value === true
                    padding: 0
                }
            }
            Label {
                text: root.attributeType
                color: Colors.lightgrey
                elide: Text.ElideRight
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.minimumWidth: 0
            }
        }

        FieldLabel {
            visible: root.isNumber
            text: "Range (min · max · step)"
        }
        RowLayout {
            visible: root.isNumber
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
}
