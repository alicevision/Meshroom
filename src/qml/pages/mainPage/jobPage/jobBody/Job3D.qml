import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Meshroom.GL 0.1

Item {

    DropArea {
        anchors.fill: parent
        hideBackground: true
        onDropped: glview.loadAlembicScene(drop.urls[0])
        GLView {
            id: glview
            anchors.fill: parent
            color: "#333"
            property variant job: currentJob
            onJobChanged: glview.loadAlembicScene(Qt.resolvedUrl(currentJob.url+"/"+currentJob.name+".abc"))
            Slider {
                onValueChanged: {
                    glview.setVisibilityThreshold(value)
                }
            }
        }
    }

}
