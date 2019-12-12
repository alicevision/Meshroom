import QtQuick 2.11
import AliceVision 1.0 as AliceVision
import QtQuick.Controls 2.0

Item {
    id: root
    property url source
    property double gamma
    property double offset

    AliceVision.FloatImageViewer {
        id: nativeViewer
        anchors.fill: parent
        source: root.source
        gamma: gammaSlider.value
        offset: offsetSlider.value
        clearBeforeLoad: false
    }
    Slider {
        id: offsetSlider
        width: parent.width
        anchors.verticalCenter: parent.verticalCenter
    }
    Slider {
        id: gammaSlider
        width: parent.width
        value: 1
        from: 0
        to: 5
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: 50
    }
}
