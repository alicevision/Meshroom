import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4
import DarkStyle.Controls 1.0
import Logger 1.0

Item {

    id: root
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    anchors.right: parent.right
    height: 30

    ListView {
        anchors.fill: parent
        model: LogModel {}
        delegate: Item {
            width: parent.width
            height: 20
            Text {
                anchors.fill: parent
                text: model.message
                color: {
                    switch(model.type)
                    {
                    case Log.DEBUG:
                        return "green";
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
        }
    }
}
