import QtQuick 2.11
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0

/**
 * The Sequence Player is a UI for manipulating
 * the currently selected (and displayed) viewpoint
 * in an ordered set of viewpoints (i.e. a sequence).
 *
 * The viewpoint manipulation process can be manual
 * (for example by dragging a slider to change the current frame)
 * or automatic
 * (by playing the sequence, i.e. incrementing the current frame at a given time rate).
 */
FloatingPane {
    id: root

    // Utility function to sort a set of viewpoints
    // using their corresponding image filenames
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

    // Sequence player model:
    // - ordered set of viewpoints
    // - current frame
    // - data related to automatic sequence playing
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

    // Exposed properties
    property var viewer: null

    // Update the frame property
    // when the selected view ID is changed externally
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

    // In play mode
    // we use a timer to increment the frame property
    // at a given time rate (defined by the fps property)
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
    
    // Widgets:
    // - "Previous Frame" button
    // - "Play - Pause" button
    // - "Next Frame" button
    // - frame label
    // - frame slider
    // - FPS spin box
    // - "Repeat" button
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

            property real frameLength: m.sortedViewIds.length > 0 ? width / m.sortedViewIds.length : 0

            background: Rectangle {
                x: frameSlider.leftPadding
                y: frameSlider.topPadding + frameSlider.height / 2 - height / 2
                width: frameSlider.availableWidth
                height: 4
                radius: 2
                color: Colors.grey

                Repeater {
                    model: viewer ? viewer.cachedFrames : []

                    Rectangle {
                        x: modelData * frameSlider.frameLength
                        y: 0
                        width: frameSlider.frameLength
                        height: 4
                        radius: 2
                        color: Colors.blue
                    }
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

    TextMetrics {
        id: fpsMetrics

        font: fpsSpinBox.font
        text: "100"
    }
}
