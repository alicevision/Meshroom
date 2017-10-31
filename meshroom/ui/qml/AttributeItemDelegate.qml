import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2

/**
  Instantiate a control to visualize and edit an Attribute based on its type.
*/
Loader {
    id: root
    property variant attribute: null

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
            text: attribute.value
            readOnly: attribute.isOutput || attribute.isLink
            selectByMouse: true
            onEditingFinished: _reconstruction.setAttribute(attribute, text.trim())
        }
    }

    Component {
        id: comboBox_component
        ComboBox {
            model: attribute.desc.values
            enabled: !attribute.isOutput && !attribute.isLink
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
            Slider {
                id: s
                Layout.fillWidth: true
                value: attribute.value
                // TODO: range from desc

                onPressedChanged: {
                    if(!pressed)
                        _reconstruction.setAttribute(attribute, value)
                }
            }
            IntValidator {
                id: intValidator
            }
            DoubleValidator {
                id: doubleValidator
            }
            TextField {
                text: attribute.value
                selectByMouse: true
                validator: attribute.type == "FloatParam" ? doubleValidator : intValidator
                onEditingFinished: _reconstruction.setAttribute(attribute, text)
            }
        }
    }

    Component {
        id: checkbox_component
        Row {
            CheckBox {
                checked: attribute.value
                onToggled: _reconstruction.setAttribute(attribute, !attribute.value)
            }
        }
    }

    Component {
        id: listAttribute_component
        RowLayout {
            width: parent.width
            Label {
                Layout.alignment: Qt.AlignTop
                text: attribute.value.count + " elements"
            }
            Button {
                Layout.alignment: Qt.AlignTop
                text: "+"
                onClicked: _reconstruction.appendAttribute(attribute, undefined)
            }
            ListView {
                id: lv
                model: attribute.value
                implicitHeight: childrenRect.height
                Layout.fillWidth: true

                delegate:  RowLayout {
                    id: item
                    property var childAttrib: object
                    layoutDirection: Qt.RightToLeft
                    //height: childrenRect.height
                    width: lv.width
                    Component.onCompleted: {
                        var cpt = Qt.createComponent("AttributeItemDelegate.qml")
                        var obj = cpt.createObject(item, {'attribute': Qt.binding(function() { return item.childAttrib })})
                        obj.Layout.fillWidth = true
                    }
                    Button {
                        text: "-"
                        onClicked: _reconstruction.removeAttribute(item.childAttrib)
                    }
                }
            }
        }
    }

    Component {
        id: groupAttribute_component
        ListView {
            id: someview
            model: attribute.value
            implicitWidth: parent.width
            implicitHeight: childrenRect.height
            onCountChanged: forceLayout()
            spacing: 4

            delegate: RowLayout {
                id: row
                width: someview.width
                //height: childrenRect.height
                property var childAttrib: object

                Label { text: childAttrib.name }
                Component.onCompleted:  {
                    var cpt = Qt.createComponent("AttributeItemDelegate.qml")
                    var obj = cpt.createObject(row, {'attribute': Qt.binding(function() { return row.childAttrib })})
                    obj.Layout.fillWidth = true
                }
            }
        }
    }

}
