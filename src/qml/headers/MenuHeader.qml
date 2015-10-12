import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.2

import "../components"

Rectangle {

    id: root

    implicitHeight: 30
    color: _style.window.color.xdarker

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        spacing: 0
        CustomToolButton {
            iconSource: "qrc:///images/funnel.svg"
            iconSize: _style.icon.size.small
            enabled: false
            opacity: 0.5
        }
        CustomTextField {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: ""
            placeholderText: "filter"
            validator: RegExpValidator {}
            textSize: _style.text.size.small
            color: _style.text.color.darker
            onEditingFinished: {
                for(var i=0; i<_applicationModel.projects.count; ++i) {
                    var project = _applicationModel.projects.data(_applicationModel.projects.index(i, 0), 261);
                    project.setFilterRegexp(text);
                }
            }
        }
    }
}
