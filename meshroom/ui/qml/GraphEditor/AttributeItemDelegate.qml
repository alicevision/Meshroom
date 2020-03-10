import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2
import MaterialIcons 2.2
import Utils 1.0

/**
  Instantiate a control to visualize and edit an Attribute based on its type.
*/
RowLayout {
    id: root

    property variant attribute: null
    property bool readOnly: false // whether the attribute's value can be modified

    property alias label: parameterLabel  // accessor to the internal Label (attribute's name)
    property int labelWidth               // shortcut to set the fixed size of the Label

    readonly property bool editable: !attribute.isOutput && !attribute.isLink && !readOnly

    signal doubleClicked(var mouse, var attr)

    spacing: 2


    Pane {
        background: Rectangle { color: Qt.darker(parent.palette.window, 1.1) }
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

                text: attribute.label

                // Tooltip hint with attribute's description
                ToolTip.text: "<b>" + object.desc.name + "</b><br>" + Format.plainToHtml(object.desc.description)
                ToolTip.visible: parameterMA.containsMouse
                ToolTip.delay: 800

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

                        property bool isFileAttribute: attribute.type == "File"
                        property bool isFilepath: isFileAttribute && Filepath.isFile(attribute.value)

                        MenuItem {
                            text: "Reset To Default Value"
                            enabled: root.editable && !attribute.isDefault
                            onTriggered: _reconstruction.resetAttribute(attribute)
                        }

                        MenuSeparator {
                            visible: paramMenu.isFileAttribute
                            height: visible ? implicitHeight : 0
                        }

                        MenuItem {
                            visible: paramMenu.isFileAttribute
                            height: visible ? implicitHeight : 0
                            text: paramMenu.isFilepath ? "Open Containing Folder" : "Open Folder"
                            onClicked: paramMenu.isFilepath ? Qt.openUrlExternally(Filepath.dirname(attribute.value)) :
                                                              Qt.openUrlExternally(Filepath.stringToUrl(attribute.value))
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
                        if(mouse.button == Qt.RightButton)
                        {
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

    function setTextFieldAttribute(value)
    {
        // editingFinished called even when TextField is readonly
        if(!editable)
            return
        switch(attribute.type)
        {
        case "IntParam":
        case "FloatParam":
            _reconstruction.setAttribute(root.attribute, Number(value))
            break;
        case "File":
            _reconstruction.setAttribute(root.attribute, value)
            break;
        default:
            _reconstruction.setAttribute(root.attribute, value.trim())
        }
    }

    Loader {
        Layout.fillWidth: true

        sourceComponent: {
            switch(attribute.type)
            {
            case "ChoiceParam": return attribute.desc.exclusive ? comboBox_component : multiChoice_component
            case "IntParam": return slider_component
            case "FloatParam": return slider_component
            case "BoolParam": return checkbox_component
            case "ListAttribute": return listAttribute_component
            case "GroupAttribute": return groupAttribute_component
            default: return textField_component
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
                    if(activeFocus)
                        setTextFieldAttribute(text)
                }
                DropArea {
                    enabled: root.editable
                    anchors.fill: parent
                    onDropped: {
                        if(drop.hasUrls)
                            setTextFieldAttribute(Filepath.urlToString(drop.urls[0]))
                        else if(drop.hasText && drop.text != '')
                            setTextFieldAttribute(drop.text)
                    }
                }
            }
        }

        Component {
            id: comboBox_component
            ComboBox {
                id: combo
                enabled: root.editable
                model: attribute.desc.values
                Component.onCompleted: currentIndex = find(attribute.value)
                onActivated: _reconstruction.setAttribute(attribute, currentText)
                Connections {
                    target: attribute
                    onValueChanged: combo.currentIndex = combo.find(attribute.value)
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
                            if(!checked) { t.splice(t.indexOf(modelData), 1) } // remove element
                            else { t.push(modelData) }                         // add element
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
                    validator: attribute.type == "FloatParam" ? doubleValidator : intValidator
                    onEditingFinished: setTextFieldAttribute(text)
                    onAccepted: {
                        setTextFieldAttribute(text)
                        // When the text is too long, display the left part
                        // (with the most important values and cut the floating point details)
                        ensureVisible(0)
                    }
                    Component.onDestruction: {
                        if(activeFocus)
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
                            if(!pressed)
                                _reconstruction.setAttribute(attribute, formattedValue)
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
                    visible: model != undefined && count > 0
                    implicitHeight: Math.min(contentHeight, 300)
                    Layout.fillWidth: true
                    Layout.margins: 4
                    clip: true
                    spacing: 4

                    ScrollBar.vertical: ScrollBar { id: sb }

                    delegate:  RowLayout {
                        id: item
                        property var childAttrib: object
                        layoutDirection: Qt.RightToLeft
                        width: lv.width - sb.width
                        Component.onCompleted: {
                            var cpt = Qt.createComponent("AttributeItemDelegate.qml")
                            var obj = cpt.createObject(item,
                                                       {'attribute': Qt.binding(function() { return item.childAttrib }),
                                                        'readOnly': Qt.binding(function() { return !root.editable })
                                                       })
                            obj.Layout.fillWidth = true
                            obj.label.text = index
                            obj.label.horizontalAlignment = Text.AlignHCenter
                            obj.label.verticalAlignment = Text.AlignVCenter
                            obj.doubleClicked.connect(function(attr) {root.doubleClicked(attr)})
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

        Component {
            id: groupAttribute_component
            ColumnLayout {
                id: groupItem
                Component.onCompleted:  {
                    var cpt = Qt.createComponent("AttributeEditor.qml");
                    var obj = cpt.createObject(groupItem,
                                               {'attributes': Qt.binding(function() { return attribute.value }),
                                                'readOnly': Qt.binding(function() { return root.readOnly }),
                                                'labelWidth': 100, // reduce label width for children (space gain)
                                               })
                    obj.Layout.fillWidth = true;
                    obj.attributeDoubleClicked.connect(function(attr) {root.doubleClicked(attr)})
                }
            }
        }
    }
}
