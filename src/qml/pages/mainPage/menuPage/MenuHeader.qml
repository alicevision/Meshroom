import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0

Rectangle {

    color: Style.window.color.xdark

    RowLayout {
        anchors.fill: parent
        spacing: 0
        ToolButton {
            iconSource: "qrc:///images/funnel.svg"
            enabled: false
            checkable: true
            checked: filterTextfield.text != ""
        }
        TextField {
            id: filterTextfield
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: ""
            placeholderText: "filter"
            validator: RegExpValidator {}
            font.pixelSize: Style.text.size.small
            color: Style.text.color.dark
            onTextChanged: currentProject.modelData.setFilterRegexp(text)
        }
    }

}
