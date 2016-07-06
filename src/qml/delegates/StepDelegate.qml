import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0


Item {

    id: root
    property variant modelData: model

    width: ListView.view.width
    height: steptitle.height + paramlist.contentHeight + 20

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Item {
            id: steptitle
            Layout.preferredHeight: (index == 0) ? 30 : 40
            Layout.fillWidth: true
            ColumnLayout {
                width: parent.width
                height: parent.height
                Item { Layout.fillHeight: true } // spacer
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    visible: index != 0
                    color: Style.window.color.light
                }
                Text {
                    Layout.fillWidth: true
                    text: modelData.name
                    font.pixelSize: Style.text.size.small
                    color: Style.text.color.dark
                    horizontalAlignment: Text.AlignLeft
                }
                Item { Layout.fillHeight: true } // spacer
            }
        }
        ListView {
            id: paramlist
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: modelData.attributes
            interactive: false
            delegate: ControlDelegate {
                onShowTooltip: {
                    tooltipTxt.text = text;
                    tooltipContainer.opacity = 1;
                }
            }
            spacing: 10
        }
    }
    Rectangle {
        id: tooltipContainer
        anchors.fill: parent
        color: Style.window.color.xdark
        opacity: 0
        Behavior on opacity { NumberAnimation{} }
        MouseArea {
            anchors.fill: parent
            visible: tooltipContainer.opacity > 0
            hoverEnabled: true
            ToolButton {
                anchors.horizontalCenter: parent.right
                anchors.verticalCenter: parent.top
                iconSource: "qrc:///images/close.svg"
                opacity: (hovered || parent.containsMouse) ? 1 : 0
                Behavior on opacity { NumberAnimation {}}
                onClicked: tooltipContainer.opacity = 0
            }
            ScrollView {
                id: scrollview
                anchors.fill: parent
                anchors.margins: 2
                Text {
                    id: tooltipTxt
                    width: scrollview.width - 4
                    text: ""
                    font.pixelSize: Style.text.size.xsmall
                    wrapMode: Text.WordWrap
                    maximumLineCount: 100
                }
            }
        }
    }

}
