import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2
import MaterialIcons 2.2
import "../filepath.js" as Filepath

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

    spacing: 4

    Label {
        id: parameterLabel

        Layout.preferredWidth: labelWidth || implicitWidth
        Layout.fillHeight: true
        horizontalAlignment: attribute.isOutput ? Qt.AlignRight : Qt.AlignLeft
        elide: Label.ElideRight
        padding: 5
        wrapMode: Label.WrapAtWordBoundaryOrAnywhere

        text: attribute.label

        // Tooltip hint with attribute's description
        ToolTip.text: object.desc.description
        ToolTip.visible: parameterMA.containsMouse && object.desc.description
        ToolTip.delay: 800

        // make label bold if attribute's value is not the default one
        font.bold: !object.isOutput && !object.isDefault

        // make label italic if attribute is a link
        font.italic: object.isLink

        background: Rectangle { color: Qt.darker(palette.window, 1.2) }

        MouseArea {
            id: parameterMA
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.AllButtons

            property Component menuComp: Menu {
                id: paramMenu

                property bool isFileAttribute: attribute.type == "File"
                property bool isFilepath: isFileAttribute && Filepath.isFile(attribute.value)

                MenuItem {
                    text: "Reset To Default Value"
                    enabled: !attribute.isOutput && !attribute.isLink && !attribute.isDefault
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
                                                      Qt.openUrlExternally(attribute.value)
                }

                MenuItem {
                    visible: paramMenu.isFilepath
                    height: visible ? implicitHeight : 0
                    text: "Open File"
                    onClicked: Qt.openUrlExternally(attribute.value)
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
            _reconstruction.setAttribute(root.attribute, value.replace("file://", "").trim())
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
                onAccepted: setTextFieldAttribute(text)
                DropArea {
                    enabled: root.editable
                    anchors.fill: parent
                    onDropped: {
                        if(drop.hasUrls)
                            setTextFieldAttribute(drop.urls[0].toLocaleString())
                        else if(drop.hasText && drop.text != '')
                            setTextFieldAttribute(drop.text)
                    }
                }
            }
        }

        Component {
            id: comboBox_component
            ComboBox {
                enabled: root.editable
                model: attribute.desc.values
                Component.onCompleted: currentIndex = find(attribute.value)
                onActivated: _reconstruction.setAttribute(attribute, currentText)
                Connections {
                    target: attribute
                    onValueChanged: currentIndex = find(attribute.value)
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
                    }
                    implicitWidth: 70
                    enabled: root.editable
                    text: s.pressed ? s.value : attribute.value
                    selectByMouse: true
                    validator: attribute.type == "FloatParam" ? doubleValidator : intValidator
                    onEditingFinished: setTextFieldAttribute(text)
                }

                Slider {
                    id: s
                    Layout.fillWidth: true
                    enabled: root.editable
                    value: attribute.value
                    from: attribute.desc.range[0]
                    to: attribute.desc.range[1]
                    stepSize: attribute.desc.range[2]
                    snapMode: Slider.SnapAlways

                    onPressedChanged: {
                        if(!pressed)
                            _reconstruction.setAttribute(attribute, value)
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
                        text: listAttribute_layout.expanded  ? "▾" : "▸"
                        onClicked: listAttribute_layout.expanded = !listAttribute_layout.expanded
                    }
                    Label {
                        anchors.verticalCenter: parent.verticalCenter
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
                    implicitHeight: Math.min(childrenRect.height, 300)
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
                                                        'readOnly': Qt.binding(function() { return root.readOnly })
                                                       })
                            obj.Layout.fillWidth = true
                            obj.label.text = index
                            obj.label.horizontalAlignment = Text.AlignHCenter
                            obj.label.verticalAlignment = Text.AlignVCenter
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
            ListView {
                id: chilrenListView
                model: attribute.value
                implicitWidth: parent.width
                implicitHeight: childrenRect.height
                onCountChanged: forceLayout()
                spacing: 2

                delegate: RowLayout {
                    id: row
                    width: chilrenListView.width
                    property var childAttrib: object

                    Component.onCompleted:  {
                        var cpt = Qt.createComponent("AttributeItemDelegate.qml")
                        var obj = cpt.createObject(row,
                                                   {'attribute': Qt.binding(function() { return row.childAttrib }),
                                                    'readOnly': Qt.binding(function() { return root.readOnly })
                                                   })
                        obj.Layout.fillWidth = true
                        obj.labelWidth = 100 // reduce label width for children (space gain)
                    }
                }
            }
        }
    }
}
