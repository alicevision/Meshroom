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
    readonly property alias sync3DSelected: m.sync3DSelected
    property alias loading: fetchButton.checked

    function updateReconstructionView() {
        if (_reconstruction && m.frame >= 0 && m.frame < sortedViewIds.length) {
            if (m.syncSelected) {
                _reconstruction.selectedViewId = sortedViewIds[m.frame];
            } else {
                _reconstruction.pickedViewId = sortedViewIds[m.frame];
                if (m.sync3DSelected) {
                    _reconstruction.updateSelectedViewpoint(_reconstruction.pickedViewId);
                }
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
        property bool sync3DSelected: false
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
            syncSelected = syncViewersMenuItem.checked || !playing;
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
                if (m.frame > 0) {
                    m.frame -= 1;
                }
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
                if (m.frame < sortedViewIds.length - 1) {
                    m.frame += 1;
                }
            }
        }

        Item {
            Layout.preferredWidth: previousFrameButton.width + frameMetrics.width + nextFrameButton.width
            Layout.preferredHeight: frameInput.height

            MouseArea {
                id: mouseAreaFrameLabel

                anchors.fill: parent

                hoverEnabled: true

                onEntered: {
                    previousFrameButton.opacity = 1
                    nextFrameButton.opacity = 1
                }

                onExited: {
                    previousFrameButton.opacity = 0
                    nextFrameButton.opacity = 0
                } 

                MaterialToolButton {
                    id: previousFrameButton

                    anchors.verticalCenter: mouseAreaFrameLabel.verticalCenter

                    opacity: 0
                    
                    text: MaterialIcons.navigate_before
                    ToolTip.text: "Previous Frame"

                    onClicked: {
                        if (m.frame > 0) {
                            m.frame -= 1;
                        }
                    }
                }

                TextInput {
                    id: frameInput

                    anchors.horizontalCenter: mouseAreaFrameLabel.horizontalCenter

                    color: palette.text
                    horizontalAlignment: Text.AlignHCenter

                    text: m.frame
                    Layout.preferredWidth: frameMetrics.width

                    onEditingFinished: {
                        // We first assign the frame to the entered text even if it is an invalid frame number. We do it for extreme cases, for example without doing it, if we are at 0, and put a negative number, m.frame would be still 0 and nothing happens but we will still see the wrong number
                        m.frame = parseInt(text) 
                        m.frame = Math.min((sortedViewIds.length - 1), Math.max(0, parseInt(text)));
                        focus = false;
                    }
                }

                MaterialToolButton {
                    id: nextFrameButton

                    anchors.right: mouseAreaFrameLabel.right
                    anchors.verticalCenter: mouseAreaFrameLabel.verticalCenter

                    opacity: 0

                    text: MaterialIcons.navigate_next
                    ToolTip.text: "Next Frame"

                    onClicked: {
                        if (m.frame < sortedViewIds.length - 1) {
                            m.frame += 1;
                        }
                    }
                }
            }
        }

    
        Slider {
            id: frameSlider

            Layout.fillWidth: true

            stepSize: 1
            snapMode: Slider.SnapAlways
            live: true

            from: 0
            to: sortedViewIds.length - 1

            onValueChanged: {
                m.frame = value;
            }

            ToolTip {
                parent: frameSlider.handle
                visible: frameSlider.hovered
                text: m.frame
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
            TextInput {
                id: fpsTextInput

                color: palette.text

                Layout.preferredWidth: fpsMetrics.width

                text: !focus ? m.fps + " FPS" : m.fps

                onEditingFinished: {
                    m.fps = parseInt(text);
                    focus = false;
                }
            }
        }

        MaterialToolButton {
            id: fetchButton

            text: MaterialIcons.download_for_offline
            ToolTip.text: "Fetch"
            checkable: true
            checked: false
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

            text: MaterialIcons.sync
            font.pointSize: 11
            padding: 2
            onClicked: syncViewerMenu.open()
            checkable: true
            checked: syncViewerMenu.visible

            Menu {
                id: syncViewerMenu
                width: 270
                y: parent.height
                x: -width + parent.width

                MenuItem {
                    id: syncViewersMenuItem
                    text: "Sync Viewers with Sequence Player"
                    checkable: true
                    onCheckedChanged: {
                        // if playing, update the syncSelected property
                        if (m.playing) {
                            m.syncSelected = checked
                        }

                        if (checked)
                            sync3DMenuItem.checked = false
                    }

                    ToolTip.text: "The Image Gallery and 3D Viewer will be updated at the same time as the Sequence Player."
                    ToolTip.visible: hovered
                    ToolTip.delay: 100
                }

                MenuItem {
                    id: sync3DMenuItem
                    text: "Sync 3D VIewer with Sequence Player"
                    checkable: true
                    onCheckedChanged: {
                        m.sync3DSelected = checked

                        if (checked)
                            syncViewersMenuItem.checked = false
                    }

                    ToolTip.text: "The 3D Viewer will be updated at the same time as the Sequence Player."
                    ToolTip.visible: hovered
                    ToolTip.delay: 100
                }
            }
        }
    }

    TextMetrics {
        id: frameMetrics

        font: frameInput.font
        text: "10000"
    }

    TextMetrics {
        id: fpsMetrics

        font: fpsTextInput.font
        text: "100 FPS"
    }

    // Action to play/pause the sequence player
    Action {
        id: playPauseAction

        shortcut: "Space"

        onTriggered: {
            m.playing = !m.playing;
        }
    }
}
