import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Meshroom.Enums 0.1
import "../../../../delegates"

Rectangle {

    id : root

    color: Style.window.color.normal
    enabled: currentJob.status == Job.NOTSTARTED

    ScrollView {
        anchors.fill: parent
        ListView {
            anchors.margins: 10
            model: currentJob.steps
            spacing: 5
            interactive: false
            delegate: StepDelegate {}
        }
    }
}
