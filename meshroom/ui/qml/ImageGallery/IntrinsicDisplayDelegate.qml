import QtQuick 2.9
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.2
import MaterialIcons 2.2
import Utils 1.0

RowLayout {
    id: root

    Layout.fillWidth: true

    property variant attribute: model.display
    property int rowIndex: model.row
    property bool readOnly: false

    Loader {
        Layout.fillWidth: true

        sourceComponent: {
            //console.warn("keys " + Object.keys(intrinsicModel.columns[model.index]))
            //console.warn("index " + intrinsicModel.columnCount)
            //console.warn("HEEELPPP " + model.display.desc.values)
            //console.warn("Object   " + intrinsicModel.columns[model.index].display)
            switch(model.display.type)
            {
               case "ChoiceParam": return choice_component
               case "IntParam": return int_component
               case "FloatParam": return float_component
               case "BoolParam": return bool_component
               case "StringParam": return textField_component
               default: return textField_component
            }
        }
    }

    Component {
        id: textField_component
        TextInput{
            text: model.display.value
            color: 'white'
            padding: 12
            selectByMouse: true
            selectionColor: 'white'
            selectedTextColor: Qt.darker(palette.window, 1.1)


            Rectangle {
                anchors.fill: parent
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
            }

            onEditingFinished: _reconstruction.setAttribute(attribute, text)
            onAccepted: {
                _reconstruction.setAttribute(attribute, text)
            }
            Component.onDestruction: {
                if(activeFocus)
                    _reconstruction.setAttribute(attribute, text)
            }
        }
    }

    Component {
        id: int_component
        TextInput{
            text: model.display.value
            color: 'white'
            padding: 12
            selectByMouse: true
            selectionColor: 'white'
            selectedTextColor: Qt.darker(palette.window, 1.1)

            IntValidator {
                id: intValidator
            }

            validator: intValidator

            Rectangle {
                anchors.fill: parent
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
            }

            onEditingFinished: _reconstruction.setAttribute(attribute, Number(text))
            onAccepted: {
                _reconstruction.setAttribute(attribute, Number(text))
            }
            Component.onDestruction: {
                if(activeFocus)
                    _reconstruction.setAttribute(attribute, Number(text))
            }
        }
    }

    Component {
        id: choice_component
        ComboBox {
            id: combo
            model: attribute.desc.values
            Component.onCompleted: currentIndex = find(attribute.value)
            onActivated: _reconstruction.setAttribute(attribute, currentText)
            flat : true
            Rectangle {
                anchors.fill: parent
                //height : combo.height
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
            }
            Connections {
                target: attribute
                onValueChanged: combo.currentIndex = combo.find(attribute.value)
            }
        }
    }

    Component {
        id: bool_component
        CheckBox {
            checked: attribute ? attribute.value : false
            padding: 12
            onToggled: _reconstruction.setAttribute(attribute, !attribute.value)
            Rectangle {
                anchors.fill: parent
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
            }
        }
    }

    Component {
        id: float_component
        TextInput{
            //readonly property int stepDecimalCount: stepSize <  1 ? String(stepSize).split(".").pop().length : 0
            readonly property real formattedValue: model.display.value.toFixed(2)
            property string displayValue: String(formattedValue)
            text: displayValue
            color: 'white'
            padding: 12
            selectByMouse: true
            selectionColor: 'white'
            selectedTextColor: Qt.darker(palette.window, 1.1)
            enabled: !readOnly

            clip: true;

            autoScroll: activeFocus

            //Use this function to ensure the left part is visible
            //while keeping the trick for formatting the text
            //Timing issues otherwise
            onActiveFocusChanged: {
                if(activeFocus) text = String(model.display.value)
                else text = String(formattedValue)
                cursorPosition = 0
            }

            DoubleValidator {
                id: doubleValidator
                locale: 'C'  // use '.' decimal separator disregarding the system locale
            }

            validator: doubleValidator

            Rectangle {
                anchors.fill: parent
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
            }
            onEditingFinished: _reconstruction.setAttribute(attribute, Number(text))
            onAccepted: {
                _reconstruction.setAttribute(attribute, Number(text))
            }
            Component.onDestruction: {
                if(activeFocus)
                    _reconstruction.setAttribute(attribute, Number(text))
            }
        }
    }




}
