import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.11

import Controls 1.0
import MaterialIcons 2.2
import Utils 1.0
import Qt.labs.settings 1.0

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
    property bool isOutputSequence: false
    readonly property alias sync3DSelected: m.sync3DSelected
    readonly property alias syncFeaturesSelected: m.syncFeaturesSelected
    property bool loading: fetchButton.checked || m.playing
    property alias settings_SequencePlayer: settings_SequencePlayer
    property alias frameId: m.frame
    property var frameRange: {"min" : 0, "max" : sortedViewIds.length - 1}

    Settings {
        id: settings_SequencePlayer
        property int maxCacheMemory: viewer ? viewer.ramInfo.x/4 : 0
    }

    function updateReconstructionView() {
        if (isOutputSequence)
            return
        if (_reconstruction && m.frame >= 0 && m.frame < sortedViewIds.length) {
            if (!m.playing && !frameSlider.pressed) {
                _reconstruction.selectedViewId = sortedViewIds[m.frame];
            } else {
                _reconstruction.pickedViewId = sortedViewIds[m.frame];
                if (m.sync3DSelected) {
                    _reconstruction.updateSelectedViewpoint(_reconstruction.pickedViewId);
                }
            }
        }
    }

    onIsOutputSequenceChanged: {
        if (!isOutputSequence) {
            frameId = frameRange.min
        }
    }

    onSortedViewIdsChanged: {
        frameSlider.from = frameRange.min
        frameSlider.to = frameRange.max
    }

    // Sequence player model:
    // - current frame
    // - data related to automatic sequence playing
    QtObject {
        id: m

        property int frame: frameRange.min
        property bool syncFeaturesSelected: true
        property bool sync3DSelected: true
        property bool playing: false
        property bool repeat: false
        property real fps: 24

        onFrameChanged: {
            updateReconstructionView();
        }

        onPlayingChanged: {
            if (!playing) {
                updateReconstructionView();
            } else if (playing && (frame + 1 >= frameRange + 1)) {
                frame = frameRange.min;
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
        running: m.playing && root.visible
        interval: 1000 / m.fps

        onTriggered: {
            if (viewer.imageStatus !== Image.Ready) {
                // Wait for current image to be displayed before switching to next image
                return;
            }
            let nextIndex = m.frame + 1;
            if (nextIndex == frameRange.max + 1) {
                if (m.repeat) {
                    m.frame = frameRange.min;
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

                    width: 10

                    anchors.verticalCenter: mouseAreaFrameLabel.verticalCenter

                    opacity: 0
                    
                    text: MaterialIcons.navigate_before
                    ToolTip.text: "Previous Frame"

                    onClicked: {
                        if (m.frame > frameRange.min) {
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
                        m.frame = Math.min(frameRange.max, Math.max(frameRange.min, parseInt(text)));
                        focus = false;
                    }
                }

                MaterialToolButton {
                    id: nextFrameButton

                    width: 10

                    anchors.right: mouseAreaFrameLabel.right
                    anchors.verticalCenter: mouseAreaFrameLabel.verticalCenter

                    opacity: 0

                    text: MaterialIcons.navigate_next
                    ToolTip.text: "Next Frame"

                    onClicked: {
                        if (m.frame < frameRange.max) {
                            m.frame += 1;
                        }
                    }
                }
            }
        }

        MaterialToolButton {
            id: playButton

            checkable: true
            checked: false
            text: checked ? MaterialIcons.pause_circle : MaterialIcons.play_circle
            font.pointSize: 20
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

    
        Slider {
            id: frameSlider

            Layout.fillWidth: true

            stepSize: 1
            snapMode: Slider.SnapAlways
            live: true

            from: frameRange.min
            to: frameRange.max

            onValueChanged: {
                m.frame = value;
            }

            onPressedChanged: {
                if (!pressed) {
                    updateReconstructionView();
                }
            }

            ToolTip {
                parent: frameSlider.handle
                visible: frameSlider.hovered
                text: m.frame
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
                    property real frameLength: sortedViewIds.length > 0 ? frameSlider.width / (frameRange.max-frameRange.min+1) : 0

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

            text: MaterialIcons.subscriptions
            ToolTip.text: "Fetch"
            checkable: true
            checked: loading
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
            id: infoButton

            text: MaterialIcons.settings
            font.pointSize: 11
            padding: 2
            onClicked: infoMenu.open()
            checkable: true
            checked: infoMenu.visible

            Popup {
                id: infoMenu
                y: parent.height
                x: -width + parent.width

                contentItem: GridLayout {
                        layoutDirection: Qt.LeftToRight
                        columns: 2

                        Column {
                            id: syncColumn
                            Layout.alignment: Qt.AlignTop

                            Text {
                                text: "<b>Synchronisation:</b>"
                                color: palette.text
                            }


                            CheckBox {
                                id: syncFeaturePointsCheckBox
                                text: "Sync Feature Points"
                                checkable: true
                                checked: m.syncFeaturesSelected
                                onCheckedChanged: {
                                    m.syncFeaturesSelected = checked
                                }

                                ToolTip.text: "The Feature points will be updated at the same time as the Sequence Player."
                                ToolTip.visible: hovered
                                ToolTip.delay: 100
                            }

                            CheckBox {
                                id: sync3DCheckBox
                                text: "Sync 3D Viewer"
                                checkable: true
                                checked: m.sync3DSelected
                                onCheckedChanged: {
                                    m.sync3DSelected = checked
                                }

                                ToolTip.text: "The 3D Viewer will be updated at the same time as the Sequence Player."
                                ToolTip.visible: hovered
                                ToolTip.delay: 100
                            }
                        }

                        Column {
                            id: cacheColumn
                            Layout.alignment: Qt.AlignTop

                            Text {
                                text: "<b>Cache:</b>"
                                color: palette.text
                            }

                            // max cache memory limit
                            Row {
                                height: sync3DCheckBox.height
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: "Max Cache Memory: "
                                    color: palette.text
                                }
                                
                                TextField {
                                    id: maxCacheMemoryInput

                                    anchors.verticalCenter: parent.verticalCenter
                                    color: palette.text

                                    text: !focus ? settings_SequencePlayer.maxCacheMemory + " GB" : settings_SequencePlayer.maxCacheMemory

                                    onEditingFinished: {
                                        settings_SequencePlayer.maxCacheMemory = parseInt(text);
                                        focus = false;
                                    }
                                }
                            }

                            Text {
                                height: sync3DCheckBox.height
                                verticalAlignment: Text.AlignVCenter
                                text: "Available Memory: " + viewer.ramInfo.x + " GB"
                                color: palette.text
                            }

                            Text {
                                height: sync3DCheckBox.height
                                verticalAlignment: Text.AlignVCenter
                                text:{
                                    // number of cached frames is the difference between the first and last frame of all intervals in the cache
                                    let cachedFrames = viewer.cachedFrames;
                                    let cachedFramesCount = 0;
                                    for (let i = 0; i < cachedFrames.length; i++) {
                                        cachedFramesCount += cachedFrames[i].y - cachedFrames[i].x + 1;
                                    }
                                    return "Cached Frames: " + (viewer ? cachedFramesCount : "0") + " / " + sortedViewIds.length
                                }
                                color: palette.text
                            }

                            // do beautiful progress bar
                            ProgressBar {
                                id: cacheProgressBar

                                width: parent.width

                                from: 0
                                to: viewer ? viewer.ramInfo.x : 0

                                value: viewer ? settings_SequencePlayer.maxCacheMemory : 0

                                ToolTip.text: "Max cache memory set: " + settings_SequencePlayer.maxCacheMemory + " GB" + "\n" + "on available memory: "+ viewer.ramInfo.x + " GB"
                                ToolTip.visible: hovered
                                ToolTip.delay: 100
                            }

                            ProgressBar {
                                id: occupiedCacheProgressBar

                                width: parent.width

                                from: 0
                                to: settings_SequencePlayer.maxCacheMemory
                                value: viewer.ramInfo.y

                                ToolTip.text: "Occupied cache: "+ viewer.ramInfo.y + " GB" + "\n" +"On max cache memory set: " + settings_SequencePlayer.maxCacheMemory + " GB"
                                ToolTip.visible: hovered
                                ToolTip.delay: 100
                            }
                            
                        }
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
