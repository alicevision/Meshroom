import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Dialogs

import MaterialIcons 2.2
import Utils 1.0
import Controls 1.0
import "AttributeControls" as AttributeControls

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

    readonly property bool editable: !attribute.isOutput && !attribute.isLink &&
                                     !readOnly && !(attribute.keyable && _currentScene.selectedViewId === "-1")
    property var errorMessages: attribute.errorMessages

    signal doubleClicked(var mouse, var attr)
    signal inAttributeClicked(var srcItem, var mouse, var inAttributes)
    signal outAttributeClicked(var srcItem, var mouse, var outAttributes)
    signal showInViewer(var attr)

    Connections {
        target: attribute
        function onValueChanged() {
            root.errorMessages = attribute.errorMessages
        }
    }

    spacing: 2

    Pane {
        visible: attribute.type !== "GroupAttribute"
        background: Rectangle {
            id: background
            color: Qt.darker(parent.palette.window, 1.1)
        }
        padding: 0
        Layout.preferredWidth: labelWidth || implicitWidth
        Layout.fillHeight: true

        RowLayout {
            spacing: 0
            width: parent.width
            height: parent.height

            // In connection
            MaterialToolButton {
                id: navButtonIn

                property bool shouldBeVisible: (object != undefined && object.hasAnyInputLinks)

                text: MaterialIcons.login
                enabled: shouldBeVisible
                font.pointSize: 8
                Layout.fillHeight: true
                visible: shouldBeVisible

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton

                    onClicked: function(mouse) {
                        root.inAttributeClicked(navButtonIn, mouse, object.allInputLinks)
                    }
                }

            }

            Label {
                id: parameterLabel

                Layout.fillHeight: true
                Layout.fillWidth: true
                horizontalAlignment: attribute.isOutput ? Qt.AlignRight : Qt.AlignLeft
                verticalAlignment: Text.AlignVCenter
                elide: Label.ElideRight
                padding: 5
                wrapMode: Label.WrapAtWordBoundaryOrAnywhere

                text: attribute.isMandatory && attribute.isDefault ? `\* ${object.label}` : object.label

                color: {
                    if (object != undefined && (object.hasAnyOutputLinks || object.isLink) && !object.enabled)
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
                        return `<b>${object.desc.name}:</b> ${attribute.type}<br>${Format.plainToHtml(object.desc.description)}`
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
                    onDoubleClicked: function(mouse) { root.doubleClicked(mouse, root.attribute) }

                    property Component menuComp: Menu {
                        id: paramMenu

                        property bool isFileAttribute: attribute.type === "File"
                        property bool isFilepath: isFileAttribute && Filepath.isFile(attribute.evalValue)

                        MenuItem {
                            text: "Reset To Default Value"
                            enabled: root.editable && !attribute.isDefault
                            onTriggered: {
                                _currentScene.resetAttribute(attribute)
                            }
                        }
                        MenuItem {
                            text: "Copy"
                            enabled: !attribute.keyable && attribute.value != ""
                            onTriggered: {
                                Clipboard.clear()
                                Clipboard.setText(attribute.value)
                            }
                        }
                        MenuItem {
                            text: "Paste"
                            enabled: Clipboard.getText() != "" && !attribute.keyable && root.editable
                            onTriggered: {
                                _currentScene.setAttribute(attribute, Clipboard.getText())
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
                            onClicked: Qt.openUrlExternally(Filepath.stringToUrl(attribute.evalValue))
                        }

                        MenuItem { 
                            visible: attribute.isOutput && (attribute.is2dDisplayable || attribute.is3dDisplayable || attribute.isTextDisplayable)
                            height: visible ? implicitHeight : 0
                            text: {
                                if (attribute.is2dDisplayable)
                                    return "Show in 2D Viewer"
                                if (attribute.isTextDisplayable)
                                    return "Show in Text Viewer"
                                return "Show in 3D Viewer"
                            }
                            onClicked: root.showInViewer(attribute)
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
                property bool isDisplayable: attribute.isOutput && (attribute.is2dDisplayable || attribute.is3dDisplayable || attribute.isTextDisplayable)
                property bool isDisplayed: attribute === _currentScene.displayedAttr2D || _currentScene.displayedAttrs3D.count && _currentScene.displayedAttrs3D.contains(attribute)
                text: isDisplayed ? MaterialIcons.visibility : MaterialIcons.visibility_off
                enabled: isDisplayed
                visible: isDisplayable
                ToolTip.text: {
                    if (attribute.is2dDisplayable)
                        return "This attribute is displayable in the 2D viewer."
                    if (attribute.isTextDisplayable)
                        return "This attribute is displayable in the Text viewer."
                    return "This attribute is displayable in the 3D viewer."
                }

                padding: 4
                font.pointSize: 8
            }

            MaterialToolButton {
                id: navButtonOut

                property bool shouldBeVisible: (attribute != undefined && attribute.hasAnyOutputLinks)

                text: MaterialIcons.logout
                font.pointSize: 8
                enabled: shouldBeVisible
                Layout.fillHeight: true
                visible: shouldBeVisible

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton

                    onClicked: function(mouse) {
                        root.outAttributeClicked(navButtonOut, mouse, attribute.allOutputLinks)
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
                // We do not set a number because we want to keep the invalid expression
                if(attribute.keyable)
                    _currentScene.addAttributeKeyValue(root.attribute, _currentScene.selectedViewId, Number(value))
                else
                    _currentScene.setAttribute(root.attribute, Number(value))
                break
            case "File":
                _currentScene.setAttribute(root.attribute, value)
                break
            default:
                _currentScene.setAttribute(root.attribute, value.trim())
                break
        }
    }


    Loader {
        Layout.fillWidth: true
        id: inputField

        sourceComponent: {
            // PushButtonParam always has value == undefined, so it needs to be excluded from this check
            if (attribute.type != "PushButtonParam" && !attribute.keyable && attribute.value === undefined) {
                return notComputedComponent
            }
            switch (attribute.type) {
                case "PushButtonParam":
                    return pushButtonComponent
                case "ChoiceParam":
                    return attribute.desc.exclusive ? choiceComponent : choiceMultiComponent
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

            RowLayout {
                anchors.fill: parent

                TextField {
                    id: textField
                    Layout.fillWidth: true

                    readOnly: !root.editable
                    text: attribute.value
                    placeholderText: attribute.isMandatory ? "This field is required" : ""
                    placeholderTextColor: "gray"
                    // Don't disable the component to keep interactive features (text selection, context menu...).
                    // Only override the look by using the Disabled palette.
                    SystemPalette {
                        id: disabledPalette
                        colorGroup: SystemPalette.Disabled
                    }

                    background: Rectangle {
                        border.color: errorMessages.length ? "orange" : "transparent"
                        color:  Qt.darker(palette.window, 1.2)
                        radius: 2
                    }

                    states: [
                        State {
                            when: readOnly
                            PropertyChanges {
                                target: textField
                                color: disabledPalette.text
                            }
                        }
                    ]

                    selectByMouse: true
                    persistentSelection: false

                    onEditingFinished: {
                        setTextFieldAttribute(text)
                    }

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
                    onPressed: (event) => {
                        if (event.button == Qt.RightButton) {
                            // Keep selection persistent while context menu is open to
                            // visualize what is being copied or what will be replaced on paste.
                            persistentSelection = true
                            const menu = textFieldMenuComponent.createObject(textField)
                            menu.popup()

                            if (selectedText === "") {
                                cursorPosition = positionAt(event.x, event.y)
                            }
                        }
                    }

                    Component {
                        id: textFieldMenuComponent
                        Menu {
                            onOpened: {
                                // Keep cursor visible to see where pasting would happen.
                                textField.cursorVisible = true
                            }
                            onClosed: {
                                // Disable selection persistency behavior once menu is closed and
                                // give focus back to the parent TextField.
                                textField.persistentSelection = false
                                textField.forceActiveFocus()
                                destroy()
                            }
                            MenuItem {
                                text: "Copy"
                                enabled: attribute.value != ""
                                onTriggered: {
                                    const hasSelection = textField.selectionStart !== textField.selectionEnd
                                    if (hasSelection) {
                                        // Use `TextField.copy` to copy only the current selection.
                                        textField.copy()
                                    }
                                    else {
                                        Clipboard.setText(attribute.value)
                                    }
                                }
                            }
                            MenuItem {
                                text: "Paste"
                                enabled: !readOnly
                                onTriggered: {
                                    const clipboardText = Clipboard.getText()
                                    if (clipboardText.length === 0) {
                                        return
                                    }
                                    const before = textField.text.substr(0, textField.selectionStart)
                                    const after = textField.text.substr(textField.selectionEnd, textField.text.length)
                                    const updatedValue = before + clipboardText + after
                                    setTextFieldAttribute(updatedValue)
                                    // Set the cursor at the end of the added text
                                    textField.cursorPosition = before.length + clipboardText.length
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

                        background: Rectangle {
                            visible: errorMessages.length
                            border.color: "orange"
                            color: "transparent"
                            radius: 2
                        }

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
                    checked: attribute.value === "" ? false : true
                    checkable: root.editable
                    text: "Custom Color"
                    property string previousColor: ""
                    onClicked: {
                        if (checked) {
                            if (colorText.text == "") {
                                if (previousColor != "")
                                    _currentScene.setAttribute(attribute, previousColor)
                                else
                                    _currentScene.setAttribute(attribute, "#0000FF")
                            }
                            else
                                _currentScene.setAttribute(attribute, colorText.text)
                        } else {
                            previousColor = attribute.value
                            _currentScene.setAttribute(attribute, "")
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
            id: choiceComponent

            AttributeControls.Choice {
                value: root.attribute.value
                values: root.attribute.values
                enabled: root.editable

                onEditingFinished: (value) => {
                    _currentScene.setAttribute(root.attribute, value)
                }
            }
        }

        Component {
            id: choiceMultiComponent

            AttributeControls.ChoiceMulti {
                value: root.attribute.value
                values: root.attribute.values
                enabled: root.editable
                customValueColor: Colors.orange

                onToggled: (value, checked) => {
                    var currentValue = root.attribute.value;
                    if (!checked) {
                        currentValue.splice(currentValue.indexOf(value), 1);
                    } else {
                        currentValue.push(value);
                    }
                    _currentScene.setAttribute(attribute, currentValue);
                }
            }
        }

        Component {
            id: sliderComponent
            RowLayout {
                ExpressionTextField {
                    id: expressionTextField
                    implicitWidth: 100
                    Layout.fillWidth: !slider.active
                    enabled: root.editable
                    // Cast value to string to avoid intrusive scientific notations on numbers
                    property string displayValue: String(slider.active && slider.item.pressed ? slider.item.formattedValue :
                                                        attribute.keyable ? attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId) :
                                                        attribute.value)
                    text: displayValue
                    selectByMouse: true
                    // Note: Use autoScroll as a workaround for alignment
                    // When the value change keep the text align to the left to be able to read the most important part
                    // of the number. When we are editing (item is in focus), the content should follow the editing.
                    autoScroll: activeFocus
                    isInt: attribute.type === "FloatParam" ? false : true
                    onEditingFinished: {
                        if (!hasExprError) {
                            setTextFieldAttribute(expressionTextField.evaluatedValue)
                            // Restore binding
                            expressionTextField.text = Qt.binding(function() { return String(expressionTextField.displayValue); })
                        }
                    }

                    background: Rectangle {
                            border.color: errorMessages.length ? "orange" : "transparent"
                            color: Qt.darker(palette.window, 1.2)
                            radius: 2
                        }

                    onAccepted: {
                        if (!hasExprError) {
                            setTextFieldAttribute(expressionTextField.evaluatedValue)
                            // Restore binding
                            expressionTextField.text = Qt.binding(function() { return String(expressionTextField.displayValue); })
                        }
                        // When the text is too long, display the left part
                        // (with the most important values and cut the floating point details)
                        ensureVisible(0)
                    }

                    Component.onDestruction: {
                        if (activeFocus) {
                            if (!hasExprError)
                                setTextFieldAttribute(expressionTextField.evaluatedValue)
                        }
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
                        value: attribute.keyable ? attribute.keyValues.getValueAtKeyOrDefault(_currentScene.selectedViewId) : attribute.value
                        from: attribute.desc.range[0]
                        to: attribute.desc.range[1]
                        stepSize: attribute.desc.range[2]
                        snapMode: Slider.SnapAlways

                        onPressedChanged: {
                            if (!pressed) {
                                if (attribute.keyable)
                                    _currentScene.addAttributeKeyValue(attribute, _currentScene.selectedViewId, formattedValue)
                                else
                                    _currentScene.setAttribute(attribute, formattedValue)
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
                        onClicked: _currentScene.appendAttribute(attribute, undefined)
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
                            && (object.hasAnyInputLinks && GraphEditorSettings.showLinkAttributes || !object.hasAnyInputLinks && GraphEditorSettings.showNotLinkAttributes))
                        visible: active
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
                                obj.inAttributeClicked.connect(function(srcItem, mouse, inAttributes) { root.inAttributeClicked(srcItem, mouse, inAttributes) })
                                obj.outAttributeClicked.connect(function(srcItem, mouse, outAttributes) { root.outAttributeClicked(srcItem, mouse, outAttributes) })
                            }
                            ToolButton {
                                enabled: root.editable
                                text: MaterialIcons.remove_circle_outline
                                font.family: MaterialIcons.fontFamily
                                font.pointSize: 11
                                padding: 2
                                ToolTip.text: "Remove Element"
                                ToolTip.visible: hovered
                                onClicked: _currentScene.removeAttribute(item.childAttrib)
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
                spacing: 0
                property bool expanded: true

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 0

                    ToolButton {
                        text: groupItem.expanded ? MaterialIcons.expand_more : MaterialIcons.chevron_right
                        font.family: MaterialIcons.fontFamily
                        font.pointSize: 10
                        padding: 2
                        onClicked: groupItem.expanded = !groupItem.expanded
                    }

                    Label {
                        text: attribute.label
                        font.bold: true
                        font.pointSize: 8
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        padding: 3

                        ToolTip {
                            text: {
                                var tooltip = ""
                                if (attribute.desc)
                                    tooltip += "<b>" + attribute.desc.name + ":</b> " + attribute.type + "<br>" + Format.plainToHtml(attribute.desc.description)
                                return tooltip
                            }
                            visible: labelMA.containsMouse
                            delay: 800
                        }

                        MouseArea {
                            id: labelMA
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: groupItem.expanded = !groupItem.expanded
                            onDoubleClicked: function(mouse) { root.doubleClicked(mouse, root.attribute) }
                        }
                    }
                }

                Component.onCompleted: {
                    var cpt = Qt.createComponent("AttributeEditor.qml");
                    var obj = cpt.createObject(groupItem,
                                               {
                                                   'model': Qt.binding(function() { return attribute.value }),
                                                   'readOnly': Qt.binding(function() { return root.readOnly }),
                                                   'labelWidth': Qt.binding(function() { return root.labelWidth }),
                                                   'objectsHideable': Qt.binding(function() { return root.objectsHideable }),
                                                   'filterText': Qt.binding(function() { return root.filterText }),
                                                   'visible': Qt.binding(function() { return groupItem.expanded }),
                                               })
                    obj.Layout.fillWidth = true;
                    obj.Layout.leftMargin = 8;
                    obj.attributeDoubleClicked.connect(
                        function(mouse, attr) {
                            root.doubleClicked(mouse, attr)
                        }
                    )
                    obj.inAttributeClicked.connect(
                        function(srcItem, mouse, inAttributes) {
                            root.inAttributeClicked(srcItem, mouse, inAttributes)
                        }
                    )
                    obj.outAttributeClicked.connect(
                        function(srcItem, mouse, outAttributes) {
                            root.outAttributeClicked(srcItem, mouse, outAttributes)
                        }
                    )
                    obj.showInViewer.connect(
                        function(attr) {
                            root.showInViewer(attr)
                        }
                    )
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
                            _currentScene.setAttribute(attribute, formattedValue)
                    }

                    background: ShaderEffect {
                        width: slider.availableWidth
                        height: slider.availableHeight
                        blending: false
                        fragmentShader: "qrc:/shaders/AttributeItemDelegate.frag.qsb"
                    }
                }
            }
        }
    }

    MaterialLabel {
        visible: !attribute.isOutput && root.errorMessages.length
        text: MaterialIcons.fmd_bad
        ToolTip.text: root.errorMessages.join("\n")
        color: "orange"
    }

    // Add or remove key button for keyable attribute
    Loader {
        active: attribute.keyable
        sourceComponent: MaterialToolButton {
            font.pointSize: 5
            padding: 6
            text: MaterialIcons.circle
            checkable: true
            checked: attribute.keyable && attribute.keyValues.hasKey(_currentScene.selectedViewId)
            enabled: root.editable
            onClicked: {
                if (attribute.keyValues.hasKey(_currentScene.selectedViewId))
                    _currentScene.removeAttributeKey(attribute, _currentScene.selectedViewId)
                else
                    _currentScene.addAttributeKeyDefaultValue(attribute, _currentScene.selectedViewId)
            }
        }
    }
}
