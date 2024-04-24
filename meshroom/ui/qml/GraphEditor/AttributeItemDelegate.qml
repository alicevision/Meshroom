import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2
import QtQuick.Dialogs 1.3
import MaterialIcons 2.2
import Utils 1.0
import Controls 1.0

/**
  Instantiate a control to visualize and edit an Attribute based on its type.
*/
RowLayout {
    id: root

    property variant attribute: null
    property bool readOnly: false // whether the attribute's value can be modified
    property bool objectsHideable: true
    property string filterText: ""

    property alias label: parameterLabel  // accessor to the internal Label (attribute's name)
    property int labelWidth               // shortcut to set the fixed size of the Label

    readonly property bool editable: !attribute.isOutput && !attribute.isLink && !readOnly

    signal doubleClicked(var mouse, var attr)

    spacing: 2

    function updateAttributeLabel() {
        background.color = attribute.validValue ?  Qt.darker(palette.window, 1.1) : Qt.darker(Colors.red, 1.5)

        if (attribute.desc) {
            var tooltip = ""
            if (!attribute.validValue && attribute.desc.errorMessage !== "")
                tooltip += "<i><b>Error: </b>" + Format.plainToHtml(attribute.desc.errorMessage) + "</i><br><br>"
            tooltip += "<b> " + attribute.desc.name + "</b><br>" + Format.plainToHtml(attribute.desc.description)

            parameterTooltip.text = tooltip
        }
    }

    Pane {
        background: Rectangle {
            id: background
            color: object.validValue ? Qt.darker(parent.palette.window, 1.1) : Qt.darker(Colors.red, 1.5)
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
                    if ((object.hasOutputConnections || object.isLink) && !object.enabled) return Colors.lightgrey
                    else return palette.text
                }

                // Tooltip hint with attribute's description
                ToolTip {
                    id: parameterTooltip

                    text: {
                        var tooltip = ""
                        if (!object.validValue && object.desc.errorMessage !== "")
                            tooltip += "<i><b>Error: </b>" + Format.plainToHtml(object.desc.errorMessage) + "</i><br><br>"
                        tooltip += "<b>" + object.desc.name + "</b><br>" + Format.plainToHtml(object.desc.description)
                        return tooltip
                    }
                    visible: parameterMA.containsMouse
                    delay: 800
                }

                // make label bold if attribute's value is not the default one
                font.bold: !object.isOutput && !object.isDefault

                // make label italic if attribute is a link
                font.italic: object.isLink

                MouseArea {
                    id: parameterMA
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.AllButtons
                    onDoubleClicked: root.doubleClicked(mouse, root.attribute)

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

                    onClicked: {
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
            switch (attribute.type) {
                case "PushButtonParam":
                    return pushButton_component
                case "ChoiceParam":
                    return attribute.desc.exclusive ? comboBox_component : multiChoice_component
                case "IntParam": return slider_component
                case "FloatParam":
                    if (attribute.desc.semantic === 'color/hue')
                        return color_hue_component
                    return slider_component
                case "BoolParam":
                    return checkbox_component
                case "ListAttribute":
                    return listAttribute_component
                case "GroupAttribute":
                    return groupAttribute_component
                case "StringParam":
                    if (attribute.desc.semantic === 'multiline')
                        return textArea_component
                    return textField_component
                case "ColorParam":
                    return color_component
                default:
                    return textField_component
            }
        }

        Component {
            id: pushButton_component
            Button {
                text: attribute.desc.label
                enabled: root.editable
                onClicked: {
                    attribute.clicked()
                }
            }
        }

        Component {
            id: textField_component
            TextField {
                readOnly: !root.editable
                text: attribute.value
                selectByMouse: true
                onEditingFinished: setTextFieldAttribute(text)
                onAccepted: {
                    setTextFieldAttribute(text)
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

        Component {
            id: textArea_component

            Rectangle {
                // Fixed background for the flickable object
                color: palette.base
                width: parent.width
                height: 70

                Flickable {
                    width: parent.width
                    height: parent.height
                    contentWidth: width
                    contentHeight: height

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AlwaysOn
                    }

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
            id: color_component
            RowLayout {
                CheckBox {
                    id: color_checkbox
                    Layout.alignment: Qt.AlignLeft
                    checked: node && node.color === "" ? false : true
                    text: "Custom Color"
                    onClicked: {
                        if (checked) {
                            _reconstruction.setAttribute(attribute, "#0000FF")
                        } else {
                            _reconstruction.setAttribute(attribute, "")
                        }
                    }
                }
                TextField {
                    id: colorText
                    Layout.alignment: Qt.AlignLeft
                    implicitWidth: 100
                    enabled: color_checkbox.checked
                    visible: enabled
                    text: enabled ? attribute.value : ""
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
                    visible: color_checkbox.checked
                    color: color_checkbox.checked ? attribute.value : ""

                    MouseArea {
                        anchors.fill: parent
                        onClicked: colorDialog.open()
                    }
                }

                ColorDialog {
                    id: colorDialog
                    title: "Please choose a color"
                    color: attribute.value
                    onAccepted: {
                        colorText.text = color
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
            id: comboBox_component

            FilterComboBox {
                inputModel: attribute.values

                Component.onCompleted: {
                    // if value not in list, override the text and precise it is not valid
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
                        // when reset, clear and find the current index
                        // but if only reopen the combo box, keep the current value
                        
                        //convert all values of desc values as string
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
            id: multiChoice_component
            Flow {
                Repeater {
                    id: checkbox_repeater
                    model: attribute.desc.values
                    delegate: CheckBox {
                        enabled: root.editable
                        text: modelData
                        checked: attribute.value.indexOf(modelData) >= 0
                        onToggled: {
                            var t = attribute.value
                            if (!checked) {
                                t.splice(t.indexOf(modelData), 1) // remove element
                            } else {
                                t.push(modelData) // add element
                            }
                            _reconstruction.setAttribute(attribute, t)
                        }
                    }
                }
            }
        }

        Component {
            id: slider_component
            RowLayout {
                TextField {
                    IntValidator {
                        id: intValidator
                    }
                    DoubleValidator {
                        id: doubleValidator
                        locale: 'C'  // use '.' decimal separator disregarding the system locale
                    }
                    implicitWidth: 100
                    Layout.fillWidth: !slider.active
                    enabled: root.editable
                    // cast value to string to avoid intrusive scientific notations on numbers
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
            id: checkbox_component
            Row {
                CheckBox {
                    enabled: root.editable
                    checked: attribute.value
                    onToggled: _reconstruction.setAttribute(attribute, !attribute.value)
                }
            }
        }

        Component {
            id: listAttribute_component
            ColumnLayout {
                id: listAttribute_layout
                width: parent.width
                property bool expanded: false
                RowLayout {
                    spacing: 4
                    ToolButton {
                        text: listAttribute_layout.expanded  ? MaterialIcons.keyboard_arrow_down : MaterialIcons.keyboard_arrow_right
                        font.family: MaterialIcons.fontFamily
                        onClicked: listAttribute_layout.expanded = !listAttribute_layout.expanded
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
                    model: listAttribute_layout.expanded ? attribute.value : undefined
                    visible: model !== undefined && count > 0
                    implicitHeight: Math.min(contentHeight, 300)
                    Layout.fillWidth: true
                    Layout.margins: 4
                    clip: true
                    spacing: 4

                    ScrollBar.vertical: ScrollBar { id: sb }

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
            id: groupAttribute_component
            ColumnLayout {
                id: groupItem
                Component.onCompleted:  {
                    var cpt = Qt.createComponent("AttributeEditor.qml");
                    var obj = cpt.createObject(groupItem,
                                               {
                                                   'model': Qt.binding(function() { return attribute.value }),
                                                   'readOnly': Qt.binding(function() { return root.readOnly }),
                                                   'labelWidth': 100, // reduce label width for children (space gain)
                                                   'objectsHideable': Qt.binding(function() { return root.objectsHideable }),
                                                   'filterText': Qt.binding(function() { return root.filterText }),
                                               })
                    obj.Layout.fillWidth = true;
                    obj.attributeDoubleClicked.connect(function(attr) {root.doubleClicked(attr)})
                }
            }
        }

        Component {
            id: color_hue_component
            RowLayout {
                TextField {
                    implicitWidth: 100
                    enabled: root.editable
                    // cast value to string to avoid intrusive scientific notations on numbers
                    property string displayValue: String(slider.pressed ? slider.formattedValue : attribute.value)
                    text: displayValue
                    selectByMouse: true
                    validator: DoubleValidator {
                        locale: 'C'  // use '.' decimal separator disregarding the system locale
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
                        fragmentShader: "
                            varying mediump vec2 qt_TexCoord0;
                            vec3 hsv2rgb(vec3 c) {
                                vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
                                vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
                                return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
                            }
                            void main() {
                                gl_FragColor = vec4(hsv2rgb(vec3(qt_TexCoord0.x, 1.0, 1.0)), 1.0);
                            }"
                    }
                }
            }
        }
    }
}
