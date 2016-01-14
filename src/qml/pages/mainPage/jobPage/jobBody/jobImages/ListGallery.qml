import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import "../../../../../delegates"

Item {

    id: root
    property variant visualModel: null

    ListView {
        id: view
        anchors.fill: parent
        model: visualModel.parts.list
        snapMode: ListView.SnapOneItem
        orientation: Qt.Horizontal
        highlightRangeMode: ListView.StrictlyEnforceRange
        clip: true
        Component.onCompleted: forceActiveFocus()
        onCurrentIndexChanged: {
            if(!moving)
                positionViewAtIndex(currentIndex, ListView.Contain);
        }
    }

    Item {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: 200
        height: 30
        Rectangle {
            anchors.fill: parent
            opacity: 0.6
            color: Style.window.color.xdark
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 4
            anchors.rightMargin: 4
            spacing: 0
            Item { Layout.fillWidth: true } // spacer
            ToolButton {
                iconSource: "qrc:///images/previous.svg"
                onClicked: view.decrementCurrentIndex()
            }
            ToolButton {
                iconSource: "qrc:///images/next.svg"
                onClicked: view.incrementCurrentIndex()
            }
            Item { Layout.fillWidth: true } // spacer
            Text {
                Layout.preferredWidth: 60
                text: (view.currentIndex+1)+"/"+view.count
                font.pixelSize: Style.text.size.small
            }
            Item { Layout.fillWidth: true } // spacer
        }
    }
}
