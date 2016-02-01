import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0


Item {

    id: root
    property variant modelData: model

    width: ListView.view.width
    height: steptitle.height + paramlist.height

    Column {
        anchors.fill: parent
        Item {
            id: steptitle
            height: (index == 0) ? 30 : 40
            width: parent.width
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
                    horizontalAlignment: Text.AlignRight
                }
                Item { Layout.fillHeight: true } // spacer
            }
        }
        ListView {
            id: paramlist
            width: parent.width
            height: contentItem.height
            model: modelData.attributes
            interactive: false
            delegate: ControlDelegate {}
        }
    }
}
