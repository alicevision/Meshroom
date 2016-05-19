import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Logger 1.0

Rectangle {

    id: root
    color: "transparent"

    // properties
    property bool expanded: false
    property alias view: logview

    // signals & slots
    signal toggle()
    onToggle: expanded = !expanded

    RowLayout {
        anchors.fill: parent
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            ListView {
                id: logview
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: LogModel { id: logmodel }
                delegate: Item {
                    width: parent.width
                    height: 30
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 5
                        Text {
                            text: "#"+index
                            font.pixelSize: Style.text.size.xsmall
                            color: Style.text.color.dark
                        }
                        Text {
                            text: model.message
                            font.pixelSize: Style.text.size.xsmall
                            color: {
                                switch(model.type) {
                                    case Log.DEBUG:
                                        return Style.text.color.debug;
                                    case Log.WARNING:
                                        return Style.text.color.warning;
                                    case Log.CRITICAL:
                                    case Log.FATAL:
                                        return Style.text.color.critical;
                                    case Log.INFO:
                                    default:
                                        return Style.text.color.info;
                                }
                            }
                        }
                        Item { Layout.fillWidth: true } // spacer
                    }
                }
                onCountChanged: {
                    positionViewAtEnd();
                    currentIndex = count - 1;
                }
            }
        }
        ColumnLayout {
            ToolButton {
                iconSource: "qrc:///images/expand.svg"
                onClicked: toggle()
            }
            ToolButton {
                iconSource: "qrc:///images/trash.svg"
                onClicked: logmodel.clear()
                visible: root.expanded
            }
        }
    }
}
