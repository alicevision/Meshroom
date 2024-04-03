import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.11

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

    // Exposed properties
    property var sortedViewIds: []
    property var viewer: null

    function updateReconstructionView() {
        if (_reconstruction && m.frame >= 0 && m.frame < sortedViewIds.length) {
            if (m.syncSelected) {
                _reconstruction.selectedViewId = sortedViewIds[m.frame];
            } else {
                _reconstruction.pickedViewId = sortedViewIds[m.frame];
            }
        }
    }

    // Sequence player model:
    // - current frame
    // - data related to automatic sequence playing
    QtObject {
        id: m

        property int frame: 0
        property bool syncSelected: true
        property bool playing: false
        property bool repeat: false
        property real fps: 24

        onFrameChanged: {
            updateReconstructionView();
        }

        onSyncSelectedChanged: {
            updateReconstructionView();
        }

        onPlayingChanged: {
            syncSelected = syncButton.checked || !playing;
            if(playing && (frame + 1 >= sortedViewIds.length))
            {
                frame = 0;
            }
            viewer.playback(playing);
        }
    }

    // Update the frame property
    // when the selected view ID is changed externally
    Connections {
        target: _reconstruction
        function onSelectedViewIdChanged() {
            for (let idx = 0; idx < sortedViewIds.length; idx++) {
                if (_reconstruction.selectedViewId === sortedViewIds[idx] && (m.frame != idx)) {
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
            if (viewer.imageStatus !== Image.Ready) {
                // Wait for current image to be displayed before switching to next image
                return;
            }
            let nextIndex = m.frame + 1;
            if (nextIndex == sortedViewIds.length) {
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
                function onPlayingChanged() {
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
            Layout.preferredWidth: frameMetrics.width
        }
    
        Slider {
            id: frameSlider

            Layout.fillWidth: true

            stepSize: 1
            snapMode: Slider.SnapAlways
            live: true
            enabled: !m.playing

            from: 0
            to: sortedViewIds.length - 1

            onValueChanged: {
                m.frame = value;
            }

            onPressedChanged: {
                m.syncSelected = !pressed;
            }

            Connections {
                target: m
                function onFrameChanged() {
                    frameSlider.value = m.frame;
                }
            }

            background: Rectangle {
                x: frameSlider.leftPadding
                y: frameSlider.topPadding + frameSlider.height / 2 - height / 2
                width: frameSlider.availableWidth
                height: 4
                radius: 2
                color: Colors.grey

                Repeater {
                    id: cacheView

                    model: viewer ? viewer.cachedFrames : []
                    property real frameLength: sortedViewIds.length > 0 ? frameSlider.width / sortedViewIds.length : 0

                    Rectangle {
                        x: modelData.x * cacheView.frameLength
                        y: 0
                        width: cacheView.frameLength * (modelData.y - modelData.x + 1)
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
                value: m.fps

                onValueChanged: {
                    m.fps = value;
                }
            }
        }

        MaterialToolButton {
            id: repeatButton

            checkable: true
            checked: false
            text: MaterialIcons.repeat
            ToolTip.text: "Repeat"

            onCheckedChanged: {
                m.repeat = checked;
            }
        }

        MaterialToolButton {
            id: syncButton

            checkable: true
            checked: false
            text: MaterialIcons.sync
            ToolTip.text: "Sync Viewers and Sequence Player"

            onCheckedChanged: {
                // if playing, update the syncSelected property
                if (m.playing) {
                    m.syncSelected = checked;
                }
            }
        }
    }

    TextMetrics {
        id: frameMetrics

        font: frameLabel.font
        text: "10000"
    }

    TextMetrics {
        id: fpsMetrics

        font: fpsSpinBox.font
        text: "100"
    }
}
