import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "../styles"

Item {

    id: root

    // logs model
    property variant model: null
    property color titleColor: "#99222222"
    property string titleText: ""
    property bool expanded: false

    anchors.bottom: parent.bottom
    width: parent.width
    height: expanded ? 150 : 25
    z: 9999

    Behavior on height { NumberAnimation {} }
    Behavior on titleColor { ColorAnimation {} }

    function getColor(logType) {
        switch(logType) {
            case 0: return "#FFF"; // debug
            case 1: return "#FFDAA520"; // warning
            case 2: return "red"; // critical
            case 3: return "red"; // fatal
            default: return "#666"; // info
        }
    }

    Timer {
        id: timer
        interval: 3000; running: false; repeat: false
        onTriggered: {
            root.titleColor = "#99222222";
            root.titleText = "";
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: false
            Layout.preferredHeight: 25
            color: "#99222222"
            RowLayout {
                anchors.fill: parent
                anchors.rightMargin: 4
                Text {
                    Layout.fillWidth: true
                    text: root.titleText
                    color: root.titleColor
                    elide: Text.ElideRight
                    wrapMode: Text.WrapAnywhere
                    font.pointSize: 10
                    opacity: root.expanded ? 0: 1
                }
                ToolButton {
                    style: DefaultStyle.microToolButton
                    tooltip: "console output"
                    iconSource: 'qrc:/images/monitor.svg'
                    onClicked: root.expanded = !root.expanded
                }
            }
        }
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.model
            delegate: Rectangle {
                width: parent.width
                height: childrenRect.height
                color: "#99222222"
                RowLayout {
                    Layout.fillHeight: false
                    Layout.preferredHeight: childrenRect.height
                    anchors.margins: 4
                    ToolButton {
                        style: DefaultStyle.microToolButton
                        tooltip: "console output"
                        iconSource: 'qrc:/images/arrow_right_outline.svg'
                    }
                    Text {
                        Layout.fillWidth: true
                        text: modelData.message
                        color: getColor(modelData.type)
                        elide: Text.ElideRight
                        wrapMode: Text.WrapAnywhere
                        font.pointSize: 10
                    }
                }
            }
            spacing: 2
            clip: true
            onModelChanged: {
                if(root.model.length <= 0)
                    return;
                root.titleColor = getColor(root.model[root.model.length-1].type);
                root.titleText = root.model[root.model.length-1].message;
                timer.start();
            }
        }
    }
}
