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
    property int columnIndex: model.column
    property bool readOnly: false
    property string toolTipText: attribute ? attribute.fullLabel : ""

    Pane {
        // anchors.fill: parent
        // Layout: childrenRect.width
        Layout.minimumWidth: loaderComponent.width
        Layout.minimumHeight: loaderComponent.height
        Layout.fillWidth: true
        // color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
        // z: -1
        // border.width: 2
        // border.color: Qt.darker(palette.window, 1.1)
        padding: 0

        hoverEnabled: true

        ToolTip.delay: 10
        ToolTip.timeout: 5000
        ToolTip.visible: hovered
        ToolTip.text: toolTipText

        Rectangle {
            width: parent.width
            height: loaderComponent.height

            color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
            border.width: 2
            border.color: Qt.darker(palette.window, 1.2)

            Loader {
                id: loaderComponent
                sourceComponent: {
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

            width: intrinsicTable.columnWidths[columnIndex]
            horizontalAlignment: TextInput.AlignRight
/*
            Rectangle {
                anchors.fill: parent
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
            }*/

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

            width: intrinsicTable.columnWidths[columnIndex]
            horizontalAlignment: TextInput.AlignRight
/*
            Rectangle {
                anchors.fill: parent
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
            }*/

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
            topInset: 7
            leftInset: 6
            rightInset: 6
            bottomInset: 7

            width: intrinsicTable.columnWidths[columnIndex]

            /*Rectangle {
                anchors.fill: parent
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
            }*/
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
/*
            Rectangle {
                anchors.fill: parent
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
            }*/
        }
    }

    Component {
        id: float_component
        TextInput{
            readonly property real formattedValue: model.display.value.toFixed(2)
            property string displayValue: String(formattedValue)
            text: displayValue
            color: 'white'
            padding: 12
            selectByMouse: true
            selectionColor: 'white'
            selectedTextColor: Qt.darker(palette.window, 1.1)
            enabled: !readOnly

            width: intrinsicTable.columnWidths[columnIndex]
            horizontalAlignment: TextInput.AlignRight
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
/*
            Rectangle {
                anchors.fill: parent
                color: rowIndex % 2 ? palette.window : Qt.darker(palette.window, 1.1)
                z: -1
                border.width: 2
                border.color: Qt.darker(palette.window, 1.1)
                ToolTip.text: "HELLOOOOO"
                ToolTip.visible: true
            }*/
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
