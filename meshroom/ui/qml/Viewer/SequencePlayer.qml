import QtQuick 2.11
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import Controls 1.0
import MaterialIcons 2.2

FloatingPane {
    id: root

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
        interval: 1000 / fpsSpinBox.value

        onTriggered: {
            let nextIndex = viewSlider.value + 1;
            if (nextIndex == m.sortedViewIds.length) {
                if (repeatButton.checked) {
                    viewSlider.value = 0;
                    return;
                }
                else {
                    playButton.checked = false;
                    return;
                }
            }
            viewSlider.value = nextIndex;
        }
    }

    TextMetrics {
        id: fpsMetrics

        font: fpsSpinBox.font
        text: "100"
    }
    
    RowLayout {

        anchors.fill: parent

        MaterialToolButton {
            id: prevButton

            text: MaterialIcons.skip_previous
            ToolTip.text: "Previous Frame"

            onClicked: {
                viewSlider.value -= 1;
            }
        }

        MaterialToolButton {
            id: playButton

            checkable: true
            checked: false
            text: checked ? MaterialIcons.pause : MaterialIcons.play_arrow
            ToolTip.text: checked ? "Pause Player" : "Play Sequence"

            onCheckedChanged: {
                if (checked) {
                    timer.running = true;
                }
                else {
                    timer.running = false;
                }
            }
        }

        MaterialToolButton {
            id: nextButton

            text: MaterialIcons.skip_next
            ToolTip.text: "Next Frame"

            onClicked: {
                viewSlider.value += 1;
            }
        }

        Label {
            id: frameLabel

            text: viewSlider.value
        }
    
        Slider {
            id: viewSlider

            Layout.fillWidth: true

            stepSize: 1
            snapMode: Slider.SnapAlways
            live: true

            from: 0
            to: m.sortedViewIds.length - 1

            onValueChanged: {
                let idx = Math.floor(value);
                if (_reconstruction && idx >= 0 && idx < m.sortedViewIds.length - 1) {
                    _reconstruction.selectedViewId = m.sortedViewIds[idx];
                }
            }
        }

        RowLayout {
            Label {
                text: "FPS:"
                ToolTip.text: "Frame Per Second"
            }

            SpinBox {
                id: fpsSpinBox

                Layout.preferredWidth: fpsMetrics.width + up.implicitIndicatorWidth

                from: 1
                to: 60
                stepSize: 1
            }
        }

        MaterialToolButton {
            id: repeatButton

            checkable: true
            checked: false
            text: MaterialIcons.replay
            ToolTip.text: "Repeat"
        }
    }
}
