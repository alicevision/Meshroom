import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Logger 1.0

Rectangle {

    id: root

    signal toggle()

    color: "transparent"

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 4
        spacing: 0
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: LogModel { id: logmodel }
            delegate: Item {
                width: parent.width
                height: 30
                RowLayout {
                    anchors.fill: parent
                    Text {
                        text: index
                        font.pixelSize: Style.text.size.xsmall
                    }
                    Text {
                        text: model.message
                        font.pixelSize: Style.text.size.xsmall
                        color: {
                            switch(model.type) {
                            case Log.DEBUG:
                                return "darkgrey";
                            case Log.WARNING:
                                return "orange";
                            case Log.CRITICAL:
                            case Log.FATAL:
                                return "red";
                            case Log.INFO:
                            default:
                                return "grey";
                            }
                        }
                    }
                    Item { Layout.fillWidth: true } // spacer
                }
            }
            clip: true
            onCountChanged: {
                positionViewAtEnd();
                currentIndex = count - 1;
            }
        }
        ColumnLayout {
            ToolButton {
                iconSource: "qrc:///images/expand.svg"
                onClicked: toggle()
            }
            // ToolButton {
            //     iconSource: "qrc:///images/disk.svg"
            //     onClicked: logmodel.clear()
            // }
        }
    }
}
