import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import "jobPage"

Item {

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // header
        JobHeader {
            id: header
            Layout.fillWidth: true
            Layout.preferredHeight: 30
        }

        // body
        JobBody {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

}
