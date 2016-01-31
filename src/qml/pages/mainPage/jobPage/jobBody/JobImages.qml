import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import ImageGallery 1.0
import Meshroom.Job 0.1

Rectangle {

    id: root
    color: Style.window.color.normal

    Gallery {
        anchors.fill: parent
        model: currentJob.images
        editable: currentJob.status == Job.NOTSTARTED
    }
}
