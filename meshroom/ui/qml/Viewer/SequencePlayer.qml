import QtQuick 2.11
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import Controls 1.0

FloatingPane {
    id: root

    property real fps: 4

    function sequence(vps) {
        let objs = []
        for (let i = 0; i < vps.count; i++) {
            objs.push({
                viewId: m.viewpoints.at(i).childAttribute("viewId").value,
                filename: Filepath.basename(m.viewpoints.at(i).childAttribute("path").value)
            });
        }
        objs.sort((a, b) => { return a.filename < b.filename ? -1 : 1; });

        let viewIds = [];
        for (let i = 0; i < objs.length; i++) {
            viewIds.push(objs[i].viewId);
        }

        return viewIds;
    }

    QtObject {
        id: m

        property var currentCameraInit: _reconstruction && _reconstruction.cameraInit ? _reconstruction.cameraInit : undefined
        property var viewpoints: currentCameraInit ? currentCameraInit.attribute('viewpoints').value : undefined
        property var sortedViewIds: viewpoints ? sequence(viewpoints) : []
    }

    Timer {
        id: timer

        repeat: true
        running: false
        interval: 1000 / fps

        onTriggered: {
            viewSlider.value += 1;
        }
    }
    
    RowLayout {

        anchors.fill: parent

        Button {
            id: prevButton

            text: "prev"

            onClicked: {
                viewSlider.value -= 1;
            }
        }

        Button {
            id: playButton

            checkable: true
            checked: false
            text: checked ? "pause" : "play"

            onCheckedChanged: {
                if (checked) {
                    timer.running = true;
                }
                else {
                    timer.running = false;
                }
            }
        }

        Button {
            id: nextButton

            text: "next"

            onClicked: {
                viewSlider.value += 1;
            }
        }
    
        Slider {
            id: viewSlider

            Layout.fillWidth: true

            stepSize: 1
            snapMode: Slider.SnapAlways
            live: true

            from: 0
            to: m.sortedViewIds.length + 1

            onValueChanged: {
                let idx = Math.floor(value);
                if (_reconstruction && idx >= 0 && idx < m.sortedViewIds.length - 1) {
                    _reconstruction.selectedViewId = m.sortedViewIds[idx];
                }
            }
        }
    }
}
