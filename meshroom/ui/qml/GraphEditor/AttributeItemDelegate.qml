import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Dialogs

import MaterialIcons 2.2
import Utils 1.0
import Controls 1.0

/**
 * Instantiate a control to visualize and edit an Attribute based on its type.
 */

RowLayout {
    id: root

    property variant attribute: null
    property bool readOnly: false  // Whether the attribute's value can be modified
    property bool objectsHideable: true
    property string filterText: ""

    property alias label: parameterLabel  // Accessor to the internal Label (attribute's name)
    property int labelWidth               // Shortcut to set the fixed size of the Label

    readonly property bool editable: !attribute.isOutput && !attribute.isLink && !readOnly

    signal doubleClicked(var mouse, var attr)

    spacing: 2

    function updateAttributeLabel() {
        background.color = attribute.validValue ?  Qt.darker(palette.window, 1.1) : Qt.darker(Colors.red, 1.5)

        if (attribute.desc) {
            var tooltip = ""
            if (!attribute.validValue && attribute.desc.errorMessage !== "")
                tooltip += "<i><b>Error: </b>" + Format.plainToHtml(attribute.desc.errorMessage) + "</i><br><br>"
            tooltip += "<b> " + attribute.desc.name + ":</b> " + attribute.type + "<br>" + Format.plainToHtml(attribute.desc.description)

            parameterTooltip.text = tooltip
        }
    }

    Pane {
        background: Rectangle {
            id: background
            color: object != undefined && object.validValue ? Qt.darker(parent.palette.window, 1.1) : Qt.darker(Colors.red, 1.5)
        }
        padding: 0
        Layout.preferredWidth: labelWidth || implicitWidth
        Layout.fillHeight: true

        RowLayout {
            spacing: 0
            width: parent.width
            height: parent.height

            Label {
                id: parameterLabel

                Layout.fillHeight: true
                Layout.fillWidth: true
                horizontalAlignment: attribute.isOutput ? Qt.AlignRight : Qt.AlignLeft
                elide: Label.ElideRight
                padding: 5
                wrapMode: Label.WrapAtWordBoundaryOrAnywhere

                text: object.label

                color: {
                    if (object != undefined && (object.hasOutputConnections || object.isLink) && !object.enabled)
                        return Colors.lightgrey
                    else
                        return palette.text
                }

                // Tooltip hint with attribute's description
                ToolTip {
                    id: parameterTooltip

                    // Position in y at mouse position
                    y: parameterMA.mouseY + 10

                    text: {
                        var tooltip = ""
                        if (!object.validValue && object.desc.errorMessage !== "")
                            tooltip += "<i><b>Error: </b>" + Format.plainToHtml(object.desc.errorMessage) + "</i><br><br>"
                        tooltip += "<b>" + object.desc.name + ":</b> " + attribute.type + "<br>" + Format.plainToHtml(object.description)
                        return tooltip
                    }
                    visible: parameterMA.containsMouse
                    delay: 800
                }

                // Make label bold if attribute's value is not the default one
                font.bold: !object.isOutput && !object.isDefault

                // Make label italic if attribute is a link
                font.italic: object.isLink

                MouseArea {
                    id: parameterMA
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.AllButtons
                    onDoubleClicked: function(mouse) { root.doubleClicked(mouse, root.attribute) }

                    property Component menuComp: Menu {
                        id: paramMenu

                        property bool isFileAttribute: attribute.type === "File"
                        property bool isFilepath: isFileAttribute && Filepath.isFile(attribute.evalValue)

                        MenuItem {
                            text: "Reset To Default Value"
                            enabled: root.editable && !attribute.isDefault
                            onTriggered: {
                                _reconstruction.resetAttribute(attribute)
                                updateAttributeLabel()
                            }
                        }
                        MenuItem {
                            text: "Copy"
                            enabled: attribute.value != ""
                            onTriggered: {
                                Clipboard.clear()
                                Clipboard.setText(attribute.value)
                            }
                        }
                        MenuItem {
                            text: "Paste"
                            enabled: Clipboard.getText() != "" && root.editable
                            onTriggered: {
                                _reconstruction.setAttribute(attribute, Clipboard.getText())
                            }
                        }

                        MenuSeparator {
                            visible: paramMenu.isFileAttribute
                            height: visible ? implicitHeight : 0
                        }

                        MenuItem {
                            visible: paramMenu.isFileAttribute
                            height: visible ? implicitHeight : 0
                            text: paramMenu.isFilepath ? "Open Containing Folder" : "Open Folder"
                            onClicked: paramMenu.isFilepath ? Qt.openUrlExternally(Filepath.dirname(attribute.evalValue)) :
                                                              Qt.openUrlExternally(Filepath.stringToUrl(attribute.evalValue))
                        }

                        MenuItem {
                            visible: paramMenu.isFilepath
                            height: visible ? implicitHeight : 0
                            text: "Open File"
                            onClicked: Qt.openUrlExternally(Filepath.stringToUrl(attribute.value))
                        }
                    }

                    onClicked: function(mouse) {
                        forceActiveFocus()
                        if (mouse.button == Qt.RightButton) {
                            var menu = menuComp.createObject(parameterLabel)
                            menu.parent = parameterLabel
                            menu.popup()
                        }
                    }
                }
            }
            MaterialLabel {
                visible: attribute.desc.advanced
                text: MaterialIcons.build
                color: palette.mid
                font.pointSize: 8
                padding: 4
            }
        }
    }

    function setTextFieldAttribute(value) {
        // editingFinished called even when TextField is readonly
        if (!editable)
            return
        switch (attribute.type) {
            case "IntParam":
            case "FloatParam":
                _reconstruction.setAttribute(root.attribute, Number(value))
                updateAttributeLabel()
                break
            case "File":
                _reconstruction.setAttribute(root.attribute, value)
                break
            default:
                _reconstruction.setAttribute(root.attribute, value.trim())
                updateAttributeLabel()
                break
        }
    }

    Loader {
        Layout.fillWidth: true

        sourceComponent: {
            // PushButtonParam always has value == undefined, so it needs to be excluded from this check
            if (attribute.type != "PushButtonParam" && attribute.value === undefined) {
                return notComputedComponent
            }
            switch (attribute.type) {
                case "PushButtonParam":
                    return pushButtonComponent
                case "ChoiceParam":
                    return attribute.desc.exclusive ? comboBoxComponent : multiChoiceComponent
                case "IntParam": return sliderComponent
                case "FloatParam":
                    if (attribute.desc.semantic === 'color/hue')
                        return colorHueComponent
                    return sliderComponent
                case "BoolParam":
                    return checkboxComponent
                case "ListAttribute":
                    return listAttributeComponent
                case "GroupAttribute":
                    return groupAttributeComponent
                case "StringParam":
                    if (attribute.desc.semantic.includes('multiline'))
                        return textAreaComponent
                    return textFieldComponent
                case "ColorParam":
                    return colorComponent
                default:
                    return textFieldComponent
            }
        }

        Component {
            id: notComputedComponent
            MaterialLabel {
                anchors.fill: parent
                text: MaterialIcons.do_not_disturb_alt
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                padding: 4
                background: Rectangle {
                    anchors.fill: parent
                    border.width: 0
                    radius: 20
                    color: Qt.darker(palette.window, 1.1)
                }
            }
        }

        Component {
            id: pushButtonComponent
            Button {
                text: attribute.label
                enabled: root.editable
                onClicked: {
                    attribute.clicked()
                }
            }
        }

        Component {
            id: textFieldComponent
            TextField {
                id: textField
                readOnly: !root.editable
                text: attribute.value
                selectByMouse: true
                onEditingFinished: setTextFieldAttribute(text)
                persistentSelection: false
                property bool memoryActiveFocus: false
                onAccepted: {
                    setTextFieldAttribute(text)
                    parameterLabel.forceActiveFocus()
                }
                Keys.onPressed: function(event) {
                    if ((event.key == Qt.Key_Escape)) {
                        event.accepted = true
                        parameterLabel.forceActiveFocus()
                    }
                }
                Component.onDestruction: {
                    if (activeFocus)
                        setTextFieldAttribute(text)
                }
                DropArea {
                    enabled: root.editable
                    anchors.fill: parent
                    onDropped: function(drop) {
                        if (drop.hasUrls)
                            setTextFieldAttribute(Filepath.urlToString(drop.urls[0]))
                        else if (drop.hasText && drop.text != '')
                            setTextFieldAttribute(drop.text)
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.RightButton
                    onClicked: function(mouse) {
                        // Do not lose the selection during the right click
                        textField.persistentSelection = true
                        // We store the status of the activeFocus before opening the popup
                        textField.memoryActiveFocus = textField.activeFocus
                        var menu = menuCopy.createObject(textField)
                        menu.parent = textField
                        menu.popup()
                        if(textField.memoryActiveFocus) {
                            // If the focus was active, we continue to display the cursor
                            // to explain that we will insert the new text in this position (in case of "Paste" action)
                            textField.cursorVisible = true
                        }
                        // We do not want the selection to be globally persistent
                        textField.persistentSelection = false
                    }

                    property Component menuCopy : Menu {
                        MenuItem {
                            text: "Copy"
                            enabled: attribute.value != ""
                            onTriggered: {
                                if (textField.selectionStart === textField.selectionEnd) {
                                    // If no selection
                                    Clipboard.clear()
                                    Clipboard.setText(attribute.value)
                                } else {
                                    // Copy selection only
                                    textField.copy()
                                }
                            }
                        }
                        MenuItem {
                            text: "Paste"
                            enabled: Clipboard.getText() != "" && !readOnly
                            onTriggered: {
                                if (textField.memoryActiveFocus) {
                                    // Replace the selected text with the clipboard
                                    // or if there is no selection insert at the cursor position
                                    var before = textField.text.substr(0, textField.selectionStart)
                                    var after = textField.text.substr(textField.selectionEnd, textField.text.length)
                                    setTextFieldAttribute(before + Clipboard.getText() + after)
                                    // Set the cursor at the end of the added text
                                    textField.cursorPosition = before.length + Clipboard.getText().length
                                } else {
                                    setTextFieldAttribute(Clipboard.getText())
                                }
                            }
                        }
                    } 
                }
            }
        }

        Component {
            id: textAreaComponent

            Rectangle {
                // Fixed background for the flickable object
                color: palette.base
                width: parent.width
                height: attribute.desc.semantic.includes("large") ? 400 : 70

                Flickable {
                    width: parent.width
                    height: parent.height
                    contentWidth: width
                    contentHeight: height

                    ScrollBar.vertical: MScrollBar {}

                    TextArea.flickable: TextArea {
                        wrapMode: Text.WordWrap
                        padding: 0
                        rightPadding: 5
                        bottomPadding: 2
                        topPadding: 2
                        readOnly: !root.editable
                        onEditingFinished: setTextFieldAttribute(text)
                        text: attribute.value
                        selectByMouse: true
                        onPressed: {
                            root.forceActiveFocus()
                        }
                        Component.onDestruction: {
                            if (activeFocus)
                                setTextFieldAttribute(text)
                        }
                        DropArea {
                            enabled: root.editable
                            anchors.fill: parent
                            onDropped: {
                                if (drop.hasUrls)
                                    setTextFieldAttribute(Filepath.urlToString(drop.urls[0]))
                                else if (drop.hasText && drop.text != '')
                                    setTextFieldAttribute(drop.text)
                            }
                        }
                    }
                }
            }
        }

        Component {
            id: colorComponent
            RowLayout {
                CheckBox {
                    id: colorCheckbox
                    Layout.alignment: Qt.AlignLeft
                    checked: node && node.color === "" ? false : true
                    checkable: root.editable
                    text: "Custom Color"
                    onClicked: {
                        if (checked) {
                            if (colorText.text == "")
                                _reconstruction.setAttribute(attribute, "#0000FF")
                            else
                                _reconstruction.setAttribute(attribute, colorText.text)
                        } else {
                            _reconstruction.setAttribute(attribute, "")
                        }
                    }
                }
                TextField {
                    id: colorText
                    Layout.alignment: Qt.AlignLeft
                    implicitWidth: 100
                    enabled: colorCheckbox.checked && root.editable
                    visible: colorCheckbox.checked
                    text: colorCheckbox.checked ? attribute.value : ""
                    selectByMouse: true
                    onEditingFinished: setTextFieldAttribute(text)
                    onAccepted: setTextFieldAttribute(text)
                    Component.onDestruction: {
                        if (activeFocus)
                            setTextFieldAttribute(text)
                    }
                }

                Rectangle {
                    height: colorText.height
                    width: colorText.width / 2
                    Layout.alignment: Qt.AlignLeft
                    visible: colorCheckbox.checked
                    color: colorCheckbox.checked ? colorDialog.selectedColor : ""

                    MouseArea {
                        enabled: root.editable
                        anchors.fill: parent
                        onClicked: colorDialog.open()
                    }
                }

                ColorDialog {
                    id: colorDialog
                    title: "Please choose a color"
                    selectedColor: colorText.text
                    onAccepted: {
                        colorText.text = colorDialog.selectedColor
                        // Artificially trigger change of attribute value
                        colorText.editingFinished()
                        close()
                    }
                    onRejected: close()
                }
                Item {
                    // Dummy item to fill out the space if needed
                    Layout.fillWidth: true
                }
            }
        }

        Component {
            id: comboBoxComponent

            FilterComboBox {
                inputModel: attribute.values

                Component.onCompleted: {
                    // If value not in list, override the text and precise it is not valid
                    var idx = find(attribute.value)
                    if (idx === -1) {
                        displayText = attribute.value
                        validValue = false
                    } else {
                        currentIndex = idx
                    }
                }

                onEditingFinished: function(value) {
                    _reconstruction.setAttribute(attribute, value)
                }

                Connections {
                    target: attribute
                    function onValueChanged() {
                        // When reset, clear and find the current index
                        // but if only reopen the combo box, keep the current value
                        
                        // Convert all values of desc values as string
                        var valuesAsString = attribute.values.map(function(value) {
                            return value.toString()
                        })
                        if (valuesAsString.includes(attribute.value) || attribute.value === attribute.desc.value) {
                            filterText.clear()
                            validValue = true
                            displayText = currentText
                            currentIndex = find(attribute.value) 
                        }
                    }
                }
            }
        }

        Component {
            id: multiChoiceComponent
            Flow {
                Repeater {
                    id: checkboxRepeater
                    model: attribute.values
                    delegate: CheckBox {
                        enabled: root.editable
                        text: modelData
                        checked: attribute.value.indexOf(modelData) >= 0
                        onToggled: {
                            var t = attribute.value
                            if (!checked) {
                                t.splice(t.indexOf(modelData), 1)  // Remove element
                            } else {
                                t.push(modelData)  // Add element
                            }
                            _reconstruction.setAttribute(attribute, t)
                        }
                    }
                }
            }
        }

        Component {
            id: sliderComponent
            RowLayout {
                TextField {
                    IntValidator {
                        id: intValidator
                    }
                    DoubleValidator {
                        id: doubleValidator
                        locale: 'C'  // Use '.' decimal separator disregarding the system locale
                    }
                    implicitWidth: 100
                    Layout.fillWidth: !slider.active
                    enabled: root.editable
                    // Cast value to string to avoid intrusive scientific notations on numbers
                    property string displayValue: String(slider.active && slider.item.pressed ? slider.item.formattedValue : attribute.value)
                    text: displayValue
                    selectByMouse: true
                    // Note: Use autoScroll as a workaround for alignment
                    // When the value change keep the text align to the left to be able to read the most important part
                    // of the number. When we are editing (item is in focus), the content should follow the editing.
                    autoScroll: activeFocus
                    validator: attribute.type === "FloatParam" ? doubleValidator : intValidator
                    onEditingFinished: setTextFieldAttribute(text)
                    onAccepted: {
                        setTextFieldAttribute(text)

                        // When the text is too long, display the left part
                        // (with the most important values and cut the floating point details)
                        ensureVisible(0)
                    }
                    Component.onDestruction: {
                        if (activeFocus)
                            setTextFieldAttribute(text)
                    }
                    Component.onCompleted: {
                        // When the text is too long, display the left part
                        // (with the most important values and cut the floating point details)
                        ensureVisible(0)
                    }
                }

                Loader {
                    id: slider
                    Layout.fillWidth: true
                    active: attribute.desc.range.length === 3
                    sourceComponent: Slider {
                        readonly property int stepDecimalCount: stepSize <  1 ? String(stepSize).split(".").pop().length : 0
                        readonly property real formattedValue: value.toFixed(stepDecimalCount)
                        enabled: root.editable
                        value: attribute.value
                        from: attribute.desc.range[0]
                        to: attribute.desc.range[1]
                        stepSize: attribute.desc.range[2]
                        snapMode: Slider.SnapAlways

                        onPressedChanged: {
                            if (!pressed) {
                                _reconstruction.setAttribute(attribute, formattedValue)
                                updateAttributeLabel()
                            }
                        }
                    }
                }
            }
        }

        Component {
            id: checkboxComponent
            Row {
                CheckBox {
                    enabled: root.editable
                    checked: attribute.value
                    onToggled: _reconstruction.setAttribute(attribute, !attribute.value)
                }
            }
        }

        Component {
            id: listAttributeComponent
            ColumnLayout {
                id: listAttributeLayout
                width: parent.width
                property bool expanded: false
                RowLayout {
                    spacing: 4
                    ToolButton {
                        text: listAttributeLayout.expanded  ? MaterialIcons.keyboard_arrow_down : MaterialIcons.keyboard_arrow_right
                        font.family: MaterialIcons.fontFamily
                        onClicked: listAttributeLayout.expanded = !listAttributeLayout.expanded
                    }
                    Label {
                        Layout.alignment: Qt.AlignVCenter
                        text: attribute.value.count + " elements"
                    }
                    ToolButton {
                        text: MaterialIcons.add_circle_outline
                        font.family: MaterialIcons.fontFamily
                        font.pointSize: 11
                        padding: 2
                        enabled: root.editable
                        onClicked: _reconstruction.appendAttribute(attribute, undefined)
                    }
                }
                ListView {
                    id: lv
                    model: listAttributeLayout.expanded ? attribute.value : undefined
                    visible: model !== undefined && count > 0
                    implicitHeight: Math.min(contentHeight, 300)
                    Layout.fillWidth: true
                    Layout.margins: 4
                    clip: true
                    spacing: 4

                    ScrollBar.vertical: MScrollBar { id: sb }

                    delegate: Loader {
                        active: !objectsHideable
                            || ((object.isDefault && GraphEditorSettings.showDefaultAttributes || !object.isDefault && GraphEditorSettings.showModifiedAttributes)
                            && (object.isLinkNested && GraphEditorSettings.showLinkAttributes || !object.isLinkNested && GraphEditorSettings.showNotLinkAttributes))
                        visible: active
                        height: implicitHeight
                        sourceComponent: RowLayout {
                            id: item
                            property var childAttrib: object
                            layoutDirection: Qt.RightToLeft
                            width: lv.width - sb.width
                            Component.onCompleted: {
                                var cpt = Qt.createComponent("AttributeItemDelegate.qml")
                                var obj = cpt.createObject(item,
                                                        {
                                                            'attribute': Qt.binding(function() { return item.childAttrib }),
                                                            'readOnly': Qt.binding(function() { return !root.editable })
                                                        })
                                obj.Layout.fillWidth = true
                                obj.label.text = index
                                obj.label.horizontalAlignment = Text.AlignHCenter
                                obj.label.verticalAlignment = Text.AlignVCenter
                                obj.doubleClicked.connect(function(attr) { root.doubleClicked(attr) })
                            }
                            ToolButton {
                                enabled: root.editable
                                text: MaterialIcons.remove_circle_outline
                                font.family: MaterialIcons.fontFamily
                                font.pointSize: 11
                                padding: 2
                                ToolTip.text: "Remove Element"
                                ToolTip.visible: hovered
                                onClicked: _reconstruction.removeAttribute(item.childAttrib)
                            }
                        }
                    }
                }
            }
        }

        Component {
            id: groupAttributeComponent
            ColumnLayout {
                id: groupItem
                Component.onCompleted:  {
                    var cpt = Qt.createComponent("AttributeEditor.qml");
                    var obj = cpt.createObject(groupItem,
                                               {
                                                   'model': Qt.binding(function() { return attribute.value }),
                                                   'readOnly': Qt.binding(function() { return root.readOnly }),
                                                   'labelWidth': 100,  // Reduce label width for children (space gain)
                                                   'objectsHideable': Qt.binding(function() { return root.objectsHideable }),
                                                   'filterText': Qt.binding(function() { return root.filterText }),
                                               })
                    obj.Layout.fillWidth = true;
                    obj.attributeDoubleClicked.connect(function(attr) {root.doubleClicked(attr)})
                }
            }
        }

        Component {
            id: colorHueComponent
            RowLayout {
                TextField {
                    implicitWidth: 100
                    enabled: root.editable
                    // Cast value to string to avoid intrusive scientific notations on numbers
                    property string displayValue: String(slider.pressed ? slider.formattedValue : attribute.value)
                    text: displayValue
                    selectByMouse: true
                    validator: DoubleValidator {
                        locale: 'C'  // Use '.' decimal separator disregarding the system locale
                    }
                    onEditingFinished: setTextFieldAttribute(text)
                    onAccepted: setTextFieldAttribute(text)
                    Component.onDestruction: {
                        if (activeFocus)
                            setTextFieldAttribute(text)
                    }
                }
                Rectangle {
                    height: slider.height
                    width: height
                    color: Qt.hsla(slider.pressed ? slider.formattedValue : attribute.value, 1, 0.5, 1)
                }
                Slider {
                    id: slider
                    Layout.fillWidth: true

                    readonly property int stepDecimalCount: 2
                    readonly property real formattedValue: value.toFixed(stepDecimalCount)
                    enabled: root.editable
                    value: attribute.value
                    from: 0
                    to: 1
                    stepSize: 0.01
                    snapMode: Slider.SnapAlways
                    onPressedChanged: {
                        if (!pressed)
                            _reconstruction.setAttribute(attribute, formattedValue)
                    }

                    background: ShaderEffect {
                        width: control.availableWidth
                        height: control.availableHeight
                        blending: false
                        fragmentShader: "qrc:/shaders/AttributeItemDelegate.frag.qsb"
                    }
                }
            }
        }
    }
}
