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
        property int frame: 0
        property bool playing: false
        property bool repeat: false
        property real fps: 1

        onFrameChanged: {
            if (_reconstruction && frame >= 0 && frame < sortedViewIds.length) {
                _reconstruction.selectedViewId = sortedViewIds[frame];
            }
        }
    }

    Connections {
        target: _reconstruction
        onSelectedViewIdChanged: {
            for (let idx = 0; idx < m.sortedViewIds.length; idx++) {
                if (_reconstruction.selectedViewId == m.sortedViewIds[idx] && (m.frame != idx)) {
                    m.frame = idx;
                }
            }
        }
    }

    Timer {
        id: timer

        repeat: true
        running: m.playing
        interval: 1000 / m.fps

        onTriggered: {
            let nextIndex = m.frame + 1;
            if (nextIndex == m.sortedViewIds.length) {
                if (m.repeat) {
                    m.frame = 0;
                    return;
                }
                else {
                    m.playing = false;
                    return;
                }
            }
            m.frame = nextIndex;
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
                m.frame -= 1;
            }
        }

        MaterialToolButton {
            id: playButton

            checkable: true
            checked: false
            text: checked ? MaterialIcons.pause : MaterialIcons.play_arrow
            ToolTip.text: checked ? "Pause Player" : "Play Sequence"

            onCheckedChanged: {
                m.playing = checked;
            }

            Connections {
                target: m
                onPlayingChanged: {
                    playButton.checked = m.playing;
                }
            }
        }

        MaterialToolButton {
            id: nextButton

            text: MaterialIcons.skip_next
            ToolTip.text: "Next Frame"

            onClicked: {
                m.frame += 1;
            }
        }

        Label {
            id: frameLabel

            text: m.frame
        }
    
        Slider {
            id: frameSlider

            Layout.fillWidth: true

            stepSize: 1
            snapMode: Slider.SnapAlways
            live: true

            from: 0
            to: m.sortedViewIds.length - 1

            onValueChanged: {
                m.frame = value;
            }

            Connections {
                target: m
                onFrameChanged: {
                    frameSlider.value = m.frame;
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

                onValueChanged: {
                    m.fps = value;
                }
            }
        }

        MaterialToolButton {
            id: repeatButton

            checkable: true
            checked: false
            text: MaterialIcons.replay
            ToolTip.text: "Repeat"

            onCheckedChanged: {
                m.repeat = checked;
            }
        }
    }
}
