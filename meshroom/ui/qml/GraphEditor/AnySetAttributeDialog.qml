import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

import Utils 1.0
import "AnySetUtils.js" as AnySetUtils

/**
 * Dialog to edit the description of an AnySet child attribute: its name and label,
 * and the parameters that depend on its type (default value, range, choice values).
 */

Dialog {
    id: root

    property var targetAttribute: null
    property real preferredX: 0
    property real preferredY: 0

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

    title: "Edit Attribute"
    modal: true
    parent: Overlay.overlay
    contentWidth: 330
    x: parent ? Math.max(0, Math.min(preferredX, parent.width - width)) : 0
    y: parent ? Math.max(0, Math.min(preferredY, parent.height - height)) : 0
    standardButtons: Dialog.Ok | Dialog.Cancel
    closePolicy: Popup.CloseOnEscape

    Component.onCompleted: standardButton(Dialog.Ok).enabled = Qt.binding(function() { return root.valid })

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

    // Red border on top of the default background of an invalid field
    component ErrorBorder: Rectangle {
        anchors.fill: parent
        radius: 4
        border.color: "red"
        color: "transparent"
        z: 1
    }

    component NumberField: TextField {
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        selectByMouse: true
        validator: RegularExpressionValidator { regularExpression: root.numberRegex }
        onAccepted: root.tryAccept()
    }

    GridLayout {
        columns: 2
        columnSpacing: 8
        rowSpacing: 8
        width: root.contentWidth

        Label {
            text: "Name"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
        }
        TextField {
            id: nameField
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: root.targetAttribute ? root.targetAttribute.name : ""
            selectByMouse: true
            validator: RegularExpressionValidator { regularExpression: /^[A-Za-z_][A-Za-z0-9_]*$/ }
            onAccepted: root.tryAccept()
            ErrorBorder { visible: !root.nameValid }
            ToolTip.text: nameField.acceptableInput ? "An attribute with this name already exists." : "Invalid attribute name."
            ToolTip.visible: !root.nameValid && hovered
        }

        Label {
            text: "Label"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
        }
        TextField {
            id: labelField
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: root.targetAttribute ? root.targetAttribute.label : ""
            selectByMouse: true
            onAccepted: root.tryAccept()
            ErrorBorder { visible: !root.labelValid }
        }

        Label {
            text: "Type"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
        }
        Label {
            text: root.attributeType
            color: Colors.lightgrey
            Layout.fillWidth: true
        }

        Label {
            visible: root.hasDefaultValue
            text: "Default"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
        }
        TextField {
            id: defaultField
            visible: root.hasDefaultValue && !root.isBool
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: root.targetAttribute && root.hasDefaultValue ? root.defaultValueText() : ""
            selectByMouse: true
            validator: RegularExpressionValidator { regularExpression: root.isNumber ? root.numberRegex : /.*/ }
            onAccepted: root.tryAccept()
            ErrorBorder { visible: root.isNumber && !defaultField.acceptableInput }
        }
        CheckBox {
            id: defaultCheckBox
            visible: root.isBool
            checked: root.isBool && root.targetAttribute.desc.value === true
            padding: 0
        }

        Label {
            visible: root.isNumber
            text: "Range"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
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

        Label {
            visible: root.isChoice
            text: "Values"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
        }
        TextField {
            id: valuesField
            visible: root.isChoice
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: root.isChoice ? root.targetAttribute.desc.values.join(", ") : ""
            placeholderText: "Comma-separated values"
            selectByMouse: true
            onAccepted: root.tryAccept()
            ErrorBorder { visible: root.isChoice && root.choiceValues().length === 0 }
        }

        Label {
            text: "Description"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
        }
        TextField {
            id: descriptionField
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            text: root.targetAttribute ? root.targetAttribute.desc.description : ""
            selectByMouse: true
            onAccepted: root.tryAccept()
        }

        Item { width: 1; height: 1 }
        CheckBox {
            id: advancedCheckBox
            text: "Advanced"
            checked: root.targetAttribute ? root.targetAttribute.desc.advanced : false
            padding: 0
        }
    }

    function tryAccept() {
        if (valid)
            accept()
    }

    onOpened: {
        nameField.forceActiveFocus()
        nameField.selectAll()
    }

    onAccepted: {
        if (targetAttribute && valid) {
            _currentScene.editAnySetAttribute(targetAttribute, parameters())
        }
        destroy()
    }

    onRejected: destroy()
}
